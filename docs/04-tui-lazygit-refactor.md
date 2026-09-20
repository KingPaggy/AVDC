# 04 TUI 重构计划（参考 lazygit 架构）

> tui-go 从命令式 gocui 直写，渐进重构为 lazygit 式
> Window/View/Context 三层架构，分 6 阶段推进，每阶段可运行。

## 1. 背景与现状

### 1.1 技术栈与目录结构

- **语言/依赖**：Go 1.26，`github.com/jesseduffield/gocui`
  （lazygit 作者维护的 fork，v0.3.1-0.20260327）
- **与 core 通信**：子进程 `uv run python cli/cli.py`
  `--json-output`，JSONL 事件流（log/progress/success/
  failure/done）+ `scan` 命令
- **当前规模**：约 2800 行，22 个 Go 文件

```
tui-go/
├── main.go / pkg/app/            入口 + BuildInfo
├── pkg/gui/
│   ├── gui.go                    Gui 包装 + 状态栏更新
│   ├── layout.go                 5 面板坐标硬编码
│   ├── views.go                  视图创建（Frame 等属性）
│   ├── keybindings.go            全局按键（重复绑到所有 view）
│   ├── context.go                ContextMgr 栈（玩具版）
│   └── controllers/              文件列表/刮削/配置编辑/
│                                 菜单/帮助/确认/列表导航
├── pkg/util/                     scanner/parser（已废弃，待删）
├── pkg/python/client.go          scan 子进程封装
└── devnotes/                     gocui 踩坑记录
```

### 1.2 现状问题清单

| # | 问题 | 现状 | lazygit 做法 |
|---|------|------|-------------|
| 1 | 列表无模型层 | `fmt.Fprintln` 直写 view，<br>选中靠 gocui cursor | ListViewModel：数据 + 选中<br>索引 + 渲染分离 |
| 2 | Context 是玩具 | 按键重复绑到所有 view，<br>靠 current view 路由 | 按键绑到 context，<br>Context 栈路由输入 |
| 3 | 无 Window 概念 | 面板即 view，焦点与布局<br>耦合 | Window（逻辑区域）与<br>View（渲染实例）解耦 |
| 4 | 布局硬编码 | layout.go 写死 1/4-1/2-<br>1/4 三栏 | flexbox 布局，可配置/可重排 |
| 5 | 无主题系统 | 颜色散落各处（Color-<br>Green/Blue/Cyan） | Theme 对象集中管理，<br>支持用户配置 |
| 6 | 命令式直写 | 状态散落控制器字段，<br>渲染即修改 | Model 驱动渲染：状态变更<br>→ 重绘 |
| 7 | 弹窗频繁重建 | DeleteView + SetView<br>重注册按键 | 常驻 view + 显隐切换，<br>无闪烁 |
| 8 | 无搜索/过滤 | 无 | `/` 进入搜索，列表过滤 |
| 9 | 无多选 | 无 | vim 风格多选，space 标记 |
| 10 | 命令层简陋 | Scraper 直接 exec.Command | Commands 层封装 +<br>取消/优雅退出 |
| 11 | 无配置文件 | 只能改 core 的 config.ini | 用户配置合并默认值 |
| 12 | 测试不足 | 4 个 mock 测试，无<br>context 级测试 | Controller 单测 +<br>context 路由测试 |

## 2. 目标架构：lazygit 设计模式

### 2.1 参考的核心模式

lazygit `pkg/gui` 的核心设计（源码 + 公开架构分析）：

1. **Window / View / Context 三层解耦**

   - **Window**：逻辑屏幕区域（如 files/log/result），
     布局引擎的编排单位
   - **View**：gocui 渲染实例，只负责绘制
   - **Context**：绑定一个 Window，携带按键路由与状态
     （`BaseContext.GetWindowName()`），是输入路由入口

2. **Context 栈管理焦点**：`Push/Pop/Switch` 控制当前
   context，`Esc` 弹栈回到上一层——所有弹窗/菜单返回
   行为统一的基础。

3. **Context 接口族**：`IListContext`（列表选择）、
   `ITabbedContext`（Tab 切换）、`IScrollableContext`
   （滚动）按能力组合，避免控制器重复实现。

4. **Model 驱动渲染**：应用状态集中存放，渲染从状态
   出发；列表用补丁式更新（只重绘变化行）。

5. **复用组件**：confirmation / menu / prompt / toast
   是通用组件，任何 context 都可调用，不各自为政。

### 2.2 目标目录结构

```
tui-go/pkg/gui/
├── types/             WindowName、ContextKind、共享模型
├── model.go           AppState（文件列表/刮削状态/结果）
├── views/             View 层：纯渲染原语（创建/属性）
├── context/
│   ├── base.go        BaseContext + 注册表
│   ├── files.go / log.go / result.go / menu.go /
│   │   config.go / help.go / confirm.go / prompt.go
│   └── manager.go     Context 栈 + 输入路由
├── controllers/       交互控制器（每个 context 一个）
├── helpers/           WindowHelper / ViewHelper / Theme
├── components/
│   ├── list_model.go  ListViewModel（选中/滚动/过滤）
│   ├── confirmation.go / menu.go / prompt.go / toast.go
├── layout.go          flexbox 布局
├── keybindings.go     context 级按键注册
└── gui.go             主循环 + 装配
```

目标约 3500-4500 行（新增类型/组件/测试，但消除大量
重复绑定与重建代码）。

### 2.3 数据流

```
按键 → gocui 事件 → ContextManager 路由到当前 context
         → Controller.Handle → 更新 AppState
         → 状态变更通知 → View 补丁重绘

Go 子进程：Commands 层 → cli.py --json-output
        → JSONL 事件 → AppState 更新 → 进度/日志/结果重绘
```

关键不变式：**控制器不直接写 view**，只改状态；
**view 只读状态**。弹窗/菜单通过 context 栈切换，
不删除视图。

## 3. 分阶段重构计划

**原则**：渐进式，每阶段结束可编译、可运行、测试通过；
不搞一次性大爆炸重写。每阶段独立提交，便于回退。
详细动作见 [tui/d01-phase-plan.md](tui/d01-phase-plan.md)。

| 阶段 | 主题 | 核心产出 | 预估改动 |
|------|------|---------|---------|
| 0 | 基线确认 | 测试基线、现状文档 | 0 |
| 1 | 列表模型与渲染层 | types/ + ListViewModel | ~400 行 |
| 2 | 三层架构 | context/ + manager | ~700 行 |
| 3 | 布局与主题 | flexbox + Theme | ~400 行 |
| 4 | 弹出组件复用 | components/ | ~300 行（净减） |
| 5 | Python 命令层 | commands + 取消 | ~400 行 |
| 6 | 交互增强（可选） | 搜索/多选/配置 | ~500 行 |

执行顺序：**Phase 0 → 1 → 2 是地基，先做**；3-5 顺序
推进；6 按需单项交付。每阶段完成后在本文件末尾勾选
并补充实际踩坑记录。

## 4. 风险与注意事项

| 风险 | 说明与对策 |
|------|-----------|
| gocui 版本 | jesseduffield 维护 fork（非官方稳定版），<br>升级/换库前先确认 API；layout 回调频率高，<br>差分渲染避免全量 Clear |
| go-errors 陷阱 | gocui 错误用 `github.com/go-errors`<br>包装，判断必须 `errors.Is()`（标准库不行），<br>见 `devnotes/gocui_integration.md` §1 |
| SetManagerFunc | 会删除所有 view 和 keybinding，重构中<br>不得运行时重复调用；弹窗显隐改用 view<br>属性而非删除（见 devnotes §2） |
| 大爆炸风险 | 严禁一次重写全部；每阶段独立提交保持<br>可运行。Phase 1-2 是地基先做 |
| 测试回归 | 现有 GUI 接口 + mockGUIForScraper 保留<br>升级；每阶段补 context/组件单测 |
| 真实刮削验证 | Phase 5 后跑真实小批量刮削验证 JSONL<br>链路（勿对 fixtures 跑 organize） |
| config.ini 归属 | TUI 配置编辑器改 core 的 config.ini<br>（`s` 保存），重构保持该行为；TUI 自身<br>配置（Phase 6）另存用户目录 |

## 5. 验收标准

1. **功能对等**：扫描 → 刮削/整理 → 结果全流程与重构前
   一致（菜单选模式、进度、状态栏、帮助面板）
2. **测试通过**：`go test ./...` 全绿；新增 ListViewModel、
   context 路由、组件、commands 四类单测
3. **代码质量**：
   - 无散落颜色字面量（全部走 Theme）
   - 无重复按键绑定（全部走 context 注册表）
   - 无 DeleteView 重建弹窗（常驻 view 显隐）
   - `pkg/util/scanner.go`、`parser.go` 已删除
4. **体验提升**：弹窗无闪烁、刮削可取消、窄窗口布局
   正常、选中行高亮不跳动
5. **规模**：总量控制在 ~4000 行，重复代码净减
   （弹出组件合并省 200+ 行）

## 6. 执行记录

> 每阶段完成后在此勾选并记录实际偏差。

- [x] **Phase 0**（2026-09-20）：基线确认。build + 3 测试包全绿；
  网络坑：go-errors 下载需 `GOPROXY=goproxy.cn`（已记 devnotes）
- [x] **Phase 1**（2026-09-20）：列表模型化。新增 types/（VideoFile/
  WindowName/ContextKind）、components/ListViewModel[T]（5 单测）；
  ListController 绑定 ListModel 接口 + 新增翻页键（`,`/`.`、PgUp/
  PgDn）；Files/Result 面板模型驱动渲染；删除废弃 pkg/util/。
  偏差：无（行为与现状一致）
- [x] **Phase 2**（2026-09-20）：Window/Context/View 三层。新增
  context/ 包（8 个 context 注册表 + Manager 栈路由，10 单测），
  Focuser 接口防循环依赖；keybindings 按 context 注册（全局键只绑
  files/log/result，消除 5-view 重复绑定；j/k 滚动仅 log）；4 个弹窗
  （menu/confirm/help/config）DeleteView 重建 → Visible 显隐常驻
  （showPopup/hidePopup），无闪烁。偏差：弹窗尚未接入 context 栈
  （menu 显示时栈顶仍为 files，Esc 由各 controller 处理）——待
  Phase 4 组件化时接入。
- [x] **Phase 3**（2026-09-20）：布局与主题。新建 helpers/（Theme
  唯一颜色源 + style 标签辅助 + LevelInfo/LevelError 常量）；
  layout.go 重写：flexPanels 权重分配 + 窄窗口（<60 列）降级
  隐藏 result + 弹窗统一 centerRect 居中；4 处弹窗坐标收敛；
  全部 gocui.ColorXxx 字面量清理（验收 grep 通过）；新增
  layout_test（宽/窄/极窄 3 测试）。偏差：flexPanels 保持原
  布局坐标语义（files→log 留空隙、log→result 相邻重叠），
  未做严格等距对称；config 编辑器非居中弹窗，坐标保留手写。
- [x] **Phase 4**（2026-09-20）：弹出组件复用。showPopup/hidePopup/
  CenterRect 移到 components（导出）；新建 Menu 组件（ListViewModel
  管理选中，幂等键位注册，OnDone/OnCancel 回调）替代
  menu_controller.go；新建 Confirmation（y/n/Esc）替代
  confirm_dialog.go；新建 Toast（状态栏轻提示，不做计时器）。
  files_controller 改用 Menu 组件，修复选择后隐藏 view 残留焦点
  （OnDone 切回 files）。组件单测 4 个。偏差：行数净增 ~90
  （组件自包含键位+渲染，含通用 popup 迁移），未达「净减 200+」
  目标，但复用模式建立（新增菜单仅需几行 config）；confirm_dialog
  原无调用点（死代码）一并清除；Menu 未接入 context 栈（仍由
  调用方切回焦点），留待后续。
- [x] **Phase 5**（2026-09-20）：Python 命令层。新建 pkg/commands/
  （ProcessRunner：子进程 + JSONL 流式解析 + 进程组 kill 取消 + 
  cancelled flag；CmdFactory 注入支持 mock；ScanArgs/ProcessArgs）；
  Scraper 改用 ProcessRunner + 事件回调，新增 Cancel（状态机
  running/cancelling）；x 键取消（files/log）；uv 绝对路径统一。
  commands 层 6 个 mock 子进程测试（事件流/stderr/非 JSON/取消/
  并发拒绝/args）。偏差：python/client.go 的 Scan 保留同步实现
  （不并入流式 ProcessRunner）；取消状态显示为日志行而非独立
  toast。
- [x] **Phase 6a**（2026-09-20）：弹窗接入 context 栈（修复 Phase 2/4
  偏差）。GUI 接口加 PushContext/PopContext；Menu/Confirmation/
  Help/Config 弹窗 show 时 Push、关闭时 Pop，Esc 语义统一走栈。
- [x] **Phase 6b**（2026-09-20）：结果面板 Tab 过滤。t 键循环
  全部/成功/失败，标题显示当前过滤，渲染按 filter 过滤模型。
- [x] **Phase 6c**（2026-09-20）：搜索过滤。/ 进入搜索模式（view
  可编辑 + 自定义 Editor 实时回调），输入按文件名增量过滤；
  Enter 确认保留过滤，Esc 取消恢复；files 专属 esc 接管（全局
  esc 剔除 files），无键位冲突。
- [x] **Phase 6d**（2026-09-20）：多选与批量刮削。space 标记/
  a 全选（行前缀 [x]），Enter 菜单增「Batch scrape N marked」
  项，Scraper.StartBatch 串行 --single（commands.SingleArgs）；
  x 可取消批量。偏差：--single 事件流只有 done，批量不做成功/
  失败统计（显示 N processed）。
- [x] **Phase 6e**（2026-09-20）：用户配置。新增 pkg/gui/config/
  （Config/Load + ParseKey/ParseAttribute + Registry 默认键位表 +
  ApplyTheme，9 单测）；配置文件 ~/.config/avdc/tui.yml（XDG_
  CONFIG_HOME 优先）；主题全字段覆盖 + 键位覆盖（global/log/
  files/result/list 共 18 action，方向键/Ctrl+C 固定不可配，
  无效覆盖回退默认）；gui.New 加载配置失败不阻塞启动；新增
  sample-tui.yml 示例（解析验证通过）。偏差：Menu/Confirmation
  弹窗内部键（enter/esc）与 files 的 Enter/Esc 固定不可配（弹窗
  通用约定）；键位配置暂不支持热重载（需重启）。
