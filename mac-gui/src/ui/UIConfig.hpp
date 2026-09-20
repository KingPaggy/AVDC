#pragma once

namespace ui {

// HIG 8pt 基线网格 + Golden Gate 视觉参数
// 依据 docs-macOS27-10（HIG 视觉规格）与 -11（自绘对齐）。
// 集中管理视觉常量，随系统版本微调只改这里。
struct UIConfig {
  static constexpr float kMargin = 20.0f;        // 窗口内容外边距（HIG 20pt）
  static constexpr float kSpacing = 8.0f;        // 控件间水平间距（HIG 8pt）
  static constexpr float kStackGap = 6.0f;       // 纵向堆叠最小间距（HIG 6pt）
  static constexpr float kLabelGap = 4.0f;       // 描述性标签间隙（HIG 4pt）
  static constexpr float kCornerRadius = 9.0f;   // GG 收敛圆角（8–10pt 取中）
  static constexpr float kToolbarItemGap = 8.0f; // 工具栏项间距（HIG 8pt）
};

}  // namespace ui
