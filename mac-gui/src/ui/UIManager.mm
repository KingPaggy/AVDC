// UIManager.mm — ImGui 上下文与业务 UI（ObjC++ 编译）
// 视觉对齐 macOS 27 设计规范：语义色调色板（Palette）、
// 系统字体（SF Pro 西文 + PingFang 中文）、HIG 8pt 网格间距。
// 阶段 0：5 页导航骨架，内容区绘制页面占位（验证中文渲染）；
// 后续阶段按页面填充实际组件（表单/日志/卡片）。

#import <Metal/Metal.h>
#import <AppKit/AppKit.h>
#import <CoreText/CoreText.h>

#include "ui/UIManager.hpp"
#include "ui/UIConfig.hpp"
#include "ui/Palette.hpp"

#include "imgui.h"
#include "imgui_impl_metal.h"
#include "imgui_impl_osx.h"

#include "core/AppState.hpp"

#include <cstdio>
#include <string>
#include <vector>

namespace ui {

namespace {

// RGBA → ImGui 颜色（Palette 数据转 ImVec4）
static ImVec4 ToVec4f(const RGBA& c) {
  return ImVec4(c.r, c.g, c.b, c.a);
}

// 页面占位内容：居中大标题 + 说明文字（阶段 0 骨架，
// 验证中文渲染；后续阶段替换为实际页面组件）
struct PageInfo {
  const char* title;      // 大标题
  const char* subtitle;   // 说明
};

// 与 core::Page 枚举顺序一致（Home/Settings/Tools/Log/About）
const PageInfo kPages[] = {
  {"主页", "输入目录、处理模式、进度（阶段 1 实现）"},
  {"设置", "配置表单：代理/命名规则/媒体等（阶段 3 实现）"},
  {"工具", "批量重命名、封面裁剪、Emby 集成（阶段 4 实现）"},
  {"日志", "运行日志查看与级别过滤（阶段 4 实现）"},
  {"关于", "版本信息与项目链接（阶段 4 实现）"},
};

void DrawPagePlaceholder(ImDrawList* dl, const ImVec2& p0, const ImVec2& p1,
                         int page, const PaletteData& pal) {
  const PageInfo& info = kPages[page];

  // 背景（内容层用标准材质色，docs-macOS27-01）
  dl->AddRectFilled(p0, p1,
                    ImGui::ColorConvertFloat4ToU32(ToVec4f(pal.contentBg)));

  const ImU32 titleCol = ImGui::ColorConvertFloat4ToU32(ToVec4f(pal.label));
  const ImU32 subCol = ImGui::ColorConvertFloat4ToU32(
      ToVec4f(pal.secondaryLabel));

  const ImVec2 c = ImVec2((p0.x + p1.x) * 0.5f, (p0.y + p1.y) * 0.5f);

  // 大标题（24pt 中文，验证 PingFang 渲染）
  ImFont* titleFont = ImGui::GetIO().Fonts->Fonts.Size > 2
      ? ImGui::GetIO().Fonts->Fonts[2]
      : ImGui::GetFont();
  const float titleSize = 24.0f;
  ImVec2 ts = titleFont->CalcTextSizeA(titleSize, FLT_MAX, 0.0f, info.title);
  dl->AddText(titleFont, titleSize, ImVec2(c.x - ts.x * 0.5f, c.y - 40.0f),
              titleCol, info.title);

  // 说明文字（13pt 副标题色）
  ImFont* font = ImGui::GetFont();
  const float fs = 13.0f;
  ImVec2 ss = font->CalcTextSizeA(fs, FLT_MAX, 0.0f, info.subtitle);
  dl->AddText(font, fs, ImVec2(c.x - ss.x * 0.5f, c.y + 4.0f), subCol,
              info.subtitle);
}

}  // namespace

UIManager::UIManager(core::AppState& state) : state_(state) {
  IMGUI_CHECKVERSION();
  ImGui::CreateContext();
  ImGuiIO& io = ImGui::GetIO();
  io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;

  // HIG 间距与圆角（docs-macOS27-10；GG 收敛圆角 8–10pt）
  ImGuiStyle& s = ImGui::GetStyle();
  s.WindowPadding = ImVec2(0, 0);
  s.ItemSpacing = ImVec2(UIConfig::kSpacing, UIConfig::kStackGap);
  s.WindowBorderSize = 0.0f;
  s.WindowRounding = UIConfig::kCornerRadius;
  s.FrameRounding = UIConfig::kCornerRadius;
  s.ChildRounding = UIConfig::kCornerRadius;
  s.ScrollbarRounding = UIConfig::kCornerRadius;
  s.GrabRounding = UIConfig::kCornerRadius;
  s.AntiAliasedLines = true;
  s.AntiAliasedFill = true;

  // 语义色主题（替换 StyleColorsDark）
  Palette::Refresh(nullptr);
  Palette::ApplyToImGui();
}

UIManager::~UIManager() { Shutdown(); }

void UIManager::Init(void* device, void* view) {
  // 系统字体：SF Pro 13pt 正文 + 17pt 标题 + PingFang 24pt 页面大标题
  // （中文必须单独字体，SFNS.ttf 无 CJK；须在
  // ImGui_ImplMetal_Init 之前加入 io.Fonts）
  ImGuiIO& io = ImGui::GetIO();
  ImFontConfig cfg;
  cfg.OversampleH = 2;
  cfg.OversampleV = 2;
  const ImWchar* latin = io.Fonts->GetGlyphRangesDefault();
  const ImWchar* chinese = io.Fonts->GetGlyphRangesChineseFull();
  io.Fonts->AddFontFromFileTTF("/System/Library/Fonts/SFNS.ttf", 13.0f,
                               &cfg, latin);
  io.Fonts->AddFontFromFileTTF("/System/Library/Fonts/SFNS.ttf", 17.0f,
                               &cfg, latin);
  // PingFang SC（中文）：CoreText 动态查询字体 URL，避免硬编码
  // AssetsV2 资产路径（含 hash，系统更新可能变化）；
  // PingFang.ttc 为字体集合，FontNo=0 即 PingFang SC Regular
  {
    CTFontDescriptorRef desc = CTFontDescriptorCreateWithNameAndSize(
        CFSTR("PingFangSC-Regular"), 13.0);
    CFURLRef url = (CFURLRef)CTFontDescriptorCopyAttribute(
        desc, kCTFontURLAttribute);
    if (url) {
      NSData* data = [NSData dataWithContentsOfURL:(__bridge NSURL*)url];
      if (data) {
        cfg.FontNo = 0;
        io.Fonts->AddFontFromMemoryTTF((void*)data.bytes,
                                       (int)data.length, 24.0f,
                                       &cfg, chinese);
      } else {
        NSLog(@"[UIManager] 无法读取 PingFang 字体文件");
      }
      CFRelease(url);
    } else {
      NSLog(@"[UIManager] 无法定位 PingFang SC 字体");
    }
    CFRelease(desc);
  }

  ImGui_ImplMetal_Init((__bridge id<MTLDevice>)device);
  ImGui_ImplOSX_Init((__bridge NSView*)view);
}

void UIManager::NewFrame(void* view, void* renderPassDescriptor) {
  // 语义色 / 无障碍设置刷新（内部有变化才重注入样式）；
  // 传 view 以窗口级 effectiveAppearance 解析浅/深色
  Palette::Refresh(view);

  NSView* nsView = (__bridge NSView*)view;
  ImGuiIO& io = ImGui::GetIO();
  io.DisplaySize.x = nsView.bounds.size.width;
  io.DisplaySize.y = nsView.bounds.size.height;
  CGFloat scale = nsView.window.screen.backingScaleFactor
                      ?: NSScreen.mainScreen.backingScaleFactor;
  io.DisplayFramebufferScale = ImVec2(scale, scale);

  ImGui_ImplMetal_NewFrame(
      (__bridge MTLRenderPassDescriptor*)renderPassDescriptor);
  ImGui_ImplOSX_NewFrame((__bridge NSView*)view);
  ImGui::NewFrame();

  const PaletteData& pal = Palette::Current();
  const int page = (int)state_.page;

  // ---- 内容区：全屏无装饰窗口，铺满整个 MTKView ----
  {
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
    ImGui::Begin("##content", nullptr,
                 ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
                     ImGuiWindowFlags_NoMove |
                     ImGuiWindowFlags_NoCollapse |
                     ImGuiWindowFlags_NoBringToFrontOnFocus |
                     ImGuiWindowFlags_NoSavedSettings);

    // HIG 布局：外边距 20pt；顶部与信息条拉开 8pt
    const float m = UIConfig::kMargin;
    const float topM = m + 8.0f;
    ImDrawList* dl = ImGui::GetWindowDrawList();
    const ImVec2 wPos = ImGui::GetWindowPos();
    const ImVec2 p0 = ImVec2(wPos.x + m, wPos.y + topM);
    const ImVec2 p1 = ImVec2(wPos.x + io.DisplaySize.x - m,
                             wPos.y + io.DisplaySize.y - m);

    DrawPagePlaceholder(dl, p0, p1, page, pal);

    ImGui::End();
    ImGui::PopStyleVar(2);
  }
}

void UIManager::Render(void* commandBuffer, void* renderEncoder) {
  ImGui::Render();
  ImDrawData* drawData = ImGui::GetDrawData();
  ImGui_ImplMetal_RenderDrawData(
      drawData, (__bridge id<MTLCommandBuffer>)commandBuffer,
      (__bridge id<MTLRenderCommandEncoder>)renderEncoder);
}

void UIManager::Shutdown() {
  ImGui_ImplMetal_Shutdown();
  ImGui_ImplOSX_Shutdown();
  ImGui::DestroyContext();
}

}  // namespace ui
