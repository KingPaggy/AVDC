package gui

import (
	"github.com/jesseduffield/gocui"
)

// Keybindings manages keyboard shortcut registration.
type Keybindings struct {
	gui *Gui
}

// setup registers all global keybindings.
func (kb *Keybindings) setup() error {
	g := kb.gui.g

	// Global bindings (active in any context)
	bindings := []struct {
		viewName string
		key      interface{}
		mod      gocui.Modifier
		handler  func(*gocui.Gui, *gocui.View) error
	}{
		// h / LeftArrow: focus previous panel
		{"", gocui.KeyArrowLeft, gocui.ModNone, kb.focusPrev},
		{"", 'h', gocui.ModNone, kb.focusPrev},

		// l / RightArrow: focus next panel
		{"", gocui.KeyArrowRight, gocui.ModNone, kb.focusNext},
		{"", 'l', gocui.ModNone, kb.focusNext},

		// j / DownArrow: scroll down
		{"", gocui.KeyArrowDown, gocui.ModNone, kb.scrollDown},
		{"", 'j', gocui.ModNone, kb.scrollDown},

		// k / UpArrow: scroll up
		{"", gocui.KeyArrowUp, gocui.ModNone, kb.scrollUp},
		{"", 'k', gocui.ModNone, kb.scrollUp},

		// q: quit
		{"", 'q', gocui.ModNone, kb.quit},

		// Ctrl+C: quit
		{"", gocui.KeyCtrlC, gocui.ModNone, kb.quit},

		// Escape: close popup / cancel
		{"", gocui.KeyEsc, gocui.ModNone, kb.escape},
	}

	for _, b := range bindings {
		var viewName = b.viewName
		if viewName == "" {
			// Global: bind to all views by binding to each individually
			views := []string{"files", "log", "result", "options", "status"}
			for _, vn := range views {
				if err := g.SetKeybinding(vn, b.key, b.mod, b.handler); err != nil {
					return err
				}
			}
		} else {
			if err := g.SetKeybinding(viewName, b.key, b.mod, b.handler); err != nil {
				return err
			}
		}
	}

	return nil
}

func (kb *Keybindings) focusPrev(g *gocui.Gui, v *gocui.View) error {
	kb.gui.contexts.FocusPrev()
	return nil
}

func (kb *Keybindings) focusNext(g *gocui.Gui, v *gocui.View) error {
	kb.gui.contexts.FocusNext()
	return nil
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
