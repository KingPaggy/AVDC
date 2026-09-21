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
//
// vim 风格键（h/l/q 等）通过键位注册表可配置（用户
// tui.yml 覆盖）；方向键/Ctrl+C 等平台标准键固定绑定。
type Keybindings struct {
	gui *Gui
}

// setup 注册全局键位（非临时 view 集合）。
func (kb *Keybindings) setup() error {
	g := kb.gui.g
	keys := kb.gui.keys

	// 接收全局键位的 view（非临时 context 对应 view）
	views := []string{"files", "log", "result"}

	for _, vn := range views {
		// 焦点切换：方向键固定 + vim 键可配置
		if err := g.SetKeybinding(vn, gocui.KeyArrowLeft,
			gocui.ModNone, kb.focusPrev); err != nil {
			return err
		}
		if err := g.SetKeybinding(vn, gocui.KeyArrowRight,
			gocui.ModNone, kb.focusNext); err != nil {
			return err
		}
		if k := keys.Key("global.focusPrev"); k != nil {
			if err := g.SetKeybinding(vn, k, gocui.ModNone,
				kb.focusPrev); err != nil {
				return err
			}
		}
		if k := keys.Key("global.focusNext"); k != nil {
			if err := g.SetKeybinding(vn, k, gocui.ModNone,
				kb.focusNext); err != nil {
				return err
			}
		}
		// 退出：q 可配置 + Ctrl+C 固定双保险
		if k := keys.Key("global.quit"); k != nil {
			if err := g.SetKeybinding(vn, k, gocui.ModNone,
				kb.quit); err != nil {
				return err
			}
		}
		if err := g.SetKeybinding(vn, gocui.KeyCtrlC,
			gocui.ModNone, kb.quit); err != nil {
			return err
		}
		// 取消 / 返回（弹栈）：所有非临时 view 统一，
		// 包括 files（搜索已移至 PromptContext）
		if k := keys.Key("global.escape"); k != nil {
			if err := g.SetKeybinding(vn, k, gocui.ModNone,
				kb.escape); err != nil {
				return err
			}
		}
	}

	// log 面板滚动（files/result 由 ListController 提供
	// 模型导航，不在此重复注册）
	if err := g.SetKeybinding("log", gocui.KeyArrowDown,
		gocui.ModNone, kb.scrollDown); err != nil {
		return err
	}
	if err := g.SetKeybinding("log", gocui.KeyArrowUp,
		gocui.ModNone, kb.scrollUp); err != nil {
		return err
	}
	if k := keys.Key("log.scrollDown"); k != nil {
		if err := g.SetKeybinding("log", k, gocui.ModNone,
			kb.scrollDown); err != nil {
			return err
		}
	}
	if k := keys.Key("log.scrollUp"); k != nil {
		if err := g.SetKeybinding("log", k, gocui.ModNone,
			kb.scrollUp); err != nil {
			return err
		}
	}

	// log 顶部/底部：g/G 可配置，Home/End 固定。
	// g 暂停自动跟随（查看历史），G 恢复跟随。
	if k := keys.Key("log.top"); k != nil {
		if err := g.SetKeybinding("log", k, gocui.ModNone,
			kb.scrollTop); err != nil {
			return err
		}
	}
	if k := keys.Key("log.bottom"); k != nil {
		if err := g.SetKeybinding("log", k, gocui.ModNone,
			kb.scrollBottom); err != nil {
			return err
		}
	}
	if err := g.SetKeybinding("log", gocui.KeyHome, gocui.ModNone,
		kb.scrollTop); err != nil {
		return err
	}
	if err := g.SetKeybinding("log", gocui.KeyEnd, gocui.ModNone,
		kb.scrollBottom); err != nil {
		return err
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
		v.Autoscroll = false // 用户主动滚动：暂停跟随
		v.ScrollDown(1)
	}
	return nil
}

func (kb *Keybindings) scrollUp(g *gocui.Gui, v *gocui.View) error {
	if v != nil {
		v.Autoscroll = false // 用户主动滚动：暂停跟随
		v.ScrollUp(1)
	}
	return nil
}

// scrollTop 跳到日志顶部（暂停自动跟随）。
func (kb *Keybindings) scrollTop(g *gocui.Gui, v *gocui.View) error {
	if v != nil {
		v.Autoscroll = false
		v.SetOriginY(0)
	}
	return nil
}

// scrollBottom 跳到日志底部（恢复自动跟随）。
func (kb *Keybindings) scrollBottom(g *gocui.Gui, v *gocui.View) error {
	if v != nil {
		v.Autoscroll = true
	}
	return nil
}

func (kb *Keybindings) quit(g *gocui.Gui, v *gocui.View) error {
	return gocui.ErrQuit
}

func (kb *Keybindings) escape(g *gocui.Gui, v *gocui.View) error {
	return kb.gui.contexts.Pop()
}
