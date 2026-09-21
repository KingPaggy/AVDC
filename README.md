# AVDC

**AV Data Capture** — 自动抓取 JAV 元数据并整理本地视频文件的桌面工具，输出供 Emby / Kodi / Plex 等媒体库使用。

![](https://img.shields.io/badge/Python-3.13-yellow.svg?style=flat-square&logo=python)
![](https://img.shields.io/badge/GUI-macOS%20SwiftUI-blue.svg?style=flat-square)
![](https://img.shields.io/badge/TUI-Go%20%2B%20gocui-cyan.svg?style=flat-square)
![](https://img.shields.io/github/license/pageking/avdc_page.svg?style=flat-square)

---

## 目录

- [主要功能](#主要功能)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [番号命名规范](#番号命名规范)
- [配置说明](#配置说明)
- [异常处理](#异常处理)
- [FAQ](#faq)
- [申明](#申明)

---

## 主要功能

- **元数据抓取** — 从 jav321、javbus、javdb、avsox、dmm、mgstage、xcity 等站点批量抓取影片元数据（封面、演员、简介、类型等）
- **视频整理** — 自动按演员/番号分类归档，支持多集（-cd1/-cd2）、字幕（-C）识别
- **多前端** — macOS 原生 GUI（SwiftUI）、Go TUI 终端界面、CLI 命令行
- **水印系统** — 封面/缩略图可添加无码、字幕、流出水印
- **Emby 集成** — 批量添加演员头像，元数据直接导入媒体库
- **子目录遍历** — 递归扫描视频目录及子目录，支持排除指定目录

---

## 项目结构

```
AVDC_Page/
├── core/               # 核心业务逻辑（零 Qt 依赖）
│   ├── _config/        #   配置管理、日志
│   ├── _models/        #   数据模型（Movie, Actor, ProcessResult）
│   ├── _scraper/       #   7 个站点爬虫 + 调度管线
│   ├── _services/      #   编排引擎、Emby 客户端、命名服务
│   ├── _files/         #   文件操作与工具
│   ├── _media/         #   图片处理、水印
│   ├── _net/           #   网络请求
│   ├── _event/         #   事件总线
│   └── test/           #   单元测试 + 集成测试 + 实时测试
├── mac-gui/            # macOS 原生 GUI（主力，纯 SwiftUI）
│   ├── Sources/        #   AVDCAppCore（Bridge/AppModel/SettingsState）
│   │                   #   + AVDCApp 视图（Home/Settings/Tools/Log/About）
│   ├── Tests/          #   Swift Testing（mock CLI 离线）
│   └── Package.swift   #   SPM 包定义
├── cli/                # CLI 命令行前端
│   └── test/           #   CLI 测试
├── tui-go/             # Go TUI 终端界面（gocui）
│   └── pkg/            #   Go 包（gui, python bridge, controllers）
├── .archive/           # 已归档 GUI（PySide6/PyQt5，2026-09-20）
├── docs/               # 技术文档
├── resources/          # 图标资源
├── config.ini          # 共享配置文件
└── pyproject.toml      # uv workspace 根配置
```

`core/`、`cli/` 两个 Python 包通过 **uv workspace** 管理。mac-gui
为纯 SwiftUI（SPM），通过子进程调用 `cli.py --json-output`，以
JSONL 协议通信；Go TUI 亦通过子进程调用 Python CLI。

---

## 快速开始

### 环境要求

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)（推荐）或 pip
- Xcode Command Line Tools（构建 mac-gui 需要）
- Go 1.26+（仅编译 TUI 时需要）

### 安装依赖

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目所有依赖
uv sync
```

### 运行

```bash
# macOS 原生 GUI（推荐，纯 SwiftUI）
cd mac-gui && swift build
./mac-gui/.build/debug/AVDCApp  # 需在项目根目录运行

# CLI 命令行
uv run python cli/cli.py --path /path/to/movies
uv run python cli/cli.py --path /path/to/movies --main-mode organize --site javbus

# Go TUI（需先编译）
cd tui-go && make build && ./avdc-tui
```

### 测试

```bash
# 核心 + CLI 测试
uv run pytest core/test cli/test/ -v

# mac-gui 测试（Swift Testing，mock CLI 离线）
cd mac-gui && swift test

# Go TUI 测试
cd tui-go && make test
```

---

## 番号命名规范

**刮削前请尽量命名规范，不区分大小写。**

### 标准有码

| 站点 | 格式示例 |
|------|----------|
| javdb / javbus / jav321 | `SSNI-111` |
| dmm | `ssni00111` |

### 无码

| 站点 | 格式示例 |
|------|----------|
| javdb / javbus / avsox | `111111-1111`、`111111_111`、`HEYZO-1111`、`n1111` |
| jav321 | `HEYZO-1111` |

### 素人

| 站点 | 格式示例 |
|------|----------|
| jav321 / mgstage | `259LUXU-1111` |
| jav321 / javdb | `LUXU-1111` |
| fc2club | `FC2-111111`、`FC2-PPV-111111` |

### 欧美

| 站点 | 格式示例 |
|------|----------|
| javdb / javbus | `sexart.11.11.11`（系列.年.月.日） |

### 特殊标记

- **字幕影片** — `ssni-xxx-c.mp4`、`abp-xxx-CD1-C.mp4`（分集在前，字幕在后）
- **多集影片** — `ssni-xxx-cd1.mp4`、`ssni-xxx-cd2.mp4`（含 `-CDn` 即自动识别分集）
- **外挂字幕** — 字幕文件名须与影片文件名一致（支持 srt/ass/sub）
- **流出影片** — 文件名包含"流出"即可

---

## 配置说明

配置文件为项目根目录的 `config.ini`，主要分区如下：

### 普通设置

| 配置项 | 说明 |
|--------|------|
| 模式 | **刮削模式**（元数据+封面+缩略图+背景图）/ **整理模式**（仅按演员分类重命名） |
| 软链接模式 | 刮削完不移动视频，创建软链接（需管理员权限） |
| 调试模式 | 输出元数据调试信息 |
| 失败后移动 | 刮削失败的视频自动移至失败输出目录 |
| 网站选择 | 全部站点或指定站点（jav321/javbus/javdb/avsox/dmm/mgstage/xcity） |

### 目录设置

| 配置项 | 说明 |
|--------|------|
| 命名规则 | 目录命名 / 媒体库标题 / 本地文件名，支持 `actor`、`number`、`title`、`studio` 等变量 |
| 视频目录 | 要扫描的视频根目录（递归遍历） |
| 排除目录 | 不扫描的目录 |
| 成功输出目录 | 刮削成功的输出位置（默认 `JAV_output`） |
| 失败输出目录 | 刮削失败的输出位置（默认 `failed`） |

### 代理设置

| 配置项 | 说明 |
|--------|------|
| 代理地址 | 本地代理，如 `127.0.0.1:7890` |
| 超时 | 连接超时秒数（3-10） |
| 重试次数 | 失败重试次数（2-5） |

> **注意**：DMM 站点需要日本代理。JavDB 频繁请求会被封 IP。

### 水印设置

支持在封面图/缩略图上添加无码、字幕、流出水印，可设置位置（左上/左下/右上/右下）、大小、顺序。水印文件要求 500x300、背景透明、PNG 格式。

### Emby 集成

填写 Emby 服务器地址和 API Key，可批量添加演员头像。头像文件放在程序目录的 `Actor/` 下。

---

## 异常处理

### 网络错误

出现 `Connect Failed`、`Updata_check`、`JSON` 相关错误时：
1. 检查代理设置，确认代理软件已开启全局模式
2. DMM 站点需确认使用日本代理
3. 尝试清除代理地址后重试

### 番号提取失败

1. 检查文件命名是否符合[番号命名规范](#番号命名规范)
2. 使用 CLI 的单文件刮削模式，指定网站重试
3. 确认番号在目标站点可查到

### PLEX 不显示封面

安装插件 [XBMCnfoMoviesImporter](https://github.com/gboudreau/XBMCnfoMoviesImporter.bundle)。

---

## FAQ

**Q: 这软件能下片吗？**
A: 不能。仅提供本地影片分类整理功能。

**Q: 什么是元数据？**
A: 影片的封面、导演、演员、简介、类型等信息。

**Q: 软件收费吗？**
A: 永久免费。

**Q: 支持 NAS 吗？**
A: 支持。群晖等 NAS 开启 SMB 后在 Windows 映射为本地磁盘即可使用。

---

## 申明

当你查阅、下载了本项目源代码或二进制程序，即代表你接受了以下条款：

- 本软件仅供技术交流、学术交流使用
- **请勿在热门的社交平台上宣传此项目**
- 本软件作者编写出该软件旨在学习 Python，提高编程水平
- 本软件不提供任何影片下载的线索
- 用户在使用本软件前，请了解并遵守当地法律法规
- 用户在使用本软件时，若产生一切违法行为由用户承担
- 严禁将本软件使用于商业和个人其他意图
- 源代码和二进制程序请在下载后 24 小时内删除
- 若不同意上述条款，请勿使用本软件

---

> 基于 [yoshiko2/AV_Data_Capture](https://github.com/yoshiko2/AV_Data_Capture)（原作者）开发，感谢原作者的贡献。
