# gocui 集成开发经验

## 1. ErrUnknownView 必须用 go-errors 的 Is() 判断

gocui 内部使用 `github.com/go-errors/errors` 包装错误：

```go
return v, errors.Wrap(ErrUnknownView, 0)
```

Go 标准库的 `errors.Is()` 无法解包 `go-errors` 包装的错误（v1.0.2 未实现 `Unwrap()`），导致直接比较失败：

```go
// 错误写法 — 会返回 "unknown view"
if err != nil && err != gocui.ErrUnknownView {
    return err
}

// 正确写法 — 使用 go-errors 的 Is()
import "github.com/go-errors/errors"

if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
    return err
}
```

受影响的文件：`views.go`、`layout.go`、`confirm_dialog.go`、`help_panel.go`、`menu_controller.go`、`config_editor.go`。

## 2. SetManagerFunc 会删除所有 views 和 keybindings

```go
// gocui/gui.go
func (g *Gui) SetManager(managers ...Manager) {
    g.managers = managers
    g.currentView = nil
    g.views = nil        // 删除所有 views
    g.keybindings = nil  // 删除所有 keybindings
}
```

因此调用 `SetManagerFunc` 后再 `createViews()` 是正常的，但如果 layout 回调再次触发 SetView，之前创建的 view 仍然可用（因为 view 已被注册到 gocui 内部的 views 列表）。

## 3. SetView 的行为

- **第一次调用**（view 不存在）：创建 view，返回 `ErrUnknownView`（被 go-errors 包装过）
- **后续调用**（view 已存在）：更新 view 坐标，返回 nil

所以标准模式是：

```go
v, err := g.SetView(name, x0, y0, x1, y1, 0)
if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
    return err
}
// v 一定不为 nil
```

## 4. view 创建顺序：layout → createViews → keybindings

lazygit 的顺序（也是我们遵循的顺序）：

```
initGocui() → SetManagerFunc(layout) → createAllViews() → onNewRepo() → MainLoop()
```

关键点：
- `SetManagerFunc` 在 `createViews` 之前调用
- view 创建通过 `prepareView()` 调用 `SetView()`，接受 `ErrUnknownView`
- keybinding 注册在 view 创建之后

## 5. Mock 测试中的 nil 安全

测试时 `ContextMgr` 的 `gui` 字段为 nil，所以 `Push`/`Pop`/`FocusNext`/`FocusPrev` 中调用 `m.gui.SetView()` 需要 nil 检查：

```go
func (m *ContextMgr) Push(name string) error {
    for _, ctx := range m.allCtx {
        if ctx.Name == name {
            m.stack = append(m.stack, ctx)
            if m.gui != nil {      // 测试时为 nil
                return m.gui.SetView(ctx.View)
            }
            return nil
        }
    }
    return nil
}
```

## 6. 项目架构要点

```
Go TUI (gocui)  ──subprocess──▶  Python cli.py --json-output
                                      │
                                      └──▶ 调用 core/ 业务逻辑
```

- Go 端负责 UI 交互（面板、导航、输入）
- Python 端负责数据抓取和处理（复用现有 core/ 代码）
- 通信协议：JSON 行，`{"type": "progress|success|failure|log|done", ...}`
- Python 使用 `uv run python cli/cli.py --json-output` 启动
