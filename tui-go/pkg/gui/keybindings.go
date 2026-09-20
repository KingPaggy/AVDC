package gui

import (
	"github.com/jesseduffield/gocui"
)

// Keybindings 管理按键注册。
//
// 注册原则：按键绑定到 context 对应的 view，不再重复绑到
// 所有面板。全局键位（焦点切换/退出/取消）绑到非临时
// view 集合（files/log/result）；弹窗 view 的键位由各自
// controller 注册——弹窗打开时全局键自动失效（gocui
// 只派发 current view 的键位）。
type Keybindings struct {
	gui *Gui
}

// setup 注册全局键位（非临时 view 集合）。
func (kb *Keybindings) setup() error {
	g := kb.gui.g

	// 接收全局键位的 view（非临时 context 对应 view）
	views := []string{"files", "log", "result"}

	global := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		// 焦点切换：h / LeftArrow
		{gocui.KeyArrowLeft, gocui.ModNone, kb.focusPrev},
		{'h', gocui.ModNone, kb.focusPrev},
		// 焦点切换：l / RightArrow
		{gocui.KeyArrowRight, gocui.ModNone, kb.focusNext},
		{'l', gocui.ModNone, kb.focusNext},
		// 退出
		{'q', gocui.ModNone, kb.quit},
		{gocui.KeyCtrlC, gocui.ModNone, kb.quit},
		// 取消 / 返回（弹栈）；files 的 esc 由 FilesController
		// 管理（搜索取消），不在此绑定
		{gocui.KeyEsc, gocui.ModNone, kb.escape},
	}
	for _, vn := range views {
		for _, b := range global {
			if b.key == gocui.KeyEsc && vn == "files" {
				continue // files 的 esc 由 FilesController 注册
			}
			if err := g.SetKeybinding(vn, b.key, b.mod, b.handler); err != nil {
				return err
			}
		}
	}

	// log 面板滚动（files/result 由 ListController 提供
	// 模型导航，不在此重复注册）
	logScroll := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyArrowDown, gocui.ModNone, kb.scrollDown},
		{'j', gocui.ModNone, kb.scrollDown},
		{gocui.KeyArrowUp, gocui.ModNone, kb.scrollUp},
		{'k', gocui.ModNone, kb.scrollUp},
	}
	for _, b := range logScroll {
		if err := g.SetKeybinding("log", b.key, b.mod, b.handler); err != nil {
			return err
		}
	}

	return nil
}

func (kb *Keybindings) focusPrev(g *gocui.Gui, v *gocui.View) error {
	return kb.gui.contexts.FocusPrev()
}

func (kb *Keybindings) focusNext(g *gocui.Gui, v *gocui.View) error {
	return kb.gui.contexts.FocusNext()
}

func (kb *Keybindings) scrollDown(g *gocui.Gui, v *gocui.View) error {
	if v != nil {
		v.ScrollDown(1)
	}
	return nil
}

func (kb *Keybindings) scrollUp(g *gocui.Gui, v *gocui.View) error {
	if v != nil {
		v.ScrollUp(1)
	}
	return nil
}

func (kb *Keybindings) quit(g *gocui.Gui, v *gocui.View) error {
	return gocui.ErrQuit
}

func (kb *Keybindings) escape(g *gocui.Gui, v *gocui.View) error {
	return kb.gui.contexts.Pop()
}
