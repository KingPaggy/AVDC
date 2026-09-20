# d01 TUI 重构分阶段详细计划

> 主计划见
> [../04-tui-lazygit-refactor.md](../04-tui-lazygit-refactor.md)。
> 本文档是 Phase 0-6 的逐阶段动作清单、涉及文件与验收。

## Phase 0：基线确认

**目标**：记录重构起点，建立回归依据。

**动作**：

- `go test ./...` 确认 4 个测试文件全绿（现有红项先修复）
- 手动跑一遍全流程：扫描 → 刮削 → 结果，留存行为基线
- 更新 `devnotes/gocui_integration.md`，补充新踩坑记录

**产出**：无代码改动。

## Phase 1：列表模型与渲染层

**目标**：文件/结果面板从直写 view 改为模型驱动。

**动作**：

1. 新建 `types/`：`VideoFile`（迁移自 `pkg/util`）、
   `ScrapeStats`、`WindowName`/`ContextKind` 枚举
2. 新建 `components/list_model.go`：`ListViewModel[T]`
   ——数据切片 + 选中索引 + `Len()`/`Selected()`/
   `Select(idx)`/`Move(delta)`，仿 lazygit `list.Render`
   做差分重绘
3. `FilesController` 改为持有 `ListViewModel[VideoFile]`，
   渲染函数从模型读取；删除 `renderFileList` 直写逻辑
4. `ResultController` 同样模型化（成功/失败行）

**涉及文件**：`pkg/gui/controllers/files_controller.go`、
`result_controller.go`、`pkg/util/`（删）、新增 `types/`、
`components/list_model.go`

**验收**：

- 选中/滚动行为与现状一致（j/k/g/G/方向键）
- `pkg/util/scanner.go`、`parser.go` 依赖清空后删除
- ListViewModel 单测：选中边界、空列表、Move 越界

## Phase 2：Window/Context/View 三层

**目标**：输入路由从「view 绑定」改为「context 栈」。

**动作**：

1. 新建 `context/base.go`：`BaseContext{Name, WindowName,
   Kind}` + 全局注册表（一次性定义全部 context：
   files/log/result/menu/help/config/confirm/prompt）
2. 重写 `context/manager.go`：Push/Pop/Switch 只改栈与
   焦点，**不再新建/删除 view**；弹窗 view 常驻
3. `keybindings.go` 改为按 context 注册，删除「全局按键
   重复绑到 5 个 view」的做法
4. 每个 context 一个 controller，按键处理迁入对应
   controller；`ContextMgr` 的 FocusNext/FocusPrev 泛化
   为非弹窗 context 循环

**涉及文件**：`pkg/gui/context.go`（重写）、
`keybindings.go`、`controllers/*`（迁移绑定）、
新增 `context/` 子包

**验收**：

- 焦点切换（h/l）、弹窗 Esc 返回行为与现状一致
- `context_test.go` 扩展：Push/Pop/Switch 路由断言
- 弹窗切换不再出现 DeleteView 重建闪烁

## Phase 3：布局与主题

**目标**：布局可配置、颜色集中管理。

**动作**：

1. 重写 `layout.go`：仿 lazygit flexbox 布局——三栏按
   比例（files 1/4、log 1/2、result 1/4），弹窗居中由
   布局引擎统一计算（替代各控制器手写坐标）
2. 新建 `helpers/theme.go`：`Theme{SelectedLineBg,
   BorderFocused, BorderUnfocused, StatusBar...}`，所有
   view 颜色引用 Theme；默认值沿用现有 green/blue/cyan
   观感
3. 选项栏/状态栏文案与颜色统一走 Theme + 状态模型

**涉及文件**：`pkg/gui/layout.go`（重写）、`views.go`、
`gui.go`（状态栏）、新增 `helpers/theme.go`

**验收**：

- 深浅色终端、窄窗口（<80 列）下布局可读
- 代码中不再出现散落的 `gocui.ColorXxx` 字面量
- 窗口 resize 后布局正确（gocui layout 回调）

## Phase 4：弹出组件复用

**目标**：menu/confirm/help 收敛为通用组件。

**动作**：

1. `components/menu.go`：通用菜单（标题/条目/回调），
   替代 `menu_controller.go`；刮削模式选择、配置操作
   等统一走它
2. `components/confirmation.go`：替代手写
   `confirm_dialog.go`（y/n/Esc），organize 前确认
3. `components/toast.go`：轻提示（成功/失败通知），
   新能力
4. 删除 `controllers/menu_controller.go`、
   `confirm_dialog.go` 旧实现；`help_panel.go` 改绑
   context 后保留

**涉及文件**：`pkg/gui/controllers/menu_controller.go`、
`confirm_dialog.go`（删）、`help_panel.go`（迁移）、
新增 `components/menu.go`、`confirmation.go`、`toast.go`

**验收**：

- 弹窗交互与现状一致；净减 200+ 行
- 组件独立单测：选中、取消、回调触发

## Phase 5：Python 命令层

**目标**：子进程封装统一，支持取消与事件解耦。

**动作**：

1. 新建 `pkg/commands/`：`ScanCmd`/`ProcessCmd`/
   `ConfigCmd` 封装 `cli.py` 调用（含 `scan` 与
   `--json-output`），错误统一包装
2. `Scraper` 改为：命令对象 + 事件回调 → AppState 更新；
   JSONL 解析移入 commands 层
3. 增加取消：进程树 kill + 状态机（idle/running/
   cancelling/done），Esc 或 `x` 取消当前任务
4. 复用 `pkg/python/client.go`（scan 已封装），删除与
   commands 层重叠部分

**涉及文件**：`pkg/gui/controllers/scraper.go`（重构）、
`pkg/python/client.go`（并入）、新增 `pkg/commands/`

**验收**：

- 刮削流程与现状一致；刮削中可取消且不残留进程
- commands 层 mock 子进程测试（沿用 mac-gui
  `mock_cli.py` 思路）
- stderr 非 JSON 输出不丢（保留 `[STDERR]` 前缀）

## Phase 6：交互增强（可选）

按需实施，单项独立可交付：

- `/` 搜索过滤文件列表（增量过滤 + Esc 退出）
- `space` 多选文件，批量操作（刮削/整理选中项）
- 用户配置文件（`~/.config/avdc/tui.yml`）：主题/键位
  覆盖；默认值与用户配置合并（lazygit config 模式）
- 结果面板 Tab 切换 成功/失败/全部 三视图
- 帮助面板改造为 context（已含 Tab 分页，迁移即可）

**产出**：以上各项独立提交，不阻塞主路径。

## 执行顺序与回退策略

- Phase 1-2 是地基，先做；每阶段独立 commit
  （`♻️ refactor(tui): ...`），便于单阶段回退
- 阶段完成后更新主计划 §6 执行记录，勾选完成项
- 若某阶段改动失控，回退该阶段 commit 重来，不累积
