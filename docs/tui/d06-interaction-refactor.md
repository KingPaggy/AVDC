# d06 操作逻辑重构（PromptContext + 反馈闭环）

> 在 d04/d05 架构基础上重构 TUI 交互逻辑：消除隐式模式、
> 统一输入弹窗、补齐刮削反馈闭环。

## 1. 目标与范围

Phase 0-6 完成后，TUI 功能已完整，但用户操作路径上
存在几处结构性别扭。本次重构聚焦**交互逻辑**，不改布局
三栏结构、Theme、commands 层与 Python JSONL 契约。

| # | 问题 | 根因 |
|---|------|------|
| 1 | `Enter` 三重语义（搜索确认/目录输入/刮削菜单） | 目录输入与搜索寄生在 files view，靠 `v.Editable` 隐式分叉 |
| 2 | 搜索实际不可用 | gocui 中 keybinding 优先于 Editor，`r/a/j/q` 等被拦截 |
| 3 | 弹窗关闭不恢复焦点 | `Menu`/`Confirmation` 调 `guiAdapter.PopContext()`，该方法是 no-op |
| 4 | organize 无二次确认 | `Confirmation` 组件零调用点 |
| 5 | 刮削无可视反馈 | 文件列表无行状态；日志不自动跟随 |
| 6 | 顶栏/帮助静态过期 | `renderOptions` 写死；help 键位表硬编码 |
| 7 | 配置写回丢注释 | `writeIniFile` 整文件重写，且路径依赖 cwd |

## 2. 交互模型变更

### 2.1 消除隐式模式

重构前 `Enter` 在 files 面板有四种含义，靠内部状态判断：

```
Enter → 搜索中？       → 确认搜索
      → 无目录？       → 把 files view 变成输入框
      → 输入模式中？   → 读取路径并扫描
      → 有目录？       → 弹刮削菜单
```

重构后 `Enter` 只保留一种含义（弹菜单）；目录输入、
搜索、字段编辑各自走独立弹窗。

### 2.2 输入统一走 PromptContext

新增 `components.Prompt`（通用输入弹窗，Enter 提交 /
Esc 取消 / Ctrl+U 清空），三处输入场景复用：

| 场景 | 触发 | 回调 |
|------|------|------|
| 目录输入 | files 无目录时 Enter/s/o/r | `OnSubmit` → `scanAndDisplay` |
| 搜索过滤 | `/` | `OnChange` → 实时过滤 |
| 配置字段 | config `Enter` | `OnSubmit` → 写回字段并重绘 |

目录输入的默认值取「已扫描目录 > config.ini 的
`common.media_path`」，避免每次手输。

`Prompt` 与 `Menu`/`Confirmation` 共用弹窗约定：居中、
常驻 view（`ShowPopup`/`HidePopup`）、`Push/PopContext`。

### 2.3 搜索为何必须移出 files view

gocui 的 `execKeybindings` 中 keybinding 优先于 Editor
（`gui.go`）：

```go
if g.matchView(v, kb) { return g.execKeybinding(v, kb) }
// ...仅在无 keybinding 匹配时才走 Editor
if g.currentView.Editable && g.currentView.Editor != nil { ... }
```

因此只要 files view 可编辑，绑定在其上的 `r/a/s/o/j/k/q`
就会拦截输入。移入 PromptContext 后，files view 永不
`Editable`，所有键位冲突消失。

## 3. 键位变更

原则：**现有单键语义全部保留**，只新增与统一。

| 键 | context | 动作 | 变更 |
|----|---------|------|------|
| `s` | files | 直接刮削（跳过菜单） | 新增 |
| `o` | files | 直接整理（弹确认） | 新增 |
| `Enter` | files | 菜单：scrape/organize/batch | 保留 |
| `/` | files | 搜索弹窗 | 语义不变，实现改 Prompt |
| `g`/`G` | log | 顶部（暂停跟随）/底部（恢复跟随） | 新增 |
| `Home`/`End` | log | 同上（固定键） | 新增 |
| `x` | result | 取消刮削 | 新增（原仅 files/log） |
| `Enter` | result | 状态栏显示选中项全文 | 新增 |
| `Esc` | files | 弹栈 | 新增（走全局 escape） |

新增 registry action：`files.scrape`、`files.organize`、
`log.top`、`log.bottom`（均可在 `~/.config/avdc/tui.yml`
覆盖）。

## 4. 反馈闭环

### 4.1 文件行状态

`types.FileStatus` 枚举 + `FilesController.status`
（path → status）作为单一数据源（`VideoFile` 是值类型，
过滤会产生拷贝，故不用字段）。

| 状态 | 前缀 | 颜色 |
|------|------|------|
| `FilePending` | `[ ]` | 默认（标记时为 `[x]`） |
| `FileActive` | `[>]` | 黄 |
| `FileOK` | `[✓]` | 绿 |
| `FileFailed` | `[✗]` | 红 |

数据流：`Scraper.notifyStatus`（progress→active、
success→ok、failure→fail）→ `FilesController.onFileStatus`
→ 状态表 + `g.Update` 重绘。批量刮削在 `runBatch` 中
按文件手动通知（`--single` 事件流只有 done）。

### 4.2 日志自动跟随

- log view 默认 `Autoscroll = true`
- 用户 `j/k/Home` 主动滚动时置 `false`（暂停跟随，
  便于查看历史）
- `G`/`End` 置 `true` 恢复跟随

### 4.3 状态栏与 options

重构前 `layout.renderStatus` 每次重绘都写死
`"Ready | Select a directory..."`，会覆盖刮削进度。
改为状态化：

- `Gui.statusText` 保存状态；`SetStatus` 异步触发重绘
- `renderStatus` 从 `statusText` 渲染（空则回退默认提示）
- `UpdateStatusReady/Scraping/Done` 改为写状态
- 状态栏附带操作提示（`x: cancel` 等）

`renderOptions` 改为按当前 context 查 `optionsHints`，
弹窗打开时显示该弹窗的键位。

### 4.4 help 动态化

`HelpKey` 增加 `Action` 字段，渲染时从键位注册表解析
（`keys.String(action)`），跟随用户覆盖；弹窗通用键
（Enter/Esc/y/n/Ctrl+U/Tab）保留固定文本。分类改为
Global/Files/Log/Result/Nav/Popups 六页。

## 5. 弹窗栈与焦点修复

`Menu`/`Confirmation` 原先在 handler 里构造
`guiAdapter{g}`，而 `guiAdapter.PopContext()` 返回 nil
（no-op），导致关闭弹窗后 context 栈与焦点均未恢复。

修复：组件在 `Show` 时保存真实 `GuiLike`，关闭时调
`close()` → `Hide` + 真实 `PopContext`；删除 `guiAdapter`。
`Prompt` 从设计起即遵循此模式。

## 6. 配置编辑器修正

| 项 | 修正前 | 修正后 |
|----|--------|--------|
| 路径 | `"config.ini"`（依赖 cwd） | `python.FindProjectRoot()` 拼接 |
| 写回 | `writeIniFile` 整文件重写 | `writeIniFilePreserving` 按行更新 |
| 注释 | 丢失 | 保留（含空行与键顺序） |
| 键序 | map 遍历无序 | 原文件顺序 |
| 字段编辑 | 复用 config view + 临时 SetKeybinding | PromptContext |

`writeIniFilePreserving` 逻辑：按行扫描，section 内命中
的键替换值；未命中的键追加到该 section 末尾（`slices.
Insert`，从后往前避免索引错位）；section 不存在则在文件
末尾新建。

## 7. 涉及文件

| 文件 | 变更 |
|------|------|
| `components/prompt.go` | 新增：通用输入弹窗（含 `onChangeEditor`） |
| `components/menu.go` | 删除 `guiAdapter`，`close()` 真实弹栈 |
| `components/confirmation.go` | 同上 |
| `gui/types/types.go` | 新增 `FileStatus` 枚举 |
| `gui/views.go` | log view `Autoscroll = true` |
| `gui/keybindings.go` | 滚动暂停跟随；`g/G/Home/End`；files 绑 escape |
| `gui/layout.go` | `optionsHints` 动态；`renderStatus` 状态化 |
| `gui/gui.go` | `SetStatus`/`StatusText`；状态更新改造 |
| `controllers/files_controller.go` | Prompt 化目录/搜索；s/o；状态渲染；`projectRoot` |
| `controllers/scraper.go` | `SetStatusHook`/`notifyStatus`；批量通知 |
| `controllers/result_controller.go` | `Enter` 详情 |
| `controllers/help_panel.go` | 键位表动态化（六页） |
| `controllers/config_editor.go` | 路径 + 保留注释写回 + Prompt 编辑 |
| `gui/config/registry.go` | 新增 4 个 action |
| `sample-tui.yml` | 同步新 action |

## 8. 与 d05 的差异

| d05 设计 | 本次实现 | 说明 |
|----------|---------|------|
| `s`/`o` 直达 | 已实现 | 均保留菜单路径 |
| `prompt` context | 已落地 | d05 已规划，Phase 2 遗漏 |
| `d` 删除文件 | 未实现 | 危险操作，本次不做 |
| `:` shell 命令 | 未实现 | 不需要 |
| `+`/`_` 屏幕模式 | 未实现 | 优先级低 |
| log `]`/`[` tab 切换 | 未实现 | 保持三栏布局 |
| `v` 范围选择 | 未实现 | `space`/`a` 已覆盖批量场景 |
