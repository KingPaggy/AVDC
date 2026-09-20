// test_bridge.mm — AVDCBridge 冒烟测试（命令行）
// 用 mock 临时项目根（含 cli/cli.py 假 CLI）验证：
//   1. scan JSON 解析
//   2. config list 解析
//   3. process 事件流（log/progress/success/failure/done 顺序）
//   4. terminate 取消
// 运行：cd mac-gui/build && ./src/bridge/bridge_test

#import <Foundation/Foundation.h>

#import "bridge/AVDCBridge.h"

static int g_pass = 0;
static int g_fail = 0;

#define CHECK(cond, msg)                                               \
  do {                                                                 \
    if (cond) {                                                        \
      g_pass++;                                                        \
      printf("  [PASS] %s\n", msg);                                    \
    } else {                                                           \
      g_fail++;                                                        \
      printf("  [FAIL] %s\n", msg);                                    \
    }                                                                  \
  } while (0)

// 构造 mock 项目根：临时目录 + cli/cli.py + pyproject.toml
static NSString* MakeMockRoot(void) {
  NSString* tmp =
      [NSTemporaryDirectory() stringByAppendingPathComponent:
          [NSString stringWithFormat:@"avdc_bridge_%d", getpid()]];
  NSString* cliDir = [tmp stringByAppendingPathComponent:@"cli"];
  [NSFileManager.defaultManager createDirectoryAtPath:cliDir
                          withIntermediateDirectories:YES
                                           attributes:nil
                                                error:nil];

  // mock_cli.py 复制为 cli/cli.py
  NSString* src = @SRC_DIR "/test/mock_cli.py";
  NSString* dst = [cliDir stringByAppendingPathComponent:@"cli.py"];
  [NSFileManager.defaultManager copyItemAtPath:src toPath:dst error:nil];

  // uv 项目标记（uv run 需要）
  NSString* pyproject =
      @"[project]\nname = \"mock\"\nversion = \"0.0.0\"\n"
      @"requires-python = \">=3.9\"\n";
  [pyproject writeToFile:[tmp stringByAppendingPathComponent:@"pyproject.toml"]
              atomically:YES encoding:NSUTF8StringEncoding error:nil];
  return tmp;
}

// 异步完成标记
@interface Waiter : NSObject
@property (nonatomic) BOOL done;
- (void)waitWithTimeout:(NSTimeInterval)secs;
@end

@implementation Waiter
- (void)waitWithTimeout:(NSTimeInterval)secs {
  NSDate* deadline = [NSDate dateWithTimeIntervalSinceNow:secs];
  while (!self.done &&
         [deadline timeIntervalSinceNow] > 0) {
    [[NSRunLoop currentRunLoop] runMode:NSDefaultRunLoopMode
                             beforeDate:[NSDate dateWithTimeIntervalSinceNow:0.05]];
  }
}
@end

static void TestScan(AVDCBridge* bridge, Waiter* w) {
  printf("[1] scan JSON 解析\n");
  w.done = NO;
  [bridge scanPath:@"/tmp/mock"
      escapeFolder:nil
      completion:^(NSArray<NSDictionary*>* files, NSError* error) {
    CHECK(error == nil, "scan 无错误");
    CHECK(files.count == 1, "scan 解析到 1 个文件");
    if (files.count == 1) {
      CHECK([files[0][@"number"] isEqualToString:@"ABC-123"],
            "番号字段正确");
    }
    w.done = YES;
  }];
  [w waitWithTimeout:30];
}

static void TestConfig(AVDCBridge* bridge, Waiter* w) {
  printf("[2] config list 解析\n");
  w.done = NO;
  [bridge configList:^(NSArray<NSString*>* lines, NSError* error) {
    CHECK(error == nil, "config list 无错误");
    CHECK(lines.count == 1, "config list 解析到 1 行");
    if (lines.count == 1) {
      CHECK([lines[0] hasPrefix:@"common.website"],
            "配置行格式正确");
    }
    w.done = YES;
  }];
  [w waitWithTimeout:30];
}

static void TestProcessEvents(AVDCBridge* bridge, Waiter* w) {
  printf("[3] process 事件流（log/progress/success/failure/done）\n");
  w.done = NO;
  NSMutableArray* order = [NSMutableArray array];
  __block NSInteger exitStatus = -99;
  [bridge processPath:@"/tmp/mock" mode:1
      onEvent:^(AVDCEventType type, NSDictionary* event) {
    switch (type) {
      case AVDCEventLog:     [order addObject:@"log"]; break;
      case AVDCEventProgress:
        [order addObject:@"progress"];
        CHECK([event[@"current"] integerValue] >= 1, "progress current 有效");
        break;
      case AVDCEventSuccess: [order addObject:@"success"]; break;
      case AVDCEventFailure:
        [order addObject:@"failure"];
        CHECK([event[@"reason"] length] > 0, "failure reason 存在");
        break;
      case AVDCEventDone:
        [order addObject:@"done"];
        CHECK([event[@"total"] integerValue] == 2, "done total=2");
        CHECK([event[@"success"] integerValue] == 1, "done success=1");
        break;
      default: break;
    }
  } onExit:^(int status) {
    exitStatus = status;
    w.done = YES;
  }];
  [w waitWithTimeout:30];
  CHECK(exitStatus == 0, "process 退出码 0");
  NSArray* expected = @[ @"log", @"progress", @"success",
                         @"progress", @"failure", @"done" ];
  CHECK([order isEqualToArray:expected],
        "事件顺序正确（log→progress→success→progress→failure→done）");
}

static void TestTerminate(AVDCBridge* bridge, Waiter* w) {
  printf("[4] terminate 取消（--sleep 5）\n");
  w.done = NO;
  __block BOOL exitCalled = NO;
  __block int exitStatus = -99;
  // 直接走底层：--sleep 5 模拟长任务
  [bridge runCommand:@[ @"--path", @"/tmp/mock",
                        @"--main-mode", @"scrape",
                        @"--json-output", @"--sleep", @"5" ]
              onLine:nil
               onExit:^(int status) {
    exitCalled = YES;
    exitStatus = status;
    w.done = YES;
  }];
  // 1 秒后取消
  dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)),
                 dispatch_get_main_queue(), ^{
    [bridge terminate];
  });
  [w waitWithTimeout:8];
  CHECK(exitCalled, "取消后 onExit 被回调");
  CHECK(exitStatus != 0, "退出码非 0（被中断）");
}

int main(int argc, const char* argv[]) {
  (void)argc; (void)argv;
  @autoreleasepool {
    printf("=== AVDCBridge 冒烟测试 ===\n");
    NSString* root = MakeMockRoot();
    NSLog(@"mock 项目根: %@", root);
    AVDCBridge* bridge = [[AVDCBridge alloc] initWithProjectRoot:root];
    Waiter* w = [[Waiter alloc] init];

    TestScan(bridge, w);
    TestConfig(bridge, w);
    TestProcessEvents(bridge, w);
    TestTerminate(bridge, w);

    printf("\n结果: %d 通过, %d 失败\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
  }
}
