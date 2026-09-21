package controllers

import (
	"fmt"
	"strings"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/helpers"

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
	Name string
	Keys []HelpKey
}

// HelpKey represents a single keybinding entry.
// Action 非空时键位从注册表解析（跟随用户配置），
// 否则用固定的 Key 文本（弹窗通用键）。
type HelpKey struct {
	Action string
	Key    string
	Desc   string
}

// NewHelpPanel creates a new help panel.
// 键位表引用注册表 action，渲染时解析为当前键位
// （跟随用户配置，避免内容过期）。
func NewHelpPanel(g GUI) *HelpPanel {
	h := &HelpPanel{gui: g, visible: false, activeTab: 0}
	h.tabs = []HelpTab{
		{
			Name: "Global",
			Keys: []HelpKey{
				{Action: "global.focusPrev", Desc: "Focus previous panel"},
				{Action: "global.focusNext", Desc: "Focus next panel"},
				{Action: "global.help", Desc: "Toggle this help"},
				{Action: "global.config", Desc: "Edit config"},
				{Action: "global.quit", Desc: "Quit"},
				{Action: "global.escape", Desc: "Cancel / back"},
			},
		},
		{
			Name: "Files",
			Keys: []HelpKey{
				{Key: "Enter", Desc: "Menu: scrape / organize / batch"},
				{Action: "files.scrape", Desc: "Scrape now (skip menu)"},
				{Action: "files.organize",
					Desc: "Organize now (confirm)"},
				{Action: "files.search", Desc: "Search / filter"},
				{Action: "files.mark", Desc: "Mark / unmark file"},
				{Action: "files.markAll", Desc: "Mark all / none"},
				{Action: "files.refresh", Desc: "Rescan directory"},
				{Action: "files.cancel", Desc: "Cancel running task"},
			},
		},
		{
			Name: "Log",
			Keys: []HelpKey{
				{Action: "log.scrollDown", Desc: "Scroll down"},
				{Action: "log.scrollUp", Desc: "Scroll up"},
				{Action: "log.top", Desc: "Top (pause follow)"},
				{Action: "log.bottom", Desc: "Bottom (resume follow)"},
				{Action: "files.cancel", Desc: "Cancel running task"},
			},
		},
		{
			Name: "Result",
			Keys: []HelpKey{
				{Key: "Enter", Desc: "Show detail in status bar"},
				{Action: "result.filter",
					Desc: "Cycle filter: all / success / failed"},
				{Action: "files.cancel", Desc: "Cancel running task"},
			},
		},
		{
			Name: "Nav",
			Keys: []HelpKey{
				{Action: "list.down", Desc: "Move down"},
				{Action: "list.up", Desc: "Move up"},
				{Action: "list.home", Desc: "Go to top"},
				{Action: "list.end", Desc: "Go to bottom"},
				{Action: "list.pageUp", Desc: "Page up"},
				{Action: "list.pageDown", Desc: "Page down"},
			},
		},
		{
			Name: "Popups",
			Keys: []HelpKey{
				{Key: "Enter", Desc: "Confirm / submit"},
				{Key: "Esc", Desc: "Cancel / back"},
				{Key: "y / n", Desc: "Yes / no (confirm)"},
				{Key: "Ctrl+U", Desc: "Clear input"},
				{Key: "Tab", Desc: "Switch help category"},
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

	// Center the help panel
	x0, y0, x1, y1 := components.CenterRect(g, 55, 16)

	// Create/update the persistent help view
	v, err := components.ShowPopup(g, "help", x0, y0, x1, y1, func(v *gocui.View) {
		v.Frame = true
		v.Title = "Help - " + h.tabs[h.activeTab].Name
		v.Wrap = false
		v.Clear()
	})
	if err != nil {
		return err
	}

	h.renderTab(v)
	if err := h.gui.SetView("help"); err != nil {
		return err
	}
	return h.gui.PushContext("help")
}

// Hide hides the help popup (persistent view, no rebuild).
func (h *HelpPanel) Hide() error {
	h.visible = false
	components.HidePopup(h.gui.GetGui(), "help")
	return h.gui.PopContext()
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

	// Global ? to toggle help（files/log/result；键位可配置）
	bindGlobal := []struct {
		view string
		fn   func(*gocui.Gui, *gocui.View) error
	}{
		{"files", func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
		{"log", func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
		{"result", func(g *gocui.Gui, v *gocui.View) error { return h.Show() }},
	}
	if k := h.gui.GetKeys().Key("global.help"); k != nil {
		for _, b := range bindGlobal {
			if err := g.SetKeybinding(b.view, k, gocui.ModNone, b.fn); err != nil {
				return err
			}
		}
	}
	return nil
}

func (h *HelpPanel) renderTab(v *gocui.View) {
	tab := h.tabs[h.activeTab]
	keys := h.gui.GetKeys()

	// 解析显示键位（action → 当前键位，跟随用户配置）
	type row struct{ key, desc string }
	rows := make([]row, 0, len(tab.Keys))
	maxKeyLen := 0
	for _, k := range tab.Keys {
		key := k.Key
		if k.Action != "" {
			key = keys.String(k.Action)
		}
		if key == "" {
			continue
		}
		rows = append(rows, row{key: key, desc: k.Desc})
		if len(key) > maxKeyLen {
			maxKeyLen = len(key)
		}
	}
	for _, r := range rows {
		padding := strings.Repeat(" ", maxKeyLen-len(r.key)+2)
		fmt.Fprintf(v, "  %s%s %s\n", helpers.Warning(r.key),
			padding, r.desc)
	}
	fmt.Fprintln(v, "\n  "+helpers.Dim(
		"Tab: switch category  |  Esc: close"))
}
