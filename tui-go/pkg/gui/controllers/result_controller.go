package controllers

import (
	"github.com/jesseduffield/gocui"
)

// ResultController handles result list interactions.
type ResultController struct {
	gui GUI
}

// Setup registers result-specific keybindings.
func (c *ResultController) Setup() error {
	g := c.gui.GetGui()
	v := "result"

	// Add list navigation
	listCtrl := NewListController(c.gui)
	if err := listCtrl.Setup(v); err != nil {
		return err
	}

	// Tab: toggle between success/failed (future feature)
	// For now just navigation
	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{'g', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			v.SetCursor(0, 0)
			v.SetOriginY(0)
			return nil
		}},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(v, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

// NewResultController creates a new result controller.
func NewResultController(g GUI) *ResultController {
	return &ResultController{gui: g}
}
