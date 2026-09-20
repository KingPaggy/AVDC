#pragma once

namespace core {

// GUI 页面导航状态（纯 C++，无 GUI / 系统依赖）
// shell 层修改 page，UI 层每帧读取绘制对应页面
enum class Page { Home, Settings, Tools, Log, About };

struct AppState {
  Page page = Page::Home;   // 当前选中页面
};

}  // namespace core
