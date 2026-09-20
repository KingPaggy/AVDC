#pragma once

// 构建标准应用主菜单（屏幕顶部系统区域，不影响窗口无标题栏观感）。
// 菜单项 keyEquivalent 定义系统快捷键；target 为 nil 走 first
// responder chain（AppViewController / NSApplication / NSWindow）。
void BuildMainMenu(void);
