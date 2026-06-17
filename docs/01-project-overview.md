# AVDC 项目总览

> 一分钟了解 AVDC 是什么、怎么用、怎么开发。

## 项目定位

**AVDC**（AV Data Capture）— 自动抓取 JAV 元数据并整理本地视频文件的桌面工具，输出供 Emby / Kodi / Plex 使用。

## 技术栈

| 层次 | 技术 |
|------|------|
| 语言 | Python 3.13 |
| GUI（主力） | PySide6 + QML，Apple HIG 暗色风格 |
| GUI（遗留） | PyQt5（仅维护） |
| 爬取 | lxml / BeautifulSoup4 / requests / cloudscraper |
| 图像处理 | Pillow + 百度 AI 人脸检测 |
| 包管理 | uv workspace（4 个成员包） |

## 模块划分

```
core/           纯业务逻辑（零 Qt 依赖）
pyside6_gui/    PySide6 + QML 界面（主力前端）
pyqt5-gui/      PyQt5 界面（遗留）
cli/            命令行工具
tui-go/         Go TUI
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

### 核心模块（`core/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [core/01-requirements.md](core/01-requirements.md) | 核心 I/O 黑盒规范 |
| 02 | [core/02-scraping-flow.md](core/02-scraping-flow.md) | 抓取流程、Pipeline、Scraper Chain |

### PySide6 GUI（`pyside6gui/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [pyside6gui/01-qml-ui-design.md](pyside6gui/01-qml-ui-design.md) | QML 组件规范、布局模式、Theme |
| 02 | [pyside6gui/02-dynamic-property.md](pyside6gui/02-dynamic-property.md) | 动态 Property 踩坑与类工厂解法 |

### 工具链（`tooling/`）

| # | 文档 | 内容 |
|---|------|------|
| 01 | [tooling/01-codegraph.md](tooling/01-codegraph.md) | CodeGraph 代码智能工具使用指南 |
