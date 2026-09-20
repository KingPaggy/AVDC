// main.mm — 应用入口（ObjC++ 薄壳层）

#import <Cocoa/Cocoa.h>
#import "AppDelegate.h"

int main(int argc, const char* argv[]) {
  @autoreleasepool {
    NSApplication* app = [NSApplication sharedApplication];
    [app setActivationPolicy:NSApplicationActivationPolicyRegular];

    AppDelegate* delegate = [[AppDelegate alloc] init];
    [NSApp setDelegate:delegate];

    [NSApp activateIgnoringOtherApps:YES];
    [NSApp run];
  }
  return 0;
}
