#pragma once

namespace ui {

// sRGB 线性颜色（调色板注入用，头文件无 GUI 框架依赖）
struct RGBA {
  float r = 0, g = 0, b = 0, a = 1;
};

// 语义色调色板：ObjC++ 壳读取 NSColor → RGBA 注入 ImGui 样式
// 实现见 Palette.mm（含 AppKit / 无障碍检测，保持头文件框架无关）
struct PaletteData {
  RGBA label;            // labelColor
  RGBA secondaryLabel;   // secondaryLabelColor
  RGBA tertiaryLabel;    // tertiaryLabelColor
  RGBA accent;           // controlAccentColor
  RGBA separator;        // separatorColor
  RGBA windowBg;         // windowBackgroundColor
  RGBA contentBg;        // controlBackgroundColor（内容区背景）
  RGBA grid;             // gridColor
  RGBA selectedBg;       // selectedContentBackgroundColor
  RGBA link;             // linkColor

  bool isDark = false;           // 当前外观是否为深色
  bool reduceTransparency = false;  // 无障碍：减少透明度
  bool reduceMotion = false;        // 无障碍：减弱动效
  bool increaseContrast = false;    // 无障碍：提高对比度
};

class Palette {
public:
  // 从当前外观（浅/深）与无障碍设置刷新（每帧调用，内部比较变化）
  // view: 所属 NSView*（窗口级外观解析），可为 null 回退应用级
  static void Refresh(void* view);

  // 取当前调色板
  static const PaletteData& Current();

  // 注入 ImGui 样式表（主题/无障碍变化时自动重调）
  static void ApplyToImGui();

private:
  static PaletteData data_;
};

}  // namespace ui
