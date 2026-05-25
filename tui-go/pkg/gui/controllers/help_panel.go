package controllers

import (
	"fmt"
	"strings"

	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"
)

// HelpPanel displays keyboard shortcuts and usage.
type HelpPanel struct {
	gui       GUI
	visible   bool
	tabs      []HelpTab
	activeTab int
}

// HelpTab is a group of keybindings for the help panel.
type HelpTab struct {
	Name  string
	Keys  []HelpKey
}

// HelpKey represents a single keybinding entry.
type HelpKey struct {
	Key  string
	Desc string
}

// NewHelpPanel creates a new help panel.
func NewHelpPanel(g GUI) *HelpPanel {
	h := &HelpPanel{gui: g, visible: false, activeTab: 0}
	h.tabs = []HelpTab{
		{
			Name: "Global",
			Keys: []HelpKey{
				{Key: "h / Left", Desc: "Focus previous panel"},
				{Key: "l / Right", Desc: "Focus next panel"},
				{Key: "j / Down", Desc: "Scroll down"},
				{Key: "k / Up", Desc: "Scroll up"},
				{Key: "g", Desc: "Go to top"},
				{Key: "G", Desc: "Go to bottom"},
				{Key: "q", Desc: "Quit"},
				{Key: "?", Desc: "Toggle this help"},
				{Key: "Esc", Desc: "Close popup / cancel"},
			},
		},
		{
			Name: "Files",
			Keys: []HelpKey{
				{Key: "Enter", Desc: "Scan dir / Start scrape"},
				{Key: "r", Desc: "Refresh file list"},
			},
		},
		{
			Name: "Menu",
			Keys: []HelpKey{
				{Key: "Enter", Desc: "Confirm selection"},
				{Key: "j / k", Desc: "Navigate menu"},
				{Key: "Esc / q", Desc: "Cancel"},
			},
		},
	}
	return h
}

// Show displays the help popup.
func (h *HelpPanel) Show() error {
	if h.visible {
		return h.Hide()
	}
	h.visible = true

	g := h.gui.GetGui()
	_, height := g.Size()
	y0 := height/2 - 8
	if y0 < 2 {
		y0 = 2
	}
	y1 := y0 + 16

	w := 55
	x0 := 10
	x1 := x0 + w

	g.DeleteView("help")
	v, err := g.SetView("help", x0, y0, x1, y1, 0)
	if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
		return err
	}
	v.Frame = true
	v.Title = "Help - " + h.tabs[h.activeTab].Name
	v.Wrap = false
	v.Clear()

	h.renderTab(v)
	return h.gui.SetView("help")
}

// Hide removes the help popup.
func (h *HelpPanel) Hide() error {
	h.visible = false
	g := h.gui.GetGui()
	g.DeleteView("help")
	return h.gui.SetView("files")
}

// IsVisible returns whether the help panel is shown.
func (h *HelpPanel) IsVisible() bool {
	return h.visible
}

// CycleTab switches to the next help tab.
func (h *HelpPanel) CycleTab() {
	h.activeTab = (h.activeTab + 1) % len(h.tabs)
	if g := h.gui.GetGui(); g != nil {
		if v, err := g.View("help"); err == nil {
			v.Title = "Help - " + h.tabs[h.activeTab].Name
			v.Clear()
			h.renderTab(v)
		}
	}
}

// Setup registers help panel keybindings.
func (h *HelpPanel) Setup() error {
	g := h.gui.GetGui()

	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEsc, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Hide() }},
		{gocui.KeyEnter, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Hide() }},
		{'q', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Hide() }},
		{gocui.KeyTab, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { h.CycleTab(); return nil }},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding("help", b.key, b.mod, b.handler); err != nil {
			return err
		}
	}

	// Global ? to toggle help
	bindGlobal := []struct {
		view  string
		key   interface{}
		mod   gocui.Modifier
		fn    func(*gocui.Gui, *gocui.View) error
	}{
		{"files", '?', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
		{"log", '?', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
		{"result", '?', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
		{"status", '?', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
	}
	for _, b := range bindGlobal {
		if err := g.SetKeybinding(b.view, b.key, b.mod, b.fn); err != nil {
			return err
		}
	}
	return nil
}

func (h *HelpPanel) renderTab(v *gocui.View) {
	tab := h.tabs[h.activeTab]
	maxKeyLen := 0
	for _, k := range tab.Keys {
		if len(k.Key) > maxKeyLen {
			maxKeyLen = len(k.Key)
		}
	}
	for _, k := range tab.Keys {
		padding := strings.Repeat(" ", maxKeyLen-len(k.Key)+2)
		fmt.Fprintf(v, "  [yellow]%s[-]%s %s\n", k.Key, padding, k.Desc)
	}
	fmt.Fprint(v, "\n  [dim]Tab: switch category  |  Esc: close[-]")
}
