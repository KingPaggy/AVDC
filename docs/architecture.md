# AVDC 整体架构概览

## 项目定位

AVDC（AV Data Capture）是一个 Python 桌面 GUI 应用，用于抓取 JAV 网站元数据并组织本地视频文件，供 Emby/Kodi/Plex 等媒体服务器使用。

**技术栈**：PyQt5（GUI）、lxml/BeautifulSoup4（HTML 解析）、requests/cloudscraper（HTTP）、Pillow（图像处理）、Baidu AIP（人脸检测）。

**Python 版本**：3.13（见 `.python-version`）

## 分层架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        UI 层 (Qt)                                │
│  main.py           ── QMainWindow, QTreeWidget, QProgressBar    │
│  ui/main_window.py ── Qt Designer 编译后的 UI 代码              │
│  cli.py            ── 独立 CLI 入口（无 Qt 依赖）               │
└───────────────────────────┬──────────────────────────────────────┘
                            │ AppConfig + 回调函数
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    内核层 CoreEngine (零 Qt)                      │
│  core/_services/orchestrator.py                                  │
│  process_batch() / process_single() → 刮削/整理流程编排          │
│  回调：on_log, on_progress, on_success, on_failure               │
└──────┬───────────┬──────────────┬───────────────┬────────────────┘
       │           │              │               │
       ▼           ▼              ▼               ▼
   文件扫描    番号提取       刮削管道        文件操作
   file_utils  file_utils   scrape_pipeline  file_operations
       │           │              │               │
       ▼           ▼              ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│                        刮削层                                    │
│  core/_scraper/  ── 基础设施（基类、注册表、调度器、管道）        │
│  core/_scraper/scrapers/  ── 7 个站点实现（javbus/javdb/...）   │
└──────────────────────────────────────────────────────────────────┘
```

## 核心设计原则

**UI 与业务逻辑完全解耦**。`CoreEngine` 不接受任何 Qt 对象，仅通过 `AppConfig` dataclass 获取配置、通过回调函数报告状态。这使得：

- 同一套核心逻辑可同时服务于 GUI（`main.py`）和 CLI（`cli.py`）
- 核心模块可在无显示器/无 Qt 环境的服务器上运行
- 测试时无需初始化 Qt 事件循环

## 入口点

| 入口 | 文件 | 说明 |
|------|------|------|
| GUI | `main.py` | PyQt5 窗口应用，`if __name__ == "__main__"` 启动 |
| CLI | `cli.py` | 无 Qt 依赖的命令行工具，支持 `--path`、`--single`、`--mode` 等参数 |

```bash
uv run python main.py                     # 启动 GUI
uv run python cli.py --path /path/to/movies # 批量刮削
uv run python cli.py --single movie.mp4 --number ABC-123  # 单文件刮削
```

## 配置系统

配置文件 `config.ini` 包含 17 个 section（common、proxy、Name_Rule、update、log、media、escape、debug_mode、emby、mark、uncensored、file_download、extrafanart、baidu 等）。

配置流经三层：

```
config.ini (磁盘)
    │
    ▼
AppConfig dataclass (core/_config/config.py)
    │  ←  _get_app_config() 从 UI 控件读取
    ▼
CoreEngine 接收 config 参数
    │
    ▼
core/ 下各子模块通过 config.field_name 读取配置
```

`AppConfig` 是核心配置中继 —— UI 层通过 `from_ini()` / `to_ini()` 读写磁盘，通过 `_get_app_config()` 从控件状态构建实例。核心业务模块只依赖 `AppConfig` 字段，**永不直接访问 `self.Ui.*`**。

## 包结构

```
core/
  _config/      AppConfig 配置、config_io 读写、logger 日志、errors 异常
  _models/      Movie / Actor / ProcessResult / ScraperResult 数据类
  _scraper/     刮削基础设施：ScraperBase 基类、ScraperRegistry 注册表、
                ScraperDispatcher 调度器、scrape_pipeline 管道、scraper_adapter 缓存
  _services/    CoreEngine 编排器、metadata 元数据、naming_service 命名、emby_client
  _files/       file_utils（文件扫描、番号提取）、file_operations（下载/NFO/移动）
  _media/       image_processing（水印叠加、海报裁剪、人脸检测）
  _net/         networking（get_html、get_html_javdb、post_html，含代理/重试）
  _event/       EventBus（线程安全 pub/sub）、Event / EventType 枚举
  scrapers/     7 个站点实现：avsox, dmm, jav321, javbus, javdb, mgstage, xcity
```

导入规范：始终使用完整的子包路径，如 `from core._config.config import AppConfig`。

## 数据模型

**Movie**（`core/_models/models.py`）：核心数据类，包含 title、number、actor、studio、publisher、director、release、year、runtime、score、outline、cover、cover_small、extrafanart、tag、series、actor_photo、website、source、imagecut 等字段。

**ProcessResult**（`core/_models/process_result.py`）：处理结果，含 ProcessStatus 枚举（SUCCESS / FAILED_NOT_FOUND / FAILED_TIMEOUT / FAILED_ERROR）。

**Event**（`core/_event/events.py`）：事件总线数据载体，包含 20+ 种 EventType，用于核心服务与 UI 间的解耦通信。
