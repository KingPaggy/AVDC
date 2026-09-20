// AVDCBridge.mm — Python Bridge 实现（ObjC++）
// NSTask + NSPipe 异步子进程管理：stdout JSONL 逐行解析，
// stderr 逐行归集；事件与退出回调统一派发到主线程
// （GUI 状态更新需主线程，Bridge 自身线程无关可独立测试）。

#import "AVDCBridge.h"

@implementation AVDCBridge {
  NSTask* _task;
  NSMutableData* _outBuffer;
  NSMutableData* _errBuffer;
  NSString* _projectRoot;
}

//---------------------------------------------------------------------------
// 初始化
//---------------------------------------------------------------------------

- (instancetype)init {
  return [self initWithProjectRoot:[AVDCBridge findProjectRoot]];
}

- (instancetype)initWithProjectRoot:(NSString*)projectRoot {
  self = [super init];
  if (self) {
    _projectRoot = [projectRoot copy];
  }
  return self;
}

//---------------------------------------------------------------------------
// 项目根定位
//---------------------------------------------------------------------------

+ (NSString*)findProjectRoot {
  NSString* dir = NSFileManager.defaultManager.currentDirectoryPath;
  for (int i = 0; i < 10; i++) {
    NSString* cli =
        [dir stringByAppendingPathComponent:@"cli/cli.py"];
    if ([NSFileManager.defaultManager fileExistsAtPath:cli]) {
      return dir;
    }
    dir = [dir stringByDeletingLastPathComponent];
  }
  return nil;
}

- (BOOL)isRunning {
  return _task != nil;
}

//---------------------------------------------------------------------------
// 底层命令执行
//---------------------------------------------------------------------------

- (void)runCommand:(NSArray<NSString*>*)arguments
            onLine:(AVDCLineHandler)onLine
             onExit:(AVDCExitHandler)onExit {
  if (_task) {
    if (onExit) onExit(-1);
    return;
  }

  NSString* root = _projectRoot.length > 0 ? _projectRoot
                                           : [AVDCBridge findProjectRoot];
  if (!root) {
    if (onLine) onLine(nil, @"[bridge] 未找到项目根目录（cli/cli.py）");
    if (onExit) onExit(-1);
    return;
  }
  NSString* cliPath = [root stringByAppendingPathComponent:@"cli/cli.py"];
  NSMutableArray* args =
      [NSMutableArray arrayWithObjects:@"uv", @"run", @"python",
                                        cliPath, nil];
  [args addObjectsFromArray:arguments];

  NSTask* task = [[NSTask alloc] init];
  task.executableURL = [NSURL fileURLWithPath:@"/usr/bin/env"];
  task.arguments = args;
  task.currentDirectoryURL = [NSURL fileURLWithPath:root];

  NSPipe* outPipe = [NSPipe pipe];
  NSPipe* errPipe = [NSPipe pipe];
  task.standardOutput = outPipe;
  task.standardError = errPipe;

  _outBuffer = [NSMutableData data];
  _errBuffer = [NSMutableData data];
  __weak typeof(self) weakSelf = self;

  // stdout / stderr 异步读取（readabilityHandler 在后台线程回调）
  outPipe.fileHandleForReading.readabilityHandler =
      ^(NSFileHandle* fh) {
    __strong typeof(self) strongSelf = weakSelf;
    if (!strongSelf) return;
    [strongSelf readFrom:fh buffer:strongSelf->_outBuffer
                 onLine:onLine];
  };
  errPipe.fileHandleForReading.readabilityHandler =
      ^(NSFileHandle* fh) {
    __strong typeof(self) strongSelf = weakSelf;
    if (!strongSelf) return;
    [strongSelf readFrom:fh buffer:strongSelf->_errBuffer
                 onLine:onLine];
  };

  __block BOOL exitCalled = NO;
  task.terminationHandler = ^(NSTask* t) {
    // 清空 EOF 后残留缓冲
    dispatch_async(dispatch_get_main_queue(), ^{
      __strong typeof(self) strongSelf = weakSelf;
      if (!strongSelf) return;
      if (strongSelf->_outBuffer.length > 0) {
        NSString* line = [[NSString alloc]
            initWithData:strongSelf->_outBuffer
                encoding:NSUTF8StringEncoding];
        [strongSelf->_outBuffer setLength:0];
        if (line.length > 0) [strongSelf emitLine:line onLine:onLine];
      }
      if (strongSelf->_errBuffer.length > 0) {
        NSString* line = [[NSString alloc]
            initWithData:strongSelf->_errBuffer
                encoding:NSUTF8StringEncoding];
        [strongSelf->_errBuffer setLength:0];
        if (line.length > 0) [strongSelf emitLine:line onLine:onLine];
      }
      strongSelf->_task = nil;
      if (!exitCalled) {
        exitCalled = YES;
        if (onExit) onExit(t.terminationStatus);
      }
    });
  };

  NSError* err = nil;
  if (![task launchAndReturnError:&err]) {
    NSLog(@"[bridge] launch 失败: %@", err);
    _outBuffer = nil;
    _errBuffer = nil;
    if (onLine) onLine(nil, [NSString stringWithFormat:
        @"[bridge] 启动失败: %@", err.localizedDescription]);
    if (onExit) onExit(-1);
    return;
  }
  _task = task;
}

// 取消：SIGTERM（CLI 捕获 KeyboardInterrupt 优雅退出）
- (void)terminate {
  [_task terminate];
}

//---------------------------------------------------------------------------
// 逐行读取（后台线程调用；行事件派发主线程）
//---------------------------------------------------------------------------

- (void)readFrom:(NSFileHandle*)fh buffer:(NSMutableData*)buffer
          onLine:(AVDCLineHandler)onLine {
  NSData* chunk = [fh availableData];
  if (chunk.length == 0) {
    // EOF：flush 剩余缓冲（无换行结尾的最后一行），
    // 避免与 terminationHandler 竞态导致行丢失
    fh.readabilityHandler = nil;
    if (buffer.length > 0) {
      NSString* line = [[NSString alloc] initWithData:buffer
                                             encoding:NSUTF8StringEncoding];
      [buffer setLength:0];
      if (line.length > 0) {
        dispatch_async(dispatch_get_main_queue(), ^{
          [self emitLine:line onLine:onLine];
        });
      }
    }
    return;
  }
  [buffer appendData:chunk];
  NSData* nl = [NSData dataWithBytes:"\n" length:1];
  while (true) {
    NSRange r = [buffer rangeOfData:nl options:0
                              range:NSMakeRange(0, buffer.length)];
    if (r.location == NSNotFound) break;
    NSData* lineData = [buffer subdataWithRange:NSMakeRange(0, r.location)];
    [buffer replaceBytesInRange:NSMakeRange(0, r.location + 1)
                      withBytes:NULL length:0];
    if (lineData.length == 0) continue;
    NSString* line = [[NSString alloc] initWithData:lineData
                                           encoding:NSUTF8StringEncoding];
    if (line.length == 0) continue;
    dispatch_async(dispatch_get_main_queue(), ^{
      [self emitLine:line onLine:onLine];
    });
  }
}

// JSONL 解析分发：可解析为字典 → json 回调；否则 raw 回调
- (void)emitLine:(NSString*)line onLine:(AVDCLineHandler)onLine {
  if (!onLine) return;
  NSData* data = [line dataUsingEncoding:NSUTF8StringEncoding];
  id obj = [NSJSONSerialization JSONObjectWithData:data
                                           options:0
                                             error:nil];
  if ([obj isKindOfClass:[NSDictionary class]]) {
    onLine((NSDictionary*)obj, nil);
  } else {
    onLine(nil, line);
  }
}

//---------------------------------------------------------------------------
// 命令封装
//---------------------------------------------------------------------------

- (void)scanPath:(NSString*)path
    escapeFolder:(nullable NSString*)escapeFolder
       completion:(void (^)(NSArray<NSDictionary*>* _Nullable files,
                            NSError* _Nullable error))completion {
  NSMutableArray* args = [NSMutableArray
      arrayWithObjects:@"scan", @"--path", path, nil];
  if (escapeFolder.length > 0) {
    [args addObjectsFromArray:@[ @"--escape-folder", escapeFolder ]];
  }
  NSMutableArray* files = [NSMutableArray array];
  __block BOOL gotResult = NO;
  [self runCommand:args onLine:^(NSDictionary* json, NSString* raw) {
    (void)raw;
    if (json[@"files"]) {
      gotResult = YES;
      [files addObjectsFromArray:json[@"files"]];
    }
  } onExit:^(int status) {
    if (status == 0 && gotResult) {
      if (completion) completion(files, nil);
    } else {
      if (completion) completion(nil, [NSError errorWithDomain:@"AVDCBridge"
          code:status userInfo:@{NSLocalizedDescriptionKey:
              [NSString stringWithFormat:@"scan 失败（退出码 %d）", status]}]);
    }
  }];
}

- (void)processPath:(NSString*)path
               mode:(NSInteger)mode
            onEvent:(AVDCEventHandler)onEvent
             onExit:(AVDCExitHandler)onExit {
  NSString* mainMode = (mode == 2) ? @"organize" : @"scrape";
  NSArray* args = @[ @"--path", path,
                     @"--main-mode", mainMode,
                     @"--json-output" ];
  [self runCommand:args onLine:^(NSDictionary* json, NSString* raw) {
    if (!onEvent) return;
    if (json) {
      NSString* type = json[@"type"];
      AVDCEventType et = AVDCEventUnknown;
      if ([type isEqualToString:@"log"]) et = AVDCEventLog;
      else if ([type isEqualToString:@"progress"]) et = AVDCEventProgress;
      else if ([type isEqualToString:@"success"]) et = AVDCEventSuccess;
      else if ([type isEqualToString:@"failure"]) et = AVDCEventFailure;
      else if ([type isEqualToString:@"done"]) et = AVDCEventDone;
      onEvent(et, json);
    } else {
      onEvent(AVDCEventStdErr, nil);
    }
  } onExit:onExit];
}

- (void)configList:(void (^)(NSArray<NSString*>* _Nullable lines,
                             NSError* _Nullable error))completion {
  NSMutableArray* lines = [NSMutableArray array];
  [self runCommand:@[ @"config", @"list" ]
           onLine:^(NSDictionary* json, NSString* raw) {
    (void)json;
    if (raw.length > 0) [lines addObject:raw];
  } onExit:^(int status) {
    if (status == 0) {
      if (completion) completion(lines, nil);
    } else {
      if (completion) completion(nil, [NSError errorWithDomain:@"AVDCBridge"
          code:status userInfo:@{NSLocalizedDescriptionKey:
              [NSString stringWithFormat:@"config list 失败（退出码 %d）",
                                         status]}]);
    }
  }];
}

- (void)configGet:(NSString*)field
       completion:(void (^)(NSString* _Nullable value,
                            NSError* _Nullable error))completion {
  NSMutableArray* lines = [NSMutableArray array];
  [self runCommand:@[ @"config", @"get", field ]
           onLine:^(NSDictionary* json, NSString* raw) {
    (void)json;
    if (raw.length > 0) [lines addObject:raw];
  } onExit:^(int status) {
    if (status == 0 && lines.count > 0) {
      if (completion) completion(lines.firstObject, nil);
    } else {
      if (completion) completion(nil, [NSError errorWithDomain:@"AVDCBridge"
          code:status userInfo:@{NSLocalizedDescriptionKey:
              [NSString stringWithFormat:@"config get %@ 失败（退出码 %d）",
                                         field, status]}]);
    }
  }];
}

- (void)configSet:(NSString*)field
            value:(NSString*)value
       completion:(void (^)(NSError* _Nullable error))completion {
  [self runCommand:@[ @"config", @"set", field, value ]
           onLine:nil
            onExit:^(int status) {
    if (completion) {
      if (status == 0) {
        completion(nil);
      } else {
        completion([NSError errorWithDomain:@"AVDCBridge"
            code:status userInfo:@{NSLocalizedDescriptionKey:
                [NSString stringWithFormat:@"config set %@ 失败（退出码 %d）",
                                           field, status]}]);
      }
    }
  }];
}

@end
