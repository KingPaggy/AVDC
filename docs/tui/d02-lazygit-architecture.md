# d02 lazygit 架构方案整理

> 基于 lazygit 官方 Codebase Guide 与源码结构，整理其
> GUI 架构的核心设计，作为 AVDC TUI 重构的参考蓝本。

## 1. 包结构总览

lazygit 是 Go 项目，`pkg/` 下按职责分包。与 GUI 直接
相关的核心包：

| 包 | 职责 |
|----|------|
| `pkg/app` | 启动：日志、用户配置、错误处理 |
| `pkg/commands/` | git 命令封装（git_commands/os_commands/\
  models/patch）——所有与外部二进制的通信都在此 |
| `pkg/config` | UserConfig 结构与默认值（`user_config.go`） |
| `pkg/i18n` | 国际化字符串（english.go） |
| `pkg/tasks` | 异步任务：高效渲染命令输出到主窗口 |
| `pkg/theme` | 颜色主题 |
| `pkg/gui` | GUI 主包（God Struct 仍存，持续拆分中） |
| `pkg/gui/context` | 每个 view 一个 context，管理状态、接收按键 |
| `pkg/gui/controllers` | 定义键位 + handler；可跨 context 复用 |
| `pkg/gui/controllers/helpers` | 控制器间共享代码 |
| `pkg/gui/types` | 共享类型与接口（避免循环依赖） |
| `pkg/gui/popup` | 弹窗组件（menu/confirm/prompt/toast） |
| `pkg/gui/style` | 文本样式（颜色/加粗） |
| `pkg/gui/presentation` | view 内部内容渲染 |
| `pkg/gui/status` | loader 与 toast |
| `pkg/gui/modes` | 模式状态（cherry-pick/rebase 等） |
| `vendor/.../gocui` | 底层库：事件循环、按键、渲染、
  View 结构（官方 vendor 内嵌） |

## 2. 核心概念

| 概念 | 说明 |
|------|------|
| View | gocui 包定义，内部 buffer 每次渲染时绘制到屏幕 |
| Context | 绑定一个 view + 该 view 的专属状态与逻辑；
  接收按键。`BaseContext` 携带 `GetWindowName()` |
| Controller | 一组键位 + handler；一个 controller 可分配给
  多个 context，一个 context 可有多个 controller |
| Helper | 控制器间共享的代码（控制器不能引用其他
  控制器的方法，只能提取到 helper） |
| Window | 屏幕上的一个区域，渲染某个 view；以默认
  view 命名。不同 context 可共享同一 window |
| Tab | window 内的标签页，每个 tab 对应一个 view，
  切换时把对应 view 置前 |
| Model | git 对象的表示（commits/branches/files） |
| ViewModel | context 用来维护 view 相关状态 |
| Keybinding | 键 + 动作的关联 |
| Action | 按键触发的动作（可能调用 git 命令，也可能
  只是导航） |
| Common | `c` 字段携带同层依赖包（logger/i18n/config/\
  helpers），控制器/helper 通过 `self.c.Helpers.X`
  访问共享能力 |

## 3. 分层与依赖方向

依赖单向流动，禁止反向：

```
controllers → helpers → contexts → views
```

- **controllers** 最上层：可引用 helpers/contexts/views
  （但 view 专属代码应放 context）
- **helpers** 可引用 contexts/views
- **contexts** 只能引用 views
- **views** 不能引用 contexts/controllers/helpers

装配关系集中在 `pkg/gui/controllers.go`（controller ↔
context 链接）、`pkg/gui/context/setup.go`（context 初
始化）、`pkg/gui/views.go`（view 创建与前后顺序）。

> lazygit 自述：controller 与 helper 的边界并无明确指南，
> 现行做法是「代码先进 controller，被第二个 controller
> 需要时再提取为 helper」；官方也承认「直接放 helper、
> controller 只做键位配对」可能更优但未定论。

## 4. 事件循环与异步

- 事件循环在 gocui 的 `MainLoop`：任何事件（按键/窗口
  尺寸变化）→ 处理 → 重绘屏幕
- 每次渲染调用 `layout.go` 的 layout 函数：布局各
  window + 执行 on-render 钩子
- 耗时操作异步执行：`c.OnWorker(myFunc)` 放后台线程；
  后台想回 UI 线程时 `c.OnUIThread(myOtherFunc)`
- 任务渲染走 `pkg/tasks`：后台命令输出高效流式渲染

## 5. 布局引擎

- `controllers/helpers/window_arrangement_helper.go`：
  计算每个 window 的尺寸与位置（flexbox 风格）
- `controllers/helpers/window_helper.go`：维护
  `WindowViewNameMap`（window ↔ view 映射），支持
  「某 window 当前显示哪个 view」查询与切换
- 布局与 context 解耦：window 是编排单位，context
  只声明自己属于哪个 window，切换 context 时 view
  在该 window 内更换

## 6. 配置系统

- UserConfig 全局配置（`pkg/config/user_config.go`），
  含默认值；用户配置合并覆盖
- 支持运行中热重载：Common 持有 UserConfig 指针，
  重载后新值即时生效；无法自动生效的项列入
  `checkForChangedConfigsThatDontAutoReload` 提示重启
- 键位、主题、布局均可配置

## 7. 对 AVDC 的借鉴要点

1. **context 是输入路由的唯一入口**：按键不绑 view，
   绑 context；Context 栈统一 Esc 返回行为
2. **controller 可跨 context 复用**：ListController 一套
   键位服务所有列表——AVDC 的 files/result/menu 同理
3. **单向依赖**：controllers → helpers → contexts →
   views，避免循环引用
4. **window 与 view 解耦**：AVDC 的 main 区域可用
   log/result 两个 view 共享一个 window，Tab 切换
5. **异步边界清晰**：OnWorker/OnUIThread 模式，
   AVDC 的 Python 子进程事件同样需要回 UI 线程
6. **配置可热重载**：TUI 自身配置（Phase 6）走
   默认值 + 用户覆盖合并
