# PySide6 GUI 概览

> PySide6 + QML 前端，Apple HIG 暗色风格。

## 推荐学习路径

### 第一次接触（30 分钟）

按以下顺序阅读，快速理解项目架构：

| 步骤 | 文档 | 你将了解 |
|------|------|----------|
| 1 | [d01-architecture.md](d01-architecture.md) | 整体架构：Python ↔ QML 如何协作、Context Property 注册顺序 |
| 2 | [d09-data-binding.md](d09-data-binding.md) | 数据绑定：Property 注册、Signal 通知链、双向绑定防循环 |
| 3 | [d02-theme-system.md](d02-theme-system.md) | 视觉系统：Theme 常量如何定义、如何在 QML 中使用 |

### 开始开发（1 小时）

准备动手改代码时：

| 步骤 | 文档 | 你将了解 |
|------|------|----------|
| 4 | [d12-qml-conventions.md](d12-qml-conventions.md) | **代码规范**：命名、布局、import 顺序 |
| 5 | [d05-component-library.md](d05-component-library.md) | 组件速查：现有组件怎么用、如何新增组件 |
| 6 | [d07-qml-pages.md](d07-qml-pages.md) | 页面结构：5 个页面如何组织、数据绑定 |
| 7 | [d04-window-and-nav.md](d04-window-and-nav.md) | 窗口导航：无边框窗口、侧边栏、Toast |

### 遇到问题

调试和避坑：

| 文档 | 解决的问题 |
|------|------------|
| [t01-dynamic-property.md](t01-dynamic-property.md) | QML 访问 Property 返回 undefined |
| [t02-debugging-guide.md](t02-debugging-guide.md) | QML 调试、性能分析、常见错误 |
| [d08-testing.md](d08-testing.md) | 如何写测试、如何运行测试 |

### 进阶主题

| 文档 | 内容 |
|------|------|
| [d03-python-models.md](d03-python-models.md) | Python 模型层详解（SettingsModel、ProcessingModel、EventBus） |
| [d06-animation-and-interaction.md](d06-animation-and-interaction.md) | 动画系统、状态过渡、快捷键 |
| [d10-accessibility.md](d10-accessibility.md) | 无障碍访问（Accessible 属性、键盘导航） |
| [d11-internationalization.md](d11-internationalization.md) | 国际化（qsTr()、翻译工作流） |

---

## 文档索引

| 编号 | 文档 | 类型 | 摘要 |
|------|------|------|------|
| d01 | [d01-architecture.md](d01-architecture.md) | design | 整体架构与数据流 |
| d02 | [d02-theme-system.md](d02-theme-system.md) | design | 颜色/间距/字号常量参考 |
| d03 | [d03-python-models.md](d03-python-models.md) | design | SettingsModel + ProcessingModel 实现 |
| d04 | [d04-window-and-nav.md](d04-window-and-nav.md) | design | 无边框窗口、导航、Toast |
| d05 | [d05-component-library.md](d05-component-library.md) | design | 组件属性速查、布局规范 |
| d06 | [d06-animation-and-interaction.md](d06-animation-and-interaction.md) | design | 动画、状态过渡、快捷键 |
| d07 | [d07-qml-pages.md](d07-qml-pages.md) | design | 5 个页面内部结构 |
| d08 | [d08-testing.md](d08-testing.md) | design | 测试架构、Mock 策略、截图回归 |
| d09 | [d09-data-binding.md](d09-data-binding.md) | design | Python ↔ QML 绑定机制、双向绑定防循环 |
| d10 | [d10-accessibility.md](d10-accessibility.md) | design | Accessible 属性、键盘导航、屏幕阅读器 |
| d11 | [d11-internationalization.md](d11-internationalization.md) | design | qsTr() 翻译、.ts/.qm 文件、本地化 |
| d12 | [d12-qml-conventions.md](d12-qml-conventions.md) | design | QML 代码规范（命名、布局、import） |
| t01 | [t01-dynamic-property.md](t01-dynamic-property.md) | trap | Qt 动态 Property 注册失败的解法 |
| t02 | [t02-debugging-guide.md](t02-debugging-guide.md) | trap | QML 调试、性能分析、常见错误 |
