// Menus.mm — 标准应用菜单栏构建（ObjC++ 薄壳层）
// 快捷键经菜单项 keyEquivalent 定义（macOS 标准做法），菜单栏位于
// 屏幕顶部系统区域，不影响窗口的透明标题栏 / fullSize 观感。
// 菜单项 target 全部为 nil，action 走 first responder chain：
//   - onZoomWindow:              → AppViewController（窗口操作）
//   - selectPage*:               → AppViewController（转 onPageSelected:）
//   - 其余（terminate/hide/...） → NSApplication / NSWindow 标准响应

#import <Cocoa/Cocoa.h>

#include "Menus.h"

// 添加菜单项并显式设置修饰键掩码（0 = 默认 Command）
static NSMenuItem* AddItem(NSMenu* menu, NSString* title, SEL action,
                           NSString* keyEquivalent,
                           NSEventModifierFlags mask) {
  NSMenuItem* item = [menu addItemWithTitle:title
                                     action:action
                              keyEquivalent:keyEquivalent];
  item.keyEquivalentModifierMask = mask;
  return item;
}

void BuildMainMenu(void) {
  NSMenu* mainMenu = [[NSMenu alloc] init];

  // ---- 应用菜单（标题取进程名）----
  NSMenuItem* appItem = [[NSMenuItem alloc] init];
  [mainMenu addItem:appItem];
  NSMenu* appMenu = [[NSMenu alloc] init];
  appItem.submenu = appMenu;

  NSString* appName = [[NSProcessInfo processInfo] processName];
  [appMenu addItemWithTitle:[NSString stringWithFormat:@"About %@", appName]
                     action:@selector(orderFrontStandardAboutPanel:)
              keyEquivalent:@""];
  [appMenu addItem:[NSMenuItem separatorItem]];

  // Preferences…（Cmd+,）：暂无设置功能，置灰占位，后续接入
  NSMenuItem* prefs = [appMenu addItemWithTitle:@"Preferences…"
                                         action:nil
                                  keyEquivalent:@","];
  prefs.enabled = NO;
  [appMenu addItem:[NSMenuItem separatorItem]];

  AddItem(appMenu, @"Hide", @selector(hide:), @"h", NSEventModifierFlagCommand);
  AddItem(appMenu, @"Hide Others", @selector(hideOtherApplications:), @"h",
          NSEventModifierFlagCommand | NSEventModifierFlagOption);
  AddItem(appMenu, @"Show All", @selector(unhideAllApplications:), @"", 0);
  [appMenu addItem:[NSMenuItem separatorItem]];
  AddItem(appMenu, [NSString stringWithFormat:@"Quit %@", appName],
          @selector(terminate:), @"q", NSEventModifierFlagCommand);

  // ---- File ----
  NSMenuItem* fileItem = [[NSMenuItem alloc] init];
  [mainMenu addItem:fileItem];
  NSMenu* fileMenu = [[NSMenu alloc] initWithTitle:@"File"];
  fileItem.submenu = fileMenu;
  AddItem(fileMenu, @"Close Window", @selector(performClose:), @"w",
          NSEventModifierFlagCommand);

  // ---- View（标准含 Enter Full Screen，⌃⌘F）----
  NSMenuItem* viewItem = [[NSMenuItem alloc] init];
  [mainMenu addItem:viewItem];
  NSMenu* viewMenu = [[NSMenu alloc] initWithTitle:@"View"];
  viewItem.submenu = viewMenu;
  AddItem(viewMenu, @"Toggle Full Screen", @selector(toggleFullScreen:), @"f",
          NSEventModifierFlagControl | NSEventModifierFlagCommand);

  // ---- Window（标准含 Minimize ⌘M / Zoom）----
  NSMenuItem* winItem = [[NSMenuItem alloc] init];
  [mainMenu addItem:winItem];
  NSMenu* winMenu = [[NSMenu alloc] initWithTitle:@"Window"];
  winItem.submenu = winMenu;
  AddItem(winMenu, @"Minimize", @selector(performMiniaturize:), @"m",
          NSEventModifierFlagCommand);
  AddItem(winMenu, @"Zoom Window", @selector(onZoomWindow:), @"=",
          NSEventModifierFlagCommand);

  // ---- Page（快捷键直切，侧边栏选中态由 onPageSelected: 同步）----
  NSMenuItem* pgItem = [[NSMenuItem alloc] init];
  [mainMenu addItem:pgItem];
  NSMenu* pgMenu = [[NSMenu alloc] initWithTitle:@"Page"];
  pgItem.submenu = pgMenu;
  AddItem(pgMenu, @"主页", @selector(selectPageHome:), @"1",
          NSEventModifierFlagCommand);
  AddItem(pgMenu, @"设置", @selector(selectPageSettings:), @"2",
          NSEventModifierFlagCommand);
  AddItem(pgMenu, @"工具", @selector(selectPageTools:), @"3",
          NSEventModifierFlagCommand);
  AddItem(pgMenu, @"日志", @selector(selectPageLog:), @"4",
          NSEventModifierFlagCommand);
  AddItem(pgMenu, @"关于", @selector(selectPageAbout:), @"5",
          NSEventModifierFlagCommand);

  NSApp.mainMenu = mainMenu;
}
