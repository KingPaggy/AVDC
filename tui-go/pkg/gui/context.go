package gui

// Context represents a focusable UI panel.
type Context struct {
	Name    string
	View    string
	IsPopup bool
}

// ContextMgr manages the stack of active contexts.
// Following lazygit's pattern: contexts are pushed/popped
// to control focus and input routing.
type ContextMgr struct {
	gui    *Gui
	stack  []*Context
	allCtx []*Context
}

// NewContextMgr creates a new context manager.
func NewContextMgr(g *Gui) *ContextMgr {
	m := &ContextMgr{gui: g}
	m.defineContexts()
	return m
}

// defineContexts registers all available contexts.
func (m *ContextMgr) defineContexts() {
	m.allCtx = []*Context{
		{Name: "files", View: "files", IsPopup: false},
		{Name: "log", View: "log", IsPopup: false},
		{Name: "result", View: "result", IsPopup: false},
	}
	// Default: start with files context
	m.stack = []*Context{m.allCtx[0]}
}

// Current returns the currently active context.
func (m *ContextMgr) Current() *Context {
	if len(m.stack) == 0 {
		return m.allCtx[0]
	}
	return m.stack[len(m.stack)-1]
}

// Push adds a context to the stack and focuses its view.
func (m *ContextMgr) Push(name string) error {
	for _, ctx := range m.allCtx {
		if ctx.Name == name {
			m.stack = append(m.stack, ctx)
			if m.gui != nil {
				return m.gui.SetView(ctx.View)
			}
			return nil
		}
	}
	return nil
}

// Pop removes the top context and focuses the one below.
func (m *ContextMgr) Pop() error {
	if len(m.stack) <= 1 {
		return nil // Don't pop the last context
	}
	m.stack = m.stack[:len(m.stack)-1]
	top := m.Current()
	if m.gui != nil {
		return m.gui.SetView(top.View)
	}
	return nil
}

// Switch replaces the top context with the named one.
func (m *ContextMgr) Switch(name string) error {
	if len(m.stack) == 0 {
		return m.Push(name)
	}
	m.stack[len(m.stack)-1] = nil
	m.stack = m.stack[:len(m.stack)-1]
	return m.Push(name)
}

// FocusNext cycles focus to the next non-popup context.
func (m *ContextMgr) FocusNext() error {
	panels := []*Context{m.allCtx[0], m.allCtx[1], m.allCtx[2]}
	current := m.Current()
	idx := 0
	for i, p := range panels {
		if p.Name == current.Name {
			idx = i
			break
		}
	}
	next := (idx + 1) % len(panels)
	m.stack = m.stack[:len(m.stack)-1]
	m.stack = append(m.stack, panels[next])
	if m.gui != nil {
		return m.gui.SetView(panels[next].View)
	}
	return nil
}

// FocusPrev cycles focus to the previous non-popup context.
func (m *ContextMgr) FocusPrev() error {
	panels := []*Context{m.allCtx[0], m.allCtx[1], m.allCtx[2]}
	current := m.Current()
	idx := 0
	for i, p := range panels {
		if p.Name == current.Name {
			idx = i
			break
		}
	}
	prev := (idx - 1 + len(panels)) % len(panels)
	m.stack = m.stack[:len(m.stack)-1]
	m.stack = append(m.stack, panels[prev])
	if m.gui != nil {
		return m.gui.SetView(panels[prev].View)
	}
	return nil
}
