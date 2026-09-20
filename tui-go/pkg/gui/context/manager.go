package context

import (
	"fmt"

	"avdc-tui/pkg/gui/types"
)

// Focuser 由 gui.Gui 实现；context 包通过它切换焦点，
// 避免 context 反向依赖 gui 包造成循环 import。
type Focuser interface {
	SetView(name string) error
}

// Manager 管理 context 栈与焦点路由。
// 栈底是根 context（files），临时 context（menu/confirm/
// prompt/config/help）Push 入栈，Esc 时 Pop 回上一层。
type Manager struct {
	focuser Focuser
	stack   []*Context
	all     map[string]*Context
	side    []*Context // 非临时 context（顺序列表，供循环切换）
}

// NewManager 创建 context 管理器，初始栈为 files。
// focuser 为 nil 时（测试）跳过焦点切换。
func NewManager(f Focuser) *Manager {
	m := &Manager{
		focuser: f,
		all:     defineContexts(),
	}
	order := []string{"files", "log", "result"}
	for _, name := range order {
		m.side = append(m.side, m.all[name])
	}
	m.stack = []*Context{m.all["files"]}
	return m
}

// Current 返回当前（栈顶）context；栈为空时回退到 files。
func (m *Manager) Current() *Context {
	if len(m.stack) == 0 {
		return m.all["files"]
	}
	return m.stack[len(m.stack)-1]
}

// Get 按名查找 context。
func (m *Manager) Get(name string) (*Context, bool) {
	c, ok := m.all[name]
	return c, ok
}

// IsTemporary 当前 context 是否为临时弹窗。
func (m *Manager) IsTemporary() bool {
	return m.Current().IsTemporary()
}

// SideContexts 返回非临时 context 列表（files/log/result）。
func (m *Manager) SideContexts() []*Context {
	return m.side
}

// Push 将命名 context 入栈并切换焦点。
// 若该 context 已在栈顶则无操作（避免重复入栈）。
func (m *Manager) Push(name string) error {
	c, ok := m.all[name]
	if !ok {
		return fmt.Errorf("unknown context: %s", name)
	}
	if m.Current().Name == name {
		return nil
	}
	m.stack = append(m.stack, c)
	return m.focus(c)
}

// Pop 弹出栈顶 context 并回到上一层。
// 栈底（files）不可弹出。
func (m *Manager) Pop() error {
	if len(m.stack) <= 1 {
		return nil
	}
	m.stack = m.stack[:len(m.stack)-1]
	return m.focus(m.Current())
}

// Switch 替换栈顶 context（不增深）；栈空时等价 Push。
func (m *Manager) Switch(name string) error {
	c, ok := m.all[name]
	if !ok {
		return fmt.Errorf("unknown context: %s", name)
	}
	if len(m.stack) == 0 {
		m.stack = []*Context{c}
		return m.focus(c)
	}
	m.stack[len(m.stack)-1] = c
	return m.focus(c)
}

// FocusNext 循环焦点到下一个非临时 context。
func (m *Manager) FocusNext() error {
	return m.cycle(1)
}

// FocusPrev 循环焦点到上一个非临时 context。
func (m *Manager) FocusPrev() error {
	return m.cycle(-1)
}

// cycle 在非临时 context 列表中循环切换（含当前为临时
// context 的情况：从 files 开始）。
func (m *Manager) cycle(delta int) error {
	cur := m.Current()
	idx := 0
	for i, c := range m.side {
		if c.Name == cur.Name {
			idx = i
			break
		}
	}
	next := (idx + delta + len(m.side)) % len(m.side)
	return m.Switch(m.side[next].Name)
}

// focus 切换焦点到 context 的 view（focuser 为 nil 时跳过）。
func (m *Manager) focus(c *Context) error {
	if m.focuser == nil {
		return nil
	}
	return m.focuser.SetView(c.View)
}

// ---- types 兼容导出（供其他包引用） ----

// KindSide / KindMain / KindTemporary 供外部便捷引用。
const (
	KindSide      = types.ContextSide
	KindMain      = types.ContextMain
	KindTemporary = types.ContextTemporary
)
