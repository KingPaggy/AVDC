// Palette.mm — 语义色调色板（ObjC++：NSColor → RGBA）
// 依据 docs-macOS27-10（HIG Color）读取系统语义色，
// 供 ImGui 自绘层注入，实现浅/深色与无障碍设置自动适配。
// 无障碍降级规则见 docs-macOS27-06（-11 §6）。

#import <AppKit/AppKit.h>

#include <cstring>

#include "ui/Palette.hpp"
#include "imgui.h"

namespace ui {

PaletteData Palette::data_;

// NSColor 语义色 → sRGB RGBA
static void FillRGBA(RGBA* out, NSColor* color) {
  NSColor* srgb = [color colorUsingColorSpace:NSColorSpace.sRGBColorSpace];
  if (!srgb) return;
  CGFloat r = 0, g = 0, b = 0, a = 1;
  [srgb getRed:&r green:&g blue:&b alpha:&a];
  *out = {(float)r, (float)g, (float)b, (float)a};
}

// RGBA → ImGui 颜色
static ImVec4 ToVec4(const RGBA& c) {
  return ImVec4(c.r, c.g, c.b, c.a);
}

static ImVec4 WithAlpha(const RGBA& c, float a) {
  return ImVec4(c.r, c.g, c.b, a);
}

void Palette::Refresh(void* viewPtr) {
  __block PaletteData d;

  // 外观（浅/深色，docs-macOS27-11 §共享调色板）
  // 优先取所属窗口的 effectiveAppearance（窗口级，最准确），
  // 无窗口时回退应用级（NSApp.effectiveAppearance）
  NSAppearance* appearance = nil;
  if (viewPtr) {
    NSView* v = (__bridge NSView*)viewPtr;
    appearance = v.window ? v.window.effectiveAppearance
                          : NSApp.effectiveAppearance;
  } else {
    appearance = NSApp.effectiveAppearance;
  }
  NSAppearanceName matched = [appearance
      bestMatchFromAppearancesWithNames:@[
        NSAppearanceNameAqua, NSAppearanceNameDarkAqua]];
  d.isDark = [matched isEqualToString:NSAppearanceNameDarkAqua];

  // 关键：Metal 渲染回调不在 AppKit drawing 上下文，dynamic color
  // （语义色）不会自动跟随外观切换。以窗口外观作为当前 drawing
  // 外观上下文解析，确保解析出最新浅/深色变体（官方 API）。
  [appearance performAsCurrentDrawingAppearance:^{
    // 语义色（HIG Color：自动适配浅/深色）
    FillRGBA(&d.label, NSColor.labelColor);
    FillRGBA(&d.secondaryLabel, NSColor.secondaryLabelColor);
    FillRGBA(&d.tertiaryLabel, NSColor.tertiaryLabelColor);
    FillRGBA(&d.accent, NSColor.controlAccentColor);
    FillRGBA(&d.separator, NSColor.separatorColor);
    FillRGBA(&d.windowBg, NSColor.windowBackgroundColor);
    FillRGBA(&d.contentBg, NSColor.controlBackgroundColor);
    FillRGBA(&d.grid, NSColor.gridColor);
    FillRGBA(&d.selectedBg, NSColor.selectedContentBackgroundColor);
    FillRGBA(&d.link, NSColor.linkColor);
  }];

  // 无障碍三项设置（docs-macOS27-06 / -11 §7）
  NSWorkspace* ws = NSWorkspace.sharedWorkspace;
  d.reduceTransparency = ws.accessibilityDisplayShouldReduceTransparency;
  d.reduceMotion = ws.accessibilityDisplayShouldReduceMotion;
  d.increaseContrast = ws.accessibilityDisplayShouldIncreaseContrast;

  // 有变化才重注入样式表（避免每帧重写）
  if (memcmp(&d, &data_, sizeof(PaletteData)) != 0) {
    data_ = d;
    ApplyToImGui();
  }
}

void Palette::ApplyToImGui() {
  const PaletteData& d = data_;
  ImGuiStyle& s = ImGui::GetStyle();
  ImVec4* c = s.Colors;

  // 文本层级（label → tertiary）
  c[ImGuiCol_Text] = ToVec4(d.label);
  c[ImGuiCol_TextDisabled] = ToVec4(d.tertiaryLabel);

  // 背景与边框：内容区透明，由自绘波形填充
  c[ImGuiCol_WindowBg] = ImVec4(0, 0, 0, 0);
  c[ImGuiCol_ChildBg] = ImVec4(0, 0, 0, 0);
  c[ImGuiCol_Border] = ToVec4(d.separator);
  c[ImGuiCol_FrameBg] = ImVec4(0, 0, 0, 0);

  // 强调色（accent）：波形、选中、交互态
  c[ImGuiCol_PlotLines] = ToVec4(d.accent);
  c[ImGuiCol_PlotLinesHovered] = WithAlpha(d.accent, 1.0f);
  c[ImGuiCol_Header] = WithAlpha(d.accent, 0.15f);
  c[ImGuiCol_HeaderHovered] = WithAlpha(d.accent, 0.22f);
  c[ImGuiCol_HeaderActive] = WithAlpha(d.accent, 0.30f);
  c[ImGuiCol_TextSelectedBg] = WithAlpha(d.accent, 0.35f);
  c[ImGuiCol_Separator] = ToVec4(d.separator);
  c[ImGuiCol_Button] = ImVec4(0, 0, 0, 0);
  c[ImGuiCol_ButtonHovered] = WithAlpha(d.label, 0.08f);
  c[ImGuiCol_ButtonActive] = WithAlpha(d.label, 0.14f);

  // 提高对比度：自绘控件加对比边框，弱化透明依赖
  // （docs-macOS27-06：元素主要变为黑/白并用对比边框突出）
  if (d.increaseContrast) {
    c[ImGuiCol_Border] = ToVec4(d.label);
    s.FrameBorderSize = 1.0f;
  } else {
    s.FrameBorderSize = 0.0f;
  }
}

const PaletteData& Palette::Current() { return data_; }

}  // namespace ui
