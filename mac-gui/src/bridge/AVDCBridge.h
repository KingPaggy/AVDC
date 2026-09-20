// AVDCBridge.h — Python Bridge（ObjC++）
// 通过 NSTask 子进程调用 `uv run python cli.py <cmd>`，
// stdout JSONL 逐行解析，事件分发到主线程。
// 契约对齐 cli/cli.py --json-output（docs/03-macos-gui-migration.md §4.3）
// 本类不依赖任何 UI 框架，可独立测试。

#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

// JSONL 事件类型（对齐 cli.py 事件契约）
typedef NS_ENUM(NSInteger, AVDCEventType) {
  AVDCEventLog,       // {"type":"log","msg":...}
  AVDCEventProgress,  // {"type":"progress","current":N,"total":N,"file":...}
  AVDCEventSuccess,   // {"type":"success","file":...,"suffix":...}
  AVDCEventFailure,   // {"type":"failure","file":...,"reason":...,"error":...}
  AVDCEventDone,      // {"type":"done","total":...,"success":...,"failed":...}
  AVDCEventUnknown,   // 其他带 type 字段的行
  AVDCEventStdErr,    // stderr 行（非 JSON，event=nil）
};

// 事件回调（主线程）：event 为解析后的 JSON 字典；StdErr 时 event=nil
typedef void (^AVDCEventHandler)(AVDCEventType type,
                                 NSDictionary* _Nullable event);

// 退出回调（主线程）：status 为进程退出码
typedef void (^AVDCExitHandler)(int status);

// 底层逐行回调（主线程）：json 非 nil 表示 JSONL 行；否则 raw 为原始行
typedef void (^AVDCLineHandler)(NSDictionary* _Nullable json,
                                NSString* _Nullable raw);

@interface AVDCBridge : NSObject

// 项目根定位：从当前工作目录向上查找含 cli/cli.py 的目录
// （仿 tui-go/pkg/python/client.go FindProjectRoot）
+ (NSString*)findProjectRoot;

// 默认初始化：项目根 = [AVDCBridge findProjectRoot]
- (instancetype)init;

// 指定项目根（测试注入 mock 环境用）
- (instancetype)initWithProjectRoot:(NSString*)projectRoot;

// 是否有任务在运行（同一 Bridge 实例同时只跑一个任务）
@property (nonatomic, readonly) BOOL isRunning;

// 底层：运行 uv run python cli.py <arguments...>；
// stdout 逐行 JSON 解析、stderr 逐行回调（raw）
- (void)runCommand:(NSArray<NSString*>*)arguments
            onLine:(AVDCLineHandler)onLine
             onExit:(AVDCExitHandler)onExit;

// ---- 命令封装 ----

// 扫描目录提取番号：cli.py scan --path
- (void)scanPath:(NSString*)path
    escapeFolder:(nullable NSString*)escapeFolder
       completion:(void (^)(NSArray<NSDictionary*>* _Nullable files,
                            NSError* _Nullable error))completion;

// 批量处理（刮削/整理）：cli.py --path --main-mode --json-output
// mode: 1=scrape 2=organize；事件流经 onEvent 分发
- (void)processPath:(NSString*)path
               mode:(NSInteger)mode
            onEvent:(AVDCEventHandler)onEvent
             onExit:(AVDCExitHandler)onExit;

// 配置：cli.py config list（输出 section.key = value 行）
- (void)configList:(void (^)(NSArray<NSString*>* _Nullable lines,
                             NSError* _Nullable error))completion;

// 配置：cli.py config get <field>
- (void)configGet:(NSString*)field
       completion:(void (^)(NSString* _Nullable value,
                            NSError* _Nullable error))completion;

// 配置：cli.py config set <field> <value>
- (void)configSet:(NSString*)field
            value:(NSString*)value
       completion:(void (^)(NSError* _Nullable error))completion;

// 取消当前任务（SIGTERM，CLI 处理 KeyboardInterrupt）
- (void)terminate;

@end

NS_ASSUME_NONNULL_END
