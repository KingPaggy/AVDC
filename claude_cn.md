# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概览

AVDC (AV Data Capture) 是一个基于 Python 的 GUI 应用程序，用于从日本成人视频 (JAV) 网站抓取元数据，并整理本地视频文件以便与 Emby、Kodi 和 Plex 等媒体服务器集成。

**核心技术**: Python 3.8+, PyQt5, lxml/BeautifulSoup4 (HTML 解析), requests/cloudscraper (HTTP 与 Cloudflare 绕过), Pillow (图像处理), Baidu AI (图像识别)

## 常用命令

### 开发环境设置
```bash
# 使用 pip 安装依赖
pip install -r py-require.txt

# 或使用 uv (现代 Python 包管理器)
uv sync

# 运行主应用程序
python AVDC_Main_new.py
```

### UI 开发
- Qt Designer 文件 (`*.ui`) 使用 `pyuic5-tool` 编译为 Python
- 编译后的 UI 位于 `Ui/AVDC_new.py`

### 配置
- 主配置文件: `config.ini` (必须与可执行文件在同一目录)
- 当 `save_log = 1` 时，日志文件保存到 `Log/` 目录

## 架构概览

### 层次结构
```
AVDC_Page/
├── AVDC_Main_new.py    # 主应用程序入口点 (UI + 业务逻辑混合)
├── Ui/
│   └── AVDC_new.py     # 编译后的 PyQt5 UI 布局
├── Function/
│   ├── Function.py     # 核心调度逻辑、文件操作、工具函数
│   └── getHtml.py      # HTTP 请求处理，支持代理/重试
└── Getter/
    ├── javbus.py       # javbus.com 抓取器
    ├── javdb.py        # javdb.com 抓取器
    ├── jav321.py       # jav321.com 抓取器
    ├── avsox.py        # avsox.com 抓取器
    ├── dmm.py          # dmm.co.jp 抓取器 (需要日本代理)
    ├── mgstage.py      # mgstage.com 抓取器
    └── xcity.py        # xcity.jp 抓取器
```

### 核心组件

**抓取器架构** (Getter 模块):
- 每个抓取器都有一个 `main(number, appoint_url, isuncensored=False)` 函数
- 返回 JSON 字符串，包含元数据字段: title, actor, studio, publisher, outline, score, runtime, director, release, number, cover, extrafanart, tag, series, year, actor_photo, website, source
- Cloudflare 绕过通过 `cloudscraper` 处理 (用于 `get_html_javdb()`)
- DMM 需要日本代理才能正常工作

**调度逻辑** (`Function/Function.py`):
- `getDataFromJSON(file_number, config, mode, appoint_url)`: 主抓取器调度器
- `mode` 参数决定尝试哪些抓取器:
  - `1`: 所有抓取器 (默认)
  - `2`: 仅 mgstage
  - `3`: 仅 javbus
  - `4`: 仅 jav321
  - `5`: 仅 javdb
  - `6`: 仅 avsox
  - `7`: 仅 xcity
  - `8`: 仅 dmm
- 抓取器按顺序尝试，使用第一个成功的结果

**番号模式检测**:
- 无码: `^\d{4,}` (例如 `111111-1111`), `n\d{4}`, `HEYZO-*` 以及配置中的自定义前缀
- FC2: `FC2-\d{5,}`
- 欧美: `\D+\.\d{2}\.\d{2}\.\d{2}` (例如 `sexart.19.11.03`)
- 标准有码: `SSIS-123`, `ABP-456`
- 混合: `259LUXU-1111` (mgstage)

**HTTP 处理** (`Function/getHtml.py`):
- `get_html(url, cookies)`: 标准 GET 请求，支持代理和重试
- `get_html_javdb(url)`: 使用 cloudscraper 绕过 Cloudflare
- `post_html(url, query)`: POST 请求支持
- 代理设置从 `config.ini` 的 [proxy] 部分读取

## 重要文件模式

### 番号命名约定 (抓取关键)
- 标准有码: `SSNI-111`, `IPX-123`, `ABP-456`
- 无码: `111111-1111`, `111111_1111`, `HEYZO-1111`, `n1111`
- FC2: `FC2-111111`, `FC2-PPV-111111`
- Mgstage/素人: `259LUXU-1111`, `SIRO-1234`
- 欧美: `sexart.19.11.03` (系列.年.月.日)

### 文件命名支持
- 多碟片: `ssni-xxx-cd1.mp4`, `ssni-xxx-cd2.mp4`
- 带字幕: `ssni-xxx-c.mp4`, `ssni-xxx-C.mp4`
- 组合: `abp-xxx-CD1-C.mp4` (碟片在前，字幕在后)

## 配置系统 (config.ini)

### 配置段
- `[common]`: main_mode, 输出文件夹, 网站选择, 软链接模式
- `[proxy]`: 类型 (no/http/socks5), 代理地址, 超时, 重试次数
- `[Name_Rule]`: folder_name, naming_media, naming_file 模式
- `[media]`: media_type 扩展名, sub_type 扩展名, media_path
- `[escape]`: 字面量, 文件夹, 需要排除的字符串
- `[debug_mode]`: 调试输出开关
- `[emby]`: emby_url, 演员照片上传的 api_key
- `[mark]`: 水印设置 (poster_mark, thumb_mark, mark_size, mark_type, mark_pos)
- `[uncensored]`: uncensored_prefix, uncensored_poster (0=官方, 1=裁剪)
- `[file_download]`: nfo, poster, fanart, thumb 下载开关
- `[extrafanart]`: extrafanart_download, extrafanart_folder

## 已知问题和架构说明

**当前架构限制** (来自 `dev-log/修改意见.md`):
- `AVDC_Main_new.py` 是一个"上帝类"，混合了 UI、业务逻辑和文件操作
- 抓取器没有统一接口 (都返回 JSON 字典但没有约定)
- `Function.py` 中的抓取器调度逻辑硬编码 - 添加新站点需要修改多个文件
- 数据以原始字典而不是类型化类流动，维护困难
- UI 和逻辑紧密耦合

**代理需求**:
- DMM 需要日本代理才能访问内容
- JavDB 可能在约 30 次请求后封禁 IP - 使用代理或切换站点
- Cloudflare 保护通过 `cloudscraper` 库处理

## 添加新的抓取站点

添加新的抓取网站:

1. 在 `Getter/` 目录中创建新文件 (例如 `newsite.py`)
2. 实现返回 JSON 的 `main(number, appoint_url, isuncensored=False)` 函数
3. 在 `Function/Function.py` 中导入它
4. 在 `getDataFromJSON()` 函数中添加调度逻辑
5. 更新 `config.ini` 的网站选项注释和 `AVDC_Main_new.py` 中的 UI 下拉菜单

## 番号提取逻辑 (`getNumber()`)

`Function/Function.py` 中的 `getNumber()` 函数处理复杂的模式匹配以从文件名中提取视频番号。它处理:
- 从配置中移除转义字符串
- 提取多碟片的 `-CDn` 或 `-cdn` (从主番号中移除)
- 处理日期模式 `\d{4}-\d{1,2}-\d{1,2}`
- 支持多种连字符/下划线格式

## 文件处理工作流

1. `movie_lists()` 扫描目录查找匹配扩展名的视频文件
2. 对于每个文件: `getNumber()` 提取视频 ID
3. `getDataFromJSON()` 根据番号模式调度到相应的抓取器
4. 如果成功: 下载元数据，重命名/移动到输出目录
5. 如果失败 (且 `failed_file_move = 1`): 移动到失败目录

## 测试抓取器更改

修改抓取器时:
- 使用每个支持站点的真实番号示例进行测试
- 验证 JSON 输出包含所有必需字段
- 检查 Cloudflare 绕过仍然有效 (对于 javdb)
- 测试有码和无码内容
- 验证图像 URL 格式正确
