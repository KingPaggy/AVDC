# AVDC macOS GUI 迁移方案

> 目标：用 14-MacApp-C-Cpp 的四层架构（C++ 核心 + ObjC++
> 薄壳 + ImGui/Metal 自绘 + SwiftUI 原生玻璃）替换 PySide6
> 主力 GUI。
> 状态：调研完成，待评审
> created: 2026-09-20

## 1. 调研结论

### 1.1 AVDC 现状

- Python 3.13 + uv workspace，四包：`core/`、`cli/`、
  `pyqt5-gui/`（遗留）、`pyside6_gui/`（主力）
- `core/`：64 个 .py，约 3450 行——7 站点爬虫（jav321/
  javbus/javdb/avsox/dmm/mgstage/xcity）、CoreEngine 编排、
  AppConfig、EventBus、图片水印，零 Qt 依赖
- `pyside6_gui/`：5 个 QML 页面（Home/Settings/Tools/Log/
  About）+ 15 个 QML 组件 + 3 个 Python 模型
  （settings_model 217 行 / processing_model 274 行 /
  log_model 240 行），共约 3386 行
- `tui-go/`：Go TUI，已验证「子进程 + JSON」桥接模式
  （`tui-go/pkg/python/client.go`，调 `uv run python
  cli.py scan` 解析 JSON）
- `cli/`：CLI 前端，子命令 scan / config / emby /
  organize / poster-crop / scrape，已支持 `--json-output`
  且逐条 `print(json.dumps(...), flush=True)` 流式输出

### 1.2 关键约束

1. **核心不重构**：业务核心是 Python（爬虫解析依赖
   lxml/BeautifulSoup、图片处理依赖 Pillow）。已决策
   （2026-09-20）：**不重构 core/cli**，以 JSONL 契约
   隔离保未来（评估见第 4 节）
   → 保留 `core/` + `cli/` 为唯一事实来源，新 GUI 只做前端
2. **桥接基础现成**：CLI 已支持 `--json-output` + 流式
   JSONL（逐文件输出 + flush），新 GUI 直接复用，无需
   改 core；仅需在 ObjC++ 侧实现子进程管理与解析
3. **GUI 形态不同**：AVDC 是元数据管理工具（表单/列表/
   日志/图片），非 14-MacApp 的波形绘制；ImGui 层需自绘
   表单控件（无 QML 级组件库），是本方案主要工作量
4. **网络在子进程**：爬虫网络请求发生在 Python 子进程，
   GUI 进程无网络，符合 14-MacApp「本地 GUI」架构约束
5. **中文界面**：ImGui 默认字体无 CJK，必须加载
   PingFang SC 入 font atlas（14-MacApp 现有 SF Pro
   加载路径可扩展）

## 2. 目标架构

### 2.1 总体分层

新前端目录 `mac-gui/`（仿 `tui-go/` 同级），复用
14-MacApp-C-Cpp 的四层架构：

```
mac-gui/
├── CMakeLists.txt          # CMake+Ninja
├── src/
│   ├── bridge/             # Python Bridge（新）
│   │   ├── ProcessRunner.{h,mm}   # NSTask 包装 + JSONL 解析
│   │   └── Bridge.hpp              # 命令封装与事件回调
│   ├── core/               # 纯 C++（少量，仅本地 UI 状态）
│   ├── ui/                 # ImGui/Metal 自绘内容区
│   │   ├── UIManager.{h,mm}
│   │   ├── Palette.{h,mm}  # 语义色（复用 14-MacApp）
│   │   └── widgets/        # 自绘表单组件（新）
│   └── shell/              # ObjC++ 薄壳 + SwiftUI
│       ├── AppDelegate.mm  # 无标题栏窗口 + 菜单栏
│       ├── Sidebar.swift   # 5 页导航（NSHostingView）
│       └── InfoBar.swift   # 玻璃按钮（.glassEffect）
└── third_party/imgui/      # submodule
```

依赖关系：Python core/cli 保持不变，GUI 只通过
`uv run python cli.py <cmd> --json-output` 子进程通信。

### 2.2 页面映射

| QML 页面 | 新实现 | 主要组件 |
|---------|-------|---------|
| HomePage | ImGui 表单+进度 | 目录选择（NSOpenPanel 桥接）、
  模式单选、进度条、成功/失败/跳过徽章 |
| SettingsPage | ImGui 表单（8 组） | checkbox/input/slider/
  radio/filepicker 自绘控件，读写 config.ini |
| ToolsPage | ImGui 卡片网格 | 工具卡片 + 操作对话框 |
| LogPage | ImGui 文本+过滤 | 日志查看器、级别过滤 |
| AboutPage | SwiftUI/ImGui | 版本、说明 |
| 侧边栏 | SwiftUI List | 5 页导航 + 选中高亮 |

### 2.3 关键实现点

1. **中文字体**：CoreText 读 PingFang SC（或苹方）构建
   ImGui font atlas，13pt 正文 + 15/17pt 标题档，
   与 14-MacApp 的 SF Pro 方案同构
2. **封面/图片**：`NSImage → CVPixelBuffer → MTLTexture`
   注册为 ImGui 纹理，供 Home 结果页与 Tools 预览使用
3. **进度/日志**：子进程 stdout 逐行解析 JSONL
   （`{type: progress|log|movie|done, ...}`），经
   Bridge 事件回调驱动 ImGui 进度条与日志面板
4. **取消任务**：NSTask terminate + 子进程 SIGTERM，
   CLI 已支持 Ctrl+C 语义（需验证）
5. **配置读写**：优先走 `cli.py config get/set`
   （JSON），避免 GUI 直接解析 config.ini 造成双写源
6. **菜单栏**：标准菜单 + Cmd 快捷键（复用 14-MacApp
   Menus.mm 模板），Signal 菜单改为页面导航项

## 3. 迁移步骤

### 阶段 0：骨架移植（0.5–1 人日）

- 从 14-MacApp-C-Cpp 复制：CMake 工程、AppKit 窗口
  （无标题栏 + fullSizeContentView）、SwiftUI 侧边栏
  与信息条、Menus.mm 标准菜单栏、Palette 语义色
- 替换波形 Demo 为 5 页导航骨架；加载 PingFang SC
  字体入 atlas，验证中文渲染
- 产出：可运行空壳 + 中文正常显示

### 阶段 1：Python Bridge（2–3 人日）

- `ProcessRunner.mm`：NSTask + pipe 包装，启动
  `uv run python cli.py ...`，异步逐行读 stdout
- JSONL 解析：progress/log/movie/done 事件分发
  （CLI 现有输出已近此格式，需核对字段对齐）
- 命令封装：`scan(path)` / `config(get|set)` /
  `process(path, mode, --json-output)` / `emby` /
  `poster-crop`
- 取消与超时处理；进程退出码与 stderr 归集到日志
- 产出：Bridge 单测（内存 mock CLI）

### 阶段 2：Home 页（1–2 人日）

- 输入区（目录选择 NSOpenPanel + 排除文件夹）
- 模式单选（刮削/整理）+ 开始/停止按钮
- 进度条 + 成功/失败/跳过徽章（接 Bridge 事件）
- 逐文件结果列表（番号、封面缩略图、状态）

### 阶段 3：Settings 页（2–3 人日）

- 8 组 SectionCard 布局（通用/代理/命名规则/媒体/
  排除/水印/Emby/其他，对照 SettingsPage.qml 347 行）
- 自绘表单控件：Checkbox / Input / Slider /
  RadioGroup / FilePicker / SwitchInt
- 读写走 `cli.py config get/set`，保存按钮统一提交

### 阶段 4：Tools / Log / About 页（2–3 人日）

- Tools：卡片网格 + 批量重命名/封面裁剪/Emby 集成
  入口（部分现为「待实现」，按现状迁移）
- Log：日志查看器（级别过滤 + 滚动），桥接
  `cli.py` stderr/文件日志
- About：版本信息 + 项目链接

### 阶段 5：打磨（1–2 人日）

- 浅/深色跟随系统（Palette 已支持，验证各页）
- 封面图片纹理加载性能；日志高频刷新防抖
- 全屏模式、快捷键、无障碍（减透明度/减动效）
- 长时间批量处理稳定性（子进程存活/内存）

### 阶段 6：清理与文档（0.5–1 人日）

- 执行第 5 节清理；更新 README、docs/、AGENTS.md
- 更新 pyproject.toml workspace 成员
- 归档迁移方案本身，记录踩坑

## 4. core/cli 重构评估（决策记录）

> 已决策（2026-09-20）：**不重构 core/cli**，以 JSONL
> 契约隔离保未来。

### 4.1 负载类型判断

AVDC 工作负载以 I/O 绑定为主（网络等待 + 站点限速），
非 CPU 绑定；高性能语言优势不明显。

| 模块 | 负载类型 | Python 现状 | 换 Go/Rust 收益 | 结论 |
|------|---------|------------|----------------|------|
| 网络抓取 | I/O 绑定 | requests +
  cloudscraper | 本地吞吐↑，但瓶颈在远端限速/封禁
  （JavDB ~30 次封 IP、DMM 需代理）；反爬生态
  Go/Rust 弱 | 不重构 |
| HTML 解析 | CPU 轻 | lxml（C 绑定
  libxml2） | goquery 更慢；Rust 略快差距小 | 类似 |
| 文件扫描 | I/O 绑定 | os.walk + 正则 |
  3–10x 提升，但绝对耗时秒级（有进度条掩盖） |
  可选定点 |
| 图片水印 | CPU 中 | Pillow（C 加速） |
  差距小 | 类似 |
| 批量编排 | 混合 | 线程池 + 事件总线 |
  瓶颈仍是网络 | 不重构 |

### 4.2 不重构理由

- 重写成本：64 文件 / 3450 行 + 7 爬虫 + 3 套测试
  （unit/integration/live），约 2–4 周
- 爬虫站点结构多变，长期维护成本高
- 反爬是最大隐性成本：Cloudflare 对抗在 Python
  cloudscraper 生态最成熟

### 4.3 契约隔离保障

- 桥接层只认 `cli.py <cmd> --json-output` 的 JSONL
  契约，GUI/TUI 与实现语言解耦
- 未来定点替换路径：若 scan 在超大目录（万级文件）
  实测变慢，单独用 Go 重写 scan（纯文件系统、无网络
  无爬虫依赖，约 1–2 天），其余命令保持 Python
- 触发条件：以实际性能痛点为准——迁移完成后跑真实
  批量抓取，若 Python 自身耗时占比 > 20% 才评估

## 5. 剩余文件清理

| 文件/目录 | 处理 | 理由 |
|----------|-----|------|
| `pyside6_gui/` | 迁移完成即移入 `.archive/` |
  无并行维护期（已决策）；保留历史供对照 |
| `pyqt5-gui/` | 移入 `.archive/` | 遗留前端，仅维护态 |
| `tui-go/` | 保留 | 终端场景独立价值，与 GUI 不冲突 |
| `cli/` + `core/` | 保留 | 事实来源，Bridge 依赖 |
| `pyproject.toml` | 移除已归档 workspace 成员 |
  避免 uv sync 失败 |
| `README.md` | 更新前端说明 | 标注 macOS GUI 为主力 |
| `docs/` | 更新架构图 + 新增 macosgui 文档 |
  遵循 00-doc-standards |
| `AGENTS.md` | 同步项目记忆 | 前端列表与命令更新 |

> 归档执行时机：**迁移完成并验证后**即归档（已决策：
> 无并行维护期）。开发期保留 PySide6 作为功能对照，
> 未验证通过前不动。`pyqt5-gui/` 可随 pyside6 一并归档。

## 6. 工作量汇总

| 阶段 | 内容 | 工作量（人日） |
|------|------|---------------|
| 0 | 骨架移植 | 0.5–1 |
| 1 | Python Bridge | 2–3 |
| 2 | Home 页 | 1–2 |
| 3 | Settings 页 | 2–3 |
| 4 | Tools/Log/About | 2–3 |
| 5 | 打磨 | 1–2 |
| 6 | 清理与文档 | 0.5–1 |
| **合计** | | **约 9.5–15 人日** |

按每周 5 人日估算约 **2–3 周**（含测试与返工余量）。

## 7. 风险与未决事项

| 风险 | 等级 | 缓解 |
|------|------|------|
| 中文 ImGui 渲染 | 低 | 字体 atlas 路径已验证 |
| Settings 表单自绘量大 | 中 | 8 种控件先做最小集，
  边用边补 |
| 长任务稳定性 | 中 | NSTask 生命周期 + 取消
  测试 |
| JSONL 字段与 GUI 期望不符 | 低 | 阶段 1 核对 CLI 输出 |
| 封面图片纹理内存 | 低 | 缩略图缓存 + LRU |

已定决策（2026-09-20）：
- PySide6：无并行维护期，迁移完成即归档
- tui-go：保留
- 新 GUI 目录：`mac-gui/`
- core/cli：不重构，契约隔离保未来（见第 4 节）

未决事项：
- 是否要动 `cli.py` 增加专用 JSONL 事件（推荐不
  动 core，仅必要时加子命令选项）

