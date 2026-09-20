#pragma once

#include <string>

namespace core {
struct AppState;
}

namespace ui {

// ImGui 上下文封装：初始化 / 每帧 UI / 渲染 / 释放
// 所有 ObjC 对象以 void* 传递，保持头文件与 GUI 框架无关
class UIManager {
public:
  explicit UIManager(core::AppState& state);
  ~UIManager();

  // shell 层在视图就绪后调用（id<MTLDevice>, NSView*）
  void Init(void* device, void* view);

  // 每帧调用（NSView*, MTLRenderPassDescriptor*）
  void NewFrame(void* view, void* renderPassDescriptor);

  // 渲染（MTLCommandBuffer*, MTLRenderCommandEncoder*）
  void Render(void* commandBuffer, void* renderEncoder);

  void Shutdown();

private:
  core::AppState& state_;
};

}  // namespace ui
