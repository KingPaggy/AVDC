# 刮削流程详解

本文档描述 AVDC 从扫描视频文件到生成完整媒体包的完整流程。

## 完整流程链路

```
视频文件 ──▶ movie_lists() ──▶ getNumber() ──▶ getDataFromJSON()
   │              │                 │                  │
   │              │                 │                  ├── ScraperDispatcher.get_scraper_chain()
   │              │                 │                  │         ▼
   │              │                 │                  │   选择刮削器链
   │              │                 │                  │         ▼
   │              │                 │                  │   _execute_chain() 顺序/并发执行
   │              │                 │                  │         ▼
   │              │                 │                  │   返回 Movie 对象
   │              │                 │                  │
   ▼              ▼                 ▼                  ▼
 CoreEngine._process_single_core() ──▶ 文件操作（下载/裁剪/移动/NFO/水印）
```

## 1. 文件扫描 — `movie_lists()`

**文件**：[core/_files/file_utils.py](core/_files/file_utils.py)

```python
def movie_lists(escape_folder: str, movie_type: str, movie_path: str) -> list[str]
```

- 使用 `os.walk()` 递归遍历 `movie_path` 目录树
- 跳过 `escape_folder` 中指定的文件夹（逗号分隔，如 `failed,JAV_output`）
- 按 `movie_type` 过滤扩展名（管道分隔：`.mp4|.avi|.rmvb|.wmv|.mov|.mkv`）
- 跳过隐藏文件（以 `.` 开头）
- 返回匹配的视频文件路径列表

## 2. 番号提取 — `getNumber()`

**文件**：[core/_files/file_utils.py](core/_files/file_utils.py)

```python
def getNumber(filepath: str, escape_string: str) -> str
```

从文件名中提取 JAV 番号的流程：

1. **清理后缀**：去除 `-C.` / `-c.`（中文字幕标记）、`-CD\d+`（分片标记）
2. **去除日期模式**：如 `-2024-01-15`
3. **去除 escape_string**：配置的干扰字符串
4. **正则匹配**（按优先级）：

| 优先级 | 正则模式 | 示例 |
|--------|----------|------|
| 1 | `\D+\.\d{2}\.\d{2}\.\d{2}` | `SexArt.22.12.25` |
| 2 | `XXX-AV-\d{4,}` | `XXX-AV-12345` |
| 3 | `FC2-\d{5,}` | `FC2-123456` |
| 4 | `\d+[a-zA-Z]+-\d+` | `10musume-123` |
| 5 | `[a-zA-Z]+-\d+` | `SSIS-123` |
| 6 | `[a-zA-Z]+-[a-zA-Z]\d+` | `ABC-A123` |
| 7 | `\d+-[a-zA-Z]+` | `123-ABC` |
| 8 | `\d+-\d+` | `111111-111` |
| 9 | `\d+_\d+` | `111_222` |

5. **兜底**：将字母前缀与数字后缀组合

## 3. 刮削器选择 — `ScraperDispatcher`

**文件**：[core/_scraper/scraper_dispatcher.py](core/_scraper/scraper_dispatcher.py)

### 模式识别

`ScraperDispatcher` 通过 5 个静态方法识别番号模式：

| 方法 | 正则/条件 | 匹配示例 |
|------|-----------|----------|
| `is_uncensored()` | `^\d{4,}` / `n\d{4}` / `HEYZO` | `111111-111`, `n1234`, `HEYZO-1234` |
| `is_fc2()` | 包含 `FC2` | `FC2-123456` |
| `is_mgstage()` | `\d+[a-zA-Z]+-\d+` / `SIRO` | `259LUXU-111`, `SIRO-1234` |
| `is_dmm_style()` | `\D{2,}00\d{3,}` 且无 `-` `_` | `ssni00111` |
| `is_european()` | `\D+\.\d{2}\.\d{2}\.\d{2}` | `sexart.19.11.03` |

### 自动模式刮削器链

`_get_auto_chain()` 根据识别结果返回有序刮削器链（优先级数字越小越先执行）：

| 模式 | 刮削器链 |
|------|----------|
| 无码 | javbus_uncensored → javdb → jav321 → avsox |
| FC2 | javdb |
| MGStage | mgstage → jav321 → javdb → javbus |
| DMM 风格 | dmm |
| 欧洲 | javdb_us → javbus_us |
| 默认（有码） | javbus → jav321 → xcity → javdb → avsox |

### 手动模式

用户可通过 UI 下拉框选择特定站点（mode 2-8）：

| mode | 站点 |
|------|------|
| 2 | mgstage |
| 3 | javbus |
| 4 | jav321 |
| 5 | javdb |
| 6 | avsox |
| 7 | xcity |
| 8 | dmm |

### 刮削器注册发现

每个刮削器模块使用 `@register_scraper` 装饰器自动注册到 `ScraperRegistry`，由 `ScraperDispatcher` 通过 `SCRAPER_MAPPING` 调度。

## 4. 刮削执行 — `getDataFromJSON()`

**文件**：[core/_scraper/scrape_pipeline.py](core/_scraper/scrape_pipeline.py)

```python
def getDataFromJSON(file_number, config, mode, appoint_url) -> dict
```

### 执行步骤

1. **懒加载刮削器模块**：`get_scraper_modules()` 首次调用时导入 7 个站点模块
2. **判断是否无码**：`is_uncensored(file_number)` 辅助判断
3. **获取刮削器链**：委托 `ScraperDispatcher.get_scraper_chain(file_number, mode)`
4. **执行链**：`_execute_chain()` 支持两种模式：
   - **顺序执行**（默认，`max_concurrent=1`）：逐个尝试，首个成功即返回
   - **并发执行**（`max_concurrent=2-5`）：用 `ThreadPoolExecutor` 分批并发，按优先级顺序检查结果
5. **缓存机制**：每个 `(scraper, number)` 对缓存结果，避免重复请求
6. **数据转换**：`_to_movie()` 将原始 JSON 转为 `Movie` 对象，清理非法字符、格式化日期、补充默认演员
7. **字段展平**：将 actor 列表转为逗号分隔字符串，供旧版兼容

### 刮削器站点角色

| 刮削器 | 角色 | 特殊要求 |
|--------|------|----------|
| javbus | 主刮（有码+无码） | 需处理 Cloudflare |
| javdb | 主刮（FC2） | 使用 cloudscraper 绕过 CF，IP 有请求限制 |
| jav321 | 备用 | 支持 isuncensored 参数 |
| avsox | 备用 | — |
| dmm | DMM 专用 | **需要日本代理** |
| mgstage | MGStage/amateur 主刮 | 首次调用后会规范化番号 |
| xcity | 备用 | — |

## 5. 数据验证

`_process_single_core()` 在收到 JSON 数据后进行 4 项验证：

1. **网站超时**：`json_data["website"] == "timeout"` → 标记失败
2. **标题缺失**：无 title 字段 → 标记失败
3. **封面 URL 缺失**：cover 不含 `http` → 异常
4. **无码封面**：`imagecut == 3` 时 cover_small 必须存在 → 异常

## 6. 后缀检测

处理文件名中的特殊标记：

| 标记 | 检测条件 | 效果 |
|------|----------|------|
| 分片 | 文件名含 `-CD` 或 `-cd` | 提取 CD 编号（CD1, CD2...） |
| 中文字幕 | 含 `-c.` / `-C.` / `中文` / `字幕` | 文件名追加 `-C` |
| 无码 | `imagecut == 3` | 触发特殊海报裁剪 |
| 流出 | 文件名含 `流出` | 文件名追加 `-流出` |

## 7. 文件操作

### 7.1 目录创建

`create_output_folder()` 根据配置的命名规则（`actor/number-title-release` 等）创建输出目录。

### 7.2 图片处理

| 操作 | 函数 | 说明 |
|------|------|------|
| 下载缩略图 | `download_thumb()` | 从 cover URL 下载 `-thumb.jpg` |
| 下载小图 | `download_small_cover()` | 下载 `-poster.jpg`（小尺寸） |
| 裁剪海报 | `cut_poster_from_thumb()` | 通过 Baidu AI 人脸检测智能裁剪，或按 imagecut 模式裁剪 |
| 修复尺寸 | `fix_image_size()` | 调整图片到标准尺寸 |
| 水印叠加 | `apply_marks()` | 在 corner 位置叠加 SUB/LEAK/UNCENSORED 水印 |

### 7.3 媒体组织

| 操作 | 函数 | 说明 |
|------|------|------|
| 移动文件 | `paste_file_to_folder()` | 将源视频移动到输出目录，附带同名子文件 |
| 写入 NFO | `write_nfo()` | 生成 Kodi/Emby/Jellyfin 兼容的 NFO 元数据文件 |
| 下载特典 | `download_extrafanart()` | 下载额外剧照到 `extrafanart/` 子目录 |
| 清理缩略图 | `delete_thumb()` | 按配置决定是否保留 `-thumb.jpg` |
| 清理空目录 | `clean_empty_dirs()` | 批量处理结束后清理空文件夹 |

## 8. 失败处理

处理失败的文件会根据 `config.failed_file_move` 配置移动到 `failed/` 目录。失败原因通过 `on_failure(filepath, reason, error)` 回调通知 UI。

## 批量 vs 单文件

| | `process_batch()` | `process_single()` |
|---|---|---|
| 输入 | 目录路径 | 文件路径 + 番号 |
| 循环 | 是（遍历目录） | 否 |
| 返回 | `{total, success, failed}` | 后缀字符串或 `"not found"` / `"error"` |
| 错误策略 | 单文件失败继续处理下一个 | 单文件失败直接返回 |
| 空目录清理 | 是 | 否 |
