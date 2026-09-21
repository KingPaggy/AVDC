package components

import (
	"fmt"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

// MenuItem 表示菜单中的一个选项。
type MenuItem struct {
	Display string // 显示文本
	Value   string // 选中后回调的值
}

// MenuConfig 定义菜单的标题、选项与回调。
type MenuConfig struct {
	Title  string // 弹窗标题
	Items  []MenuItem
	OnDone func(selected string) // 确认选中（值）
	// OnCancel 可空：取消/关闭时回调
	OnCancel func()
}

// Menu 是通用菜单弹窗组件：任何 context 都可调用，
// 替代各自为政的手写菜单。
//
// 选中索引用 ListViewModel[int] 管理（索引列表），
// 移动/夹紧逻辑复用列表模型（已有单测覆盖）。
type Menu struct {
	config MenuConfig
	list   *ListViewModel[int]
	keys   bool    // 键位是否已注册（常驻 view 只注册一次）
	gui    GuiLike // Show 时保存，关闭时走真实 PopContext
}

// NewMenu 创建菜单组件。
func NewMenu(config MenuConfig) *Menu {
	idxs := make([]int, len(config.Items))
	for i := range idxs {
		idxs[i] = i
	}
	list := NewListViewModel[int]()
	list.SetItems(idxs)
	return &Menu{config: config, list: list}
}

// Show 显示菜单弹窗（常驻 view，无重建）。
func (m *Menu) Show(gui GuiLike) error {
	g := gui.GetGui()
	if err := m.ensureKeys(g); err != nil {
		return err
	}
	m.gui = gui
	x0, y0, x1, y1 := CenterRect(g, 40, len(m.config.Items)+2)
	v, err := ShowPopup(g, "menu", x0, y0, x1, y1, func(v *gocui.View) {
		v.Frame = true
		v.Title = m.config.Title
		v.Highlight = true
		v.SelBgColor = helpers.Theme.MenuSelectedBg
		v.SelFgColor = helpers.Theme.MenuSelectedFg
		v.Clear()
	})
	if err != nil {
		return err
	}
	m.list.ResetSelection()
	m.render(v)
	v.SetCursor(0, m.list.SelectedIndex())
	if err := gui.SetView("menu"); err != nil {
		return err
	}
	return gui.PushContext("menu")
}

// Hide 隐藏菜单（常驻 view）。
func (m *Menu) Hide(gui GuiLike) {
	HidePopup(gui.GetGui(), "menu")
}

// Selected 返回当前选中项的值。
func (m *Menu) Selected() string {
	i, ok := m.list.Selected()
	if !ok || i < 0 || i >= len(m.config.Items) {
		return ""
	}
	return m.config.Items[i].Value
}

// render 从选中索引渲染菜单项。
func (m *Menu) render(v *gocui.View) {
	sel := m.list.SelectedIndex()
	for i, item := range m.config.Items {
		if i == sel {
			fmt.Fprintln(v, "  "+helpers.Info(item.Display))
		} else {
			fmt.Fprintf(v, "  %s\n", item.Display)
		}
	}
}

// ensureKeys 幂等注册菜单键位（enter/esc/j/k/q/方向键）。
func (m *Menu) ensureKeys(g *gocui.Gui) error {
	if m.keys {
		return nil
	}
	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEnter, gocui.ModNone, m.handleSelect},
		{gocui.KeyEsc, gocui.ModNone, m.handleCancel},
		{'q', gocui.ModNone, m.handleCancel},
		{'j', gocui.ModNone, m.handleDown},
		{'k', gocui.ModNone, m.handleUp},
		{gocui.KeyArrowDown, gocui.ModNone, m.handleDown},
		{gocui.KeyArrowUp, gocui.ModNone, m.handleUp},
	}
	for _, b := range bindings {
		if err := g.SetKeybinding("menu", b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	m.keys = true
	return nil
}

func (m *Menu) handleSelect(g *gocui.Gui, v *gocui.View) error {
	selected := m.Selected()
	m.close()
	if m.config.OnDone != nil {
		m.config.OnDone(selected)
	}
	return nil
}

func (m *Menu) handleCancel(g *gocui.Gui, v *gocui.View) error {
	m.close()
	if m.config.OnCancel != nil {
		m.config.OnCancel()
	}
	return nil
}

// close 隐藏弹窗并真实弹栈（焦点恢复由 PopContext 负责）。
func (m *Menu) close() {
	if m.gui != nil {
		m.Hide(m.gui)
		_ = m.gui.PopContext()
	}
}

func (m *Menu) handleDown(g *gocui.Gui, v *gocui.View) error {
	m.list.Move(1)
	m.render(v)
	v.SetCursor(0, m.list.SelectedIndex())
	return nil
}

func (m *Menu) handleUp(g *gocui.Gui, v *gocui.View) error {
	m.list.Move(-1)
	m.render(v)
	v.SetCursor(0, m.list.SelectedIndex())
	return nil
}
