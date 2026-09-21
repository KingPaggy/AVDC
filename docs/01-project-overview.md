# AVDC 项目总览

> 一分钟了解 AVDC 是什么、怎么用、怎么开发。

## 项目定位

**AVDC**（AV Data Capture）— 自动抓取 JAV 元数据并整理本地视频文件的桌面工具，输出供 Emby / Kodi / Plex 使用。

## 技术栈

| 层次 | 技术 |
|------|------|
| 语言 | Python 3.13 + Swift |
| GUI（主力） | macOS 原生 SwiftUI（mac-gui） |
| 爬取 | lxml / BeautifulSoup4 / requests / cloudscraper |
| 图像处理 | Pillow + 百度 AI 人脸检测 |
| 包管理 | uv workspace（core + cli 两个成员包） |
| GUI（归档） | PySide6 / PyQt5（.archive/，仅作参考） |

## 模块划分

```
core/           纯业务逻辑（零 Qt 依赖）
mac-gui/        macOS 原生 GUI（主力，纯 SwiftUI）
cli/            命令行工具
tui-go/         Go TUI
.archive/       已归档 GUI（PySide6/PyQt5，2026-09-20）
docs/           技术文档
```

## 核心工作流

```
视频文件 → 提取番号 → 选择站点链 → 抓取元数据 → 下载图片 → 生成 NFO → 重命名归档
```

## 文档导航

按阅读顺序排列：

| # | 文档 | 内容 |
|---|------|------|
| 02 | [architecture.md](02-architecture.md) | 分层架构、设计原则、包结构 |
| 03 | [macos-gui-migration.md](03-macos-gui-migration.md) | mac-gui 迁移方案、CLI 契约 |
| 04 | [tui-lazygit-refactor.md](04-tui-lazygit-refactor.md) | TUI 重构计划（lazygit 式三层） |
| — | [macGUI 设计对齐方案](report-2026-09-21-1016-macGUI-官方设计标准对齐优化方案.md) | 设计系统对齐（决策版 + 执行记录） |

### 核心模块（`core/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [core/01-requirements.md](core/01-requirements.md) | 核心 I/O 黑盒规范 |
| 02 | [core/02-scraping-flow.md](core/02-scraping-flow.md) | 抓取流程、Pipeline、Scraper Chain |

### PySide6 GUI（`pyside6gui/`，已归档，仅作功能对照参考）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [pyside6gui/d12-qml-conventions.md](pyside6gui/d12-qml-conventions.md) | QML 代码规范、命名、布局、import |
| 02 | [pyside6gui/t01-dynamic-property.md](pyside6gui/t01-dynamic-property.md) | 动态 Property 踩坑与类工厂解法 |

### TUI 重构（`tui/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [tui/d01-phase-plan.md](tui/d01-phase-plan.md) | Phase 0-6 分阶段计划 |
| 02 | [tui/d02-lazygit-architecture.md](tui/d02-lazygit-architecture.md) | lazygit 架构方案 |
| 03 | [tui/d03-lazygit-keybindings.md](tui/d03-lazygit-keybindings.md) | lazygit 键位体系 |
| 04 | [tui/d04-avdc-design.md](tui/d04-avdc-design.md) | AVDC 面板/Context 设计 |
| 05 | [tui/d05-avdc-keybindings.md](tui/d05-avdc-keybindings.md) | AVDC 各 context 键位表 |

### 工具链（`tooling/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [tooling/01-codegraph.md](tooling/01-codegraph.md) | CodeGraph 代码智能工具使用指南 |
