# d04 AVDC TUI 功能划分与面板设计

> 基于 d02/d03 的 lazygit 方案，设计 AVDC TUI 的面板
> 布局、Context、Controller 与 Model 划分。

## 1. 功能盘点与概念映射

现有 tui-go 功能，映射到 lazygit 概念：

| 现有功能 | lazygit 概念 | 目标形态 |
|---------|-------------|---------|
| 文件列表（扫描/选中） | 列表面板 | FilesContext +
  ListViewModel |
| 目录路径输入 | Input prompt | PromptContext
  （临时弹窗） |
| 刮削/整理模式选择 | Menu | MenuContext（临时弹窗） |
| 刮削进度与日志流 | 主面板（log） | LogContext（只读滚动） |
| 成功/失败结果 | 主面板（tab 视图） | ResultContext（列表） |
| 配置编辑（config.ini） | 二级面板 | ConfigContext（临时） |
| 帮助面板 | `?` 键位菜单 | HelpContext（临时） |
| organize 前确认 | Confirmation | ConfirmationContext |
| 状态栏（Ready/Scraping/Done） | status window | StatusView（非焦点，
  只读） |
| options 栏（键位提示） | options bar | OptionsView（非焦点） |

## 2. 面板布局设计

采用 lazygit 式「侧栏 + 主区域」：

```
┌────────────────────────────────────────────────┐
│ options  当前 context 键位提示（常驻顶栏）       │
├─────────────┬──────────────────────────────────┤
│             │  main 区域（Window）              │
│  files      │  ┌─ tab: log ── tab: result ─┐  │
│  （侧栏）    │  │ 刮削实时日志流  /  结果列表 │  │
│  文件列表    │  └───────────────────────────┘  │
│  选中行高亮  │    （] / [ 切换 tab）            │
├─────────────┴──────────────────────────────────┤
│ status  状态栏：Ready / 进度 xx/xx (xx%) / Done │
└────────────────────────────────────────────────┘
```

- **files Window**（左侧 1/4）：文件列表，核心交互区
- **main Window**（右侧 3/4）：log 与 result 两个 view
  共享，Tab 切换（仿 lazygit 的 window 内多 view）
- **options / status**：非焦点栏，不参与 context 栈
- **弹窗**（menu/confirm/prompt/help）：居中覆盖，
  常驻 view 显隐，不做 DeleteView 重建

窄窗口（<80 列）降级：main 区域自动隐藏 result tab
标题，仅保留当前 tab。

## 3. Context 设计

| Context | Kind | Window | 类型 | 职责 |
|---------|------|--------|------|------|
| files | SIDE | files | list | 文件列表：选中、
  标记、启动刮削/整理 |
| log | MAIN | main | scroll | 刮削日志实时流 |
| result | MAIN | main | list | 成功/失败结果，
  可过滤 |
| menu | TEMPORARY | — | list | 模式选择等菜单 |
| confirm | TEMPORARY | — | static | 危险操作确认 |
| prompt | TEMPORARY | — | input | 目录路径输入 |
| config | TEMPORARY | — | list | config.ini 字段
  编辑 |
| help | TEMPORARY | — | scroll | 键位帮助
  （Tab 分页） |

Context 栈规则：

- 默认栈底 `files`；`h`/`l` 在 files ↔ log ↔ result
  间循环焦点
- 临时 context（menu/confirm/prompt/help/config）
  Push 入栈，`esc` Pop 回 files
- FocusNext/FocusPrev 只遍历非临时 context

## 4. Controller 设计

| Controller | 分配到的 context | 职责 |
|-----------|-----------------|------|
| ListController | files/result/menu/\
  config | 通用导航：j/k、g/G、
  翻页、搜索、范围选择 |
| FileController | files | 扫描、刷新、Enter
  启动刮削（弹菜单）、space 标记 |
| ScraperController | files（全局） | 启动/取消刮削，
  订阅 JSONL 事件更新状态 |
| ConfigController | config | 字段导航/编辑/保存 |
| HelpController | help | 键位表渲染、Tab 分页 |
| MenuController | menu | 菜单选中/确认 |
| ConfirmController | confirm | y/n/esc |
| PromptController | prompt | 输入确认/取消 |
| GlobalController | 全部 | esc 弹栈、? 帮助、
  q 退出、R 刷新 |

复用关系：ListController 一套键位服务 4 个列表
context；GlobalController 的 esc 弹栈是所有返回行为
的唯一实现。

## 5. Model 设计

```go
// AppState：全局状态（渲染唯一数据源）
type AppState struct {
    Files     []*FileItem        // 文件列表
    Scrape    ScrapeState        // 刮削状态
    Results   []ResultItem       // 结果
    Logs      []LogLine          // 日志缓冲
    Theme     Theme              // 主题
}

type FileItem struct {
    Path   string
    Name   string
    Number string
    Status FileStatus   // pending/scraping/ok/failed
    Marked bool         // space 多选标记
}
```

- 渲染从 AppState 出发，控制器只改状态、不直写 view
- `FileItem.Status` 驱动行前缀图标（`[ ]`/`[*]`/`[✓]`/
  `[✗]`）与颜色
- 刮削事件 → 更新 ScrapeState + 追加 Logs/Results →
  对应 view 增量重绘

## 6. 与分阶段计划的对应

| 设计项 | 落地阶段 |
|--------|---------|
| types/ + ListViewModel + AppState | Phase 1 |
| Context 注册表 + 栈路由 + 单向依赖 | Phase 2 |
| 侧栏+主区域 flexbox 布局 + Theme | Phase 3 |
| menu/confirm/prompt/toast 组件 | Phase 4 |
| ScraperController + commands 层 | Phase 5 |
| 搜索/多选/用户配置（含键位覆盖） | Phase 6 |

详细键位设计见 [d05-avdc-keybindings.md](d05-avdc-keybindings.md)。
