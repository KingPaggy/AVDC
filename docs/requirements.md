# AVDC 核心需求规格

> 将内核视为黑盒。定义它应该接收什么、产出什么。

---

## 一、输入

### 1. 单个视频文件

```
输入：文件路径
  /videos/SSIS-487.mp4
  /videos/FC2-PPV-1234567.mkv
  /videos/111111-1111-C-CD1.avi
```

黑盒自动从文件名中提取番号（处理多碟、字幕标记、转义字符串等）。

### 2. 直接给定番号

```
输入：番号 + 可选指定网站
  SSIS-487           → 全站点自动匹配
  FC2-1234567        → 全站点自动匹配
  HEYZO-3032         → 全站点自动匹配
  SSIS-487 | javbus  → 只从 javbus 抓取
  259LUXU-504 | all  → 全站点尝试
```

### 3. 批量目录扫描

```
输入：目录路径 + 配置
  /videos/JAV/        → 递归扫描所有媒体文件
  /videos/JAV/        → 排除 .skip/ 目录
  /videos/JAV/        → 排除文件名中含 "sample" 的文件
```

### 4. 配置项（影响行为的核心参数）

| 参数 | 作用 |
|------|------|
| `main_mode` | 1=全抓取, 2-8=指定站点 |
| `website` | 默认目标站点 |
| `proxy` | 代理地址（DMM/JavDB 需要） |
| `timeout` / `retry` | 网络超时和重试次数 |
| `naming_file` | 输出文件名模板 |
| `naming_media` | NFO 内媒体名模板 |
| `folder_name` | 输出文件夹模板 |
| `media_type` | 识别的文件扩展名 |
| `soft_link` | 软链接还是移动文件 |
| `failed_file_move` | 失败是否移入失败目录 |
| `poster_mark` / `thumb_mark` | 是否加水印 |
| `mark_type` | 水印类型：SUB/LEAK/UNCENSORED |
| `nfo_download` / `poster_download` / `thumb_download` / `fanart_download` | 各类文件下载开关 |
| `uncensored_poster` | 无码海报：0=官方 1=裁剪 |

---

## 二、输出

### 1. 元数据（JSON / NFO）

每个视频被抓取后，产出以下结构化信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| `number` | 番号 | `SSIS-487` |
| `title` | 标题 | `こんな綺麗なお姉さんが...楓ふうあ` |
| `actor` | 演员列表 | `楓ふうあ,安齋らら` |
| `studio` | 制作商 | `S1 NO.1 STYLE` |
| `publisher` | 发行商 | `S1 NO.1 STYLE` |
| `director` | 导演 | `キョウセイ` |
| `release` | 发行日期 | `2022-08-09` |
| `year` | 年份 | `2022` |
| `runtime` | 时长（分钟） | `210` |
| `score` | 评分 | `4.5` |
| `outline` | 简介/剧情描述 | `いまどき韓国系の美女で...` |
| `tag` | 标签列表 | `巨乳,騎乗位,痴女` |
| `series` | 系列名 | `S1 NO.1 STYLE` |
| `cover` | 封面大图 URL | `http://pics.dmm.co.jp/.../pb_e_...jpg` |
| `cover_small` | 小封面 URL | `http://pics.dmm.co.jp/.../pl.jpg` |
| `actor_photo` | 演员头像 | `{"楓ふうあ": "https://...", ...}` |
| `extrafanart` | 剧照列表 | `["https://...", ...]` |
| `website` | 数据来源站点 | `jav321` |
| `source` | 来源脚本 | `jav321.py` |
| `imagecut` | 海报裁剪模式 | `1`（有码）/ `3`（无码） |

### 2. NFO 文件（Kodi/Emby/Jellyfin 兼容）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<movie>
  <title>标题</title>
  <originaltitle>原标题</originaltitle>
  <sorttitle>排序标题</sorttitle>
  <set>系列</set>
  <studio>制作商</studio>
  <publisher>发行商</publisher>
  <director>导演</director>
  <premiered>2022-08-09</premiered>
  <release>2022-08-09</release>
  <plot>简介</plot>
  <runtime>210</runtime>
  <number>SSIS-487</number>
  <cover>封面URL</cover>
  <website>来源站点</website>
  <actor>
    <name>楓ふうあ</name>
  </actor>
  <genre>巨乳</genre>
  <genre>騎乗位</genre>
</movie>
```

### 3. 图片文件

| 文件 | 说明 |
|------|------|
| `{番号}-poster.jpg` | 海报（竖版，2:3 比例） |
| `{番号}-thumb.jpg` | 缩略图（横版） |
| `{番号}-fanart.jpg` | 同人图/背景图（通常等于 thumb） |
| `extrafanart/fanart1.jpg` | 额外剧照（可选） |

### 4. 文件组织（输出目录结构）

```
成功输出：
  {output}/
    actor/
      number-title-release/
        number-title.mp4          ← 重命名后的视频
        number-title.nfo          ← 元数据
        number-title-poster.jpg   ← 海报
        number-title-thumb.jpg    ← 缩略图
        number-title-fanart.jpg   ← 背景图
        number-title.srt          ← 字幕（如有）

失败输出：
  {output}/
    failed/
      SSIS-487.mp4                ← 无法匹配的视频
```

多碟文件：
```
  SSIS-487-CD1.mp4
  SSIS-487-CD2.mp4
  SSIS-487-CD1-C.mp4              ← 含中文字幕
```

---

## 三、核心流程（黑盒内部逻辑）

```
输入文件 ──→ 提取番号 ──→ 识别类型 ──→ 选择站点链 ──→ 抓取数据
                                                    ↓
                                              数据有效？
                                                 ↙    ↘
                                              是        否
                                              ↓         ↓
                                         生成输出    移入失败目录
                                              ↓
                                     下载图片 / 生成NFO
                                              ↓
                                     裁剪海报 / 加水印
                                              ↓
                                     重命名 + 移动文件
                                              ↓
                                          返回结果
```

### 站点选择规则（mode=1 全自动）

| 番号类型 | 抓取顺序 |
|----------|----------|
| 有码标准 `SSIS-123` | javbus → jav321 → xcity → javdb → avsox |
| 无码 `HEYZO-3032` | javbus.uc → javdb → jav321.uc → avsox |
| FC2 `FC2-123456` | javdb |
| MGS混合 `259LUXU-504` | mgstage → jav321 → javdb → javbus |
| DMM风格 `abcd00123` | dmm |
| 欧洲风格 `sexart.19.11.03` | javdb.us → javbus.us |

### 成功判定

- `title` 非空、非 "None"、非 "null" → 成功
- 任意字段缺失但有 title → 仍算成功
- 所有站点均失败 / title 为空 → 失败

---

## 四、期望效果总结

**一句话描述：**

> 输入一个视频文件或番号，自动获取该作品的完整元数据，下载海报和剧照，生成 NFO 文件，并按命名规则重命名、整理到输出目录。

**输入：** 文件路径 或 番号
**输出：** 整理好的文件夹（含视频 + 元数据 + 图片 + NFO）
