package controllers

import (
	"fmt"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

// MenuItem represents a selectable menu item.
type MenuItem struct {
	Display string
	Value   string
}

// MenuContext manages the popup menu state.
type MenuContext struct {
	gui     GUI
	items   []MenuItem
	highlit int
	title   string
}

// NewMenuContext creates a new menu context.
func NewMenuContext(g GUI, title string, items []MenuItem) *MenuContext {
	return &MenuContext{gui: g, items: items, highlit: 0, title: title}
}

// Show displays the menu popup.
func (mc *MenuContext) Show() error {
	g := mc.gui.GetGui()

	// Position menu in center of screen
	x0, y0, x1, y1 := centerRect(g, 40, len(mc.items)+2)

	// Create/update the persistent menu view
	v, err := showPopup(g, "menu", x0, y0, x1, y1, func(v *gocui.View) {
		v.Frame = true
		v.Title = mc.title
		v.Highlight = true
		v.SelBgColor = helpers.Theme.MenuSelectedBg
		v.SelFgColor = helpers.Theme.MenuSelectedFg
		v.Clear()
	})
	if err != nil {
		return err
	}

	// Render items
	mc.renderItems(v)
	mc.highlit = 0
	v.SetCursor(0, 0)

	return mc.gui.SetView("menu")
}

// Hide hides the menu popup (persistent view, no rebuild).
func (mc *MenuContext) Hide() error {
	hidePopup(mc.gui.GetGui(), "menu")
	return nil
}

// renderItems draws the menu items.
func (mc *MenuContext) renderItems(v *gocui.View) {
	for i, item := range mc.items {
		if i == mc.highlit {
			fmt.Fprintln(v, "  "+helpers.Info(item.Display))
		} else {
			fmt.Fprintf(v, "  %s\n", item.Display)
		}
	}
}

// Selected returns the currently highlighted item's value.
func (mc *MenuContext) Selected() string {
	if mc.highlit >= 0 && mc.highlit < len(mc.items) {
		return mc.items[mc.highlit].Value
	}
	return ""
}

// SelectedDisplay returns the currently highlighted item's display text.
func (mc *MenuContext) SelectedDisplay() string {
	if mc.highlit >= 0 && mc.highlit < len(mc.items) {
		return mc.items[mc.highlit].Display
	}
	return ""
}

// MenuController handles menu interactions.
type MenuController struct {
	gui    GUI
	ctx    *MenuContext
	onDone func(selected string)
}

// NewMenuController creates a new menu controller.
func NewMenuController(g GUI, ctx *MenuContext, onDone func(string)) *MenuController {
	return &MenuController{gui: g, ctx: ctx, onDone: onDone}
}

// Setup registers menu keybindings.
func (mc *MenuController) Setup() error {
	g := mc.gui.GetGui()

	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEnter, gocui.ModNone, mc.handleSelect},
		{gocui.KeyEsc, gocui.ModNone, mc.handleCancel},
		{'q', gocui.ModNone, mc.handleCancel},
		{'j', gocui.ModNone, mc.handleDown},
		{'k', gocui.ModNone, mc.handleUp},
		{gocui.KeyArrowDown, gocui.ModNone, mc.handleDown},
		{gocui.KeyArrowUp, gocui.ModNone, mc.handleUp},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding("menu", b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

func (mc *MenuController) handleSelect(g *gocui.Gui, v *gocui.View) error {
	selected := mc.ctx.Selected()
	mc.ctx.Hide()

	if mc.onDone != nil {
		mc.onDone(selected)
	}
	return nil
}

func (mc *MenuController) handleCancel(g *gocui.Gui, v *gocui.View) error {
	mc.ctx.Hide()
	// Return focus to files
	return mc.gui.SetView("files")
}

func (mc *MenuController) handleDown(g *gocui.Gui, v *gocui.View) error {
	if mc.ctx.highlit < len(mc.ctx.items)-1 {
		mc.ctx.highlit++
		mc.ctx.renderItems(v)
		v.SetCursor(0, mc.ctx.highlit)
	}
	return nil
}

func (mc *MenuController) handleUp(g *gocui.Gui, v *gocui.View) error {
	if mc.ctx.highlit > 0 {
		mc.ctx.highlit--
		mc.ctx.renderItems(v)
		v.SetCursor(0, mc.ctx.highlit)
	}
	return nil
}
