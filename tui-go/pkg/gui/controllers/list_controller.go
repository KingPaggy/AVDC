package controllers

import (
	"github.com/jesseduffield/gocui"
)

// ListController provides common list navigation (j/k, g/G, scroll).
type ListController struct {
	gui GUI
}

// Setup registers navigation keybindings for the given view.
func (c *ListController) Setup(viewName string) error {
	g := c.gui.GetGui()

	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{'j', gocui.ModNone, c.HandleDown},
		{'k', gocui.ModNone, c.HandleUp},
		{gocui.KeyArrowDown, gocui.ModNone, c.HandleDown},
		{gocui.KeyArrowUp, gocui.ModNone, c.HandleUp},
		{'g', gocui.ModNone, c.HandleHome},
		{'G', gocui.ModNone, c.HandleEnd},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(viewName, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

// HandleDown moves the cursor/selection down one line.
func (c *ListController) HandleDown(g *gocui.Gui, v *gocui.View) error {
	_, cy := v.Cursor()
	if cy < 0 {
		v.SetCursor(0, 0)
	} else {
		v.SetCursor(0, cy+1)
	}
	return nil
}

// HandleUp moves the cursor/selection up one line.
func (c *ListController) HandleUp(g *gocui.Gui, v *gocui.View) error {
	_, cy := v.Cursor()
	if cy <= 0 {
		return nil
	}
	v.SetCursor(0, cy-1)
	return nil
}

// HandleHome moves cursor to the first line.
func (c *ListController) HandleHome(g *gocui.Gui, v *gocui.View) error {
	v.SetCursor(0, 0)
	v.SetOriginY(0)
	return nil
}

// HandleEnd moves cursor to the last line.
func (c *ListController) HandleEnd(g *gocui.Gui, v *gocui.View) error {
	v.Autoscroll = true
	return nil
}

// NewListController creates a new list controller.
func NewListController(g GUI) *ListController {
	return &ListController{gui: g}
}
