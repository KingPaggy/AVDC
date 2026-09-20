// AppDelegate.mm — ObjC++ 薄壳层
// AppKit 页面框架（侧边栏 + 内容区）+ MTKView 内容区（ImGui）
// 阶段 0：5 页导航骨架（主页/设置/工具/日志/关于）

#import "AppDelegate.h"

#include "Menus.h"

#import <AppKit/AppKit.h>
#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>

#include "ui/UIManager.hpp"
#include "ui/Palette.hpp"
#include "core/AppState.hpp"

#import "AVDCMacGUI-Swift.h"

//---------------------------------------------------------------------------
// AppViewController：AppKit 页面框架 + MTKView（ImGui 内容区）
// 左侧边栏由 SwiftUI（NSHostingView）承载；内容区 = SwiftUI
// 信息条（页面标题 + 全屏玻璃按钮）+ ImGui 页面内容
//---------------------------------------------------------------------------

@interface AppViewController : NSViewController <MTKViewDelegate>
@property (nonatomic, strong) id<MTLDevice> device;
@property (nonatomic, strong) id<MTLCommandQueue> commandQueue;
@property (nonatomic, strong) MTKView* mtkView;
@property (nonatomic, strong) SidebarView* sidebarView;
@property (nonatomic, strong) InfoBarView* infoBar;
@end

@implementation AppViewController {
  core::AppState state_;        // 页面导航状态（core 纯 C++）
  ui::UIManager* uiManager_;    // ImGui 上下文
  NSArray<NSString*>* pageNames_;
  NSInteger currentPage_;
  NSLayoutConstraint* infoBarTop_;   // 信息条顶部避让（标题栏/菜单栏）
}

- (instancetype)initWithNibName:(NSString*)nibNameOrNil
                         bundle:(NSBundle*)nibBundleOrNil {
  self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
  if (self) {
    _device = MTLCreateSystemDefaultDevice();
    _commandQueue = [_device newCommandQueue];
    if (!_device) {
      NSLog(@"Metal is not supported on this device");
      abort();
    }
    uiManager_ = new ui::UIManager(state_);   // ImGui 上下文
    pageNames_ = @[@"主页", @"设置", @"工具", @"日志", @"关于"];
    currentPage_ = 0;
  }
  return self;
}

- (void)dealloc {
  if (uiManager_) {
    uiManager_->Shutdown();
    delete uiManager_;
  }
}

//---------------------------------------------------------------------------
// 视图层级：NSSplitView = 左 AppKit 侧边栏 + 右 MTKView 内容区
//---------------------------------------------------------------------------

- (void)loadView {
  NSView* root = [[NSView alloc] initWithFrame:NSMakeRect(0, 0, 1200, 800)];
  self.view = root;

  // ---- 左侧：SwiftUI 侧边栏（NSHostingView 嵌入 AppKit） ----
  NSView* sidebar = [[NSView alloc] init];
  sidebar.translatesAutoresizingMaskIntoConstraints = NO;

  __weak typeof(self) weakSelf = self;
  SidebarView* sv = [[SidebarView alloc] initOnSelect:^(NSInteger idx) {
    [weakSelf onPageSelected:idx];
  }];
  self.sidebarView = sv;
  sv.view.translatesAutoresizingMaskIntoConstraints = NO;
  [sidebar addSubview:sv.view];
  [NSLayoutConstraint activateConstraints:@[
    [sv.view.topAnchor constraintEqualToAnchor:sidebar.topAnchor],
    [sv.view.leadingAnchor constraintEqualToAnchor:sidebar.leadingAnchor],
    [sv.view.trailingAnchor constraintEqualToAnchor:sidebar.trailingAnchor],
    [sv.view.bottomAnchor constraintEqualToAnchor:sidebar.bottomAnchor],
  ]];

  // ---- 右侧：内容区 = SwiftUI 信息条 + MTKView（ImGui 页面内容）----
  // 文字层（页面标题/按钮）原生 SwiftUI，ImGui 绘制页面内容
  NSView* content = [[NSView alloc] init];
  content.translatesAutoresizingMaskIntoConstraints = NO;

  InfoBarView* bar = [[InfoBarView alloc]
      initOnToggleFullScreen:^{ [weakSelf.view.window toggleFullScreen:nil]; }];
  self.infoBar = bar;
  bar.view.translatesAutoresizingMaskIntoConstraints = NO;
  [content addSubview:bar.view];

  MTKView* mtkView = [[MTKView alloc] init];
  mtkView.translatesAutoresizingMaskIntoConstraints = NO;
  mtkView.device = _device;
  mtkView.delegate = self;
  self.mtkView = mtkView;
  [content addSubview:mtkView];

  // 信息条顶部锚定（顶部约束 0：非全屏/全屏位置一致，落入标题栏行）；
  // leading 绑定 LayoutRegion 角部避让 guide（macOS 26+），
  // 自动避让左上角红绿灯/圆角区域，无需手动测量宽度
  NSLayoutConstraint* barTop = [bar.view.topAnchor
      constraintEqualToAnchor:content.topAnchor];
  infoBarTop_ = barTop;
  NSLayoutGuide* leadGuide = [content layoutGuideForLayoutRegion:
      [NSViewLayoutRegion safeAreaLayoutRegionWithCornerAdaptation:
          NSViewLayoutRegionAdaptivityAxisHorizontal]];
  [NSLayoutConstraint activateConstraints:@[
    barTop,
    [bar.view.leadingAnchor constraintEqualToAnchor:leadGuide.leadingAnchor],
    [bar.view.trailingAnchor constraintEqualToAnchor:content.trailingAnchor],
    [bar.view.heightAnchor constraintEqualToConstant:40.0f],
    [mtkView.topAnchor constraintEqualToAnchor:bar.view.bottomAnchor],
    [mtkView.leadingAnchor constraintEqualToAnchor:content.leadingAnchor],
    [mtkView.trailingAnchor constraintEqualToAnchor:content.trailingAnchor],
    [mtkView.bottomAnchor constraintEqualToAnchor:content.bottomAnchor],
  ]];

  // ---- NSSplitView ----
  NSSplitView* split = [[NSSplitView alloc] init];
  split.translatesAutoresizingMaskIntoConstraints = NO;
  split.vertical = YES;
  split.dividerStyle = NSSplitViewDividerStyleThin;
  [split addArrangedSubview:sidebar];
  [split addArrangedSubview:content];
  [split setHoldingPriority:NSLayoutPriorityDefaultLow
              forSubviewAtIndex:0];

  [root addSubview:split];
  [NSLayoutConstraint activateConstraints:@[
    [split.topAnchor constraintEqualToAnchor:root.topAnchor],
    [split.leadingAnchor constraintEqualToAnchor:root.leadingAnchor],
    [split.trailingAnchor constraintEqualToAnchor:root.trailingAnchor],
    [split.bottomAnchor constraintEqualToAnchor:root.bottomAnchor],
    [sidebar.widthAnchor constraintEqualToConstant:200],
  ]];

  // 信息条初始标题（当前页）
  [self.infoBar setTitle:pageNames_[currentPage_]];
}

- (void)viewDidLoad {
  [super viewDidLoad];
  // ImGui 事件绑定到内容区（MTKView），与 AppKit 控件互不干扰
  uiManager_->Init((__bridge void*)_device, (__bridge void*)self.mtkView);
}

- (void)viewDidAppear {
  [super viewDidAppear];
  // 内容顶部锚定（fullSize 下内容延伸至标题栏/菜单栏区域，
  // 全屏/非全屏位置一致）
  [self updateContentTopInset];
  NSWindow* window = self.view.window;
  [[NSNotificationCenter defaultCenter] addObserver:self
      selector:@selector(onFullScreenChanged:)
      name:NSWindowDidEnterFullScreenNotification object:window];
  [[NSNotificationCenter defaultCenter] addObserver:self
      selector:@selector(onFullScreenChanged:)
      name:NSWindowDidExitFullScreenNotification object:window];
}

- (void)viewDidDisappear {
  [[NSNotificationCenter defaultCenter] removeObserver:self
      name:NSWindowDidEnterFullScreenNotification object:nil];
  [[NSNotificationCenter defaultCenter] removeObserver:self
      name:NSWindowDidExitFullScreenNotification object:nil];
  [super viewDidDisappear];
}

// 全屏/非全屏内容位置一致：InfoBar 均锚定窗口顶部（top = 0，
// 与左侧侧边栏同）；红绿灯避让由 LayoutRegion 角部 guide
// （leading 约束）自动处理，全屏时 guide 自动归零
- (void)updateContentTopInset {
  infoBarTop_.constant = 0;
}

// 全屏切换即时刷新（不依赖窗口尺寸变化事件）
- (void)onFullScreenChanged:(NSNotification*)note {
  [self updateContentTopInset];
}

//---------------------------------------------------------------------------
// 窗口操作（信息条按钮 / 菜单快捷键共用）
//---------------------------------------------------------------------------
- (void)onZoomWindow:(id)sender {
  [self.view.window zoom:sender];
}

//---------------------------------------------------------------------------
// 帧循环（MTKViewDelegate）
//---------------------------------------------------------------------------

- (void)mtkView:(MTKView*)view drawableSizeWillChange:(CGSize)size {
  [self updateContentTopInset];   // 窗口尺寸变化时刷新避让高度
}

- (void)drawInMTKView:(MTKView*)view {
  id<MTLCommandBuffer> commandBuffer = [self.commandQueue commandBuffer];
  MTLRenderPassDescriptor* rpd = view.currentRenderPassDescriptor;
  if (rpd == nil) {
    [commandBuffer commit];
    return;
  }

  uiManager_->NewFrame((__bridge void*)self.mtkView,
                       (__bridge void*)rpd);

  // 内容区背景跟随系统外观（controlBackgroundColor 语义色，
  // 浅/深自动适配；与页面内容背景一致，避免透明边距露旧深灰）
  const ui::RGBA& bg = ui::Palette::Current().contentBg;
  rpd.colorAttachments[0].clearColor =
      MTLClearColorMake(bg.r, bg.g, bg.b, bg.a);
  id<MTLRenderCommandEncoder> encoder =
      [commandBuffer renderCommandEncoderWithDescriptor:rpd];
  uiManager_->Render((__bridge void*)commandBuffer,
                     (__bridge void*)encoder);
  [encoder endEncoding];

  [commandBuffer presentDrawable:view.currentDrawable];
  [commandBuffer commit];
}

//---------------------------------------------------------------------------
// SwiftUI 侧边栏回调（NSHostingView 嵌入）
//---------------------------------------------------------------------------

- (void)onPageSelected:(NSInteger)idx {
  if (idx < 0 || idx >= (NSInteger)pageNames_.count) return;
  NSLog(@"page -> %@ (idx %ld)", pageNames_[idx], (long)idx);
  currentPage_ = idx;
  state_.page = (core::Page)idx;   // ImGui 每帧读取刷新
  // 同步选中态到侧边栏（高亮回显，防重复触发有 guard）
  [self.sidebarView setSelectedIndex:idx];
  // 信息条标题刷新
  [self.infoBar setTitle:pageNames_[idx]];
}

// 菜单快捷键（Cmd+1..5）入口：菜单 action 只传 sender 对象，
// 复用统一入口（侧边栏选中态同步）
- (void)selectPageHome:(id)sender     { [self onPageSelected:0]; }
- (void)selectPageSettings:(id)sender { [self onPageSelected:1]; }
- (void)selectPageTools:(id)sender    { [self onPageSelected:2]; }
- (void)selectPageLog:(id)sender      { [self onPageSelected:3]; }
- (void)selectPageAbout:(id)sender    { [self onPageSelected:4]; }

@end

//---------------------------------------------------------------------------
// AppDelegate：应用生命周期 + 主窗口
//---------------------------------------------------------------------------

@implementation AppDelegate

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:
    (NSApplication*)sender {
  return YES;
}

- (instancetype)init {
  if (self = [super init]) {
    AppViewController* vc =
        [[AppViewController alloc] initWithNibName:nil bundle:nil];
    NSWindow* window = [[NSWindow alloc]
        initWithContentRect:NSZeroRect
                  styleMask:NSWindowStyleMaskTitled |
                            NSWindowStyleMaskClosable |
                            NSWindowStyleMaskResizable |
                            NSWindowStyleMaskMiniaturizable
                    backing:NSBackingStoreBuffered
                      defer:NO];
    window.contentViewController = vc;
    // 方案 B：透明标题栏（report-2026-09-17-1758 §5）
    window.titlebarAppearsTransparent = YES;
    window.titleVisibility = NSWindowTitleHidden;
    window.titlebarSeparatorStyle = NSTitlebarSeparatorStyleNone;
    window.styleMask |= NSWindowStyleMaskFullSizeContentView;
    [window center];
    [window makeKeyAndOrderFront:self];

    // 标准应用菜单栏（屏幕顶部系统区域）；快捷键经菜单项 keyEquivalent
    // 定义，菜单项 target 为 nil 走 first responder chain
    BuildMainMenu();
  }
  return self;
}

@end
