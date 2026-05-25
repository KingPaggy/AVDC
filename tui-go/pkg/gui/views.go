package gui

import (
	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"
)

// Unicode box-drawing runes for panel borders (same as lazygit default)
var frameRunes = []rune{'─', '│', '┌', '┐', '└', '┘'}

// Views holds references to all named views.
type Views struct {
	Options *gocui.View
	Files   *gocui.View
	Log     *gocui.View
	Result  *gocui.View
	Status  *gocui.View
}

// create initializes all views with their properties.
func (vs *Views) create(g *gocui.Gui) error {
	viewNames := []string{"options", "files", "log", "result", "status"}
	for _, name := range viewNames {
		v, err := g.SetView(name, 0, 0, 10, 10, 0)
		if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
			return err
		}
		v.Wrap = true

		// Store references
		switch name {
		case "options":
			vs.Options = v
			v.Frame = false
			v.BgColor = gocui.ColorDefault
			v.FgColor = gocui.ColorGreen
		case "files":
			vs.Files = v
			v.Frame = true
			v.Title = "Files"
		case "log":
			vs.Log = v
			v.Frame = true
			v.Title = "Log"
		case "result":
			vs.Result = v
			v.Frame = true
			v.Title = "Result"
		case "status":
			vs.Status = v
			v.Frame = false
			v.BgColor = gocui.ColorDefault
			v.FgColor = gocui.ColorCyan
		}
	}

	// Apply common properties to all framed panels (like lazygit's configureViewProperties)
	for _, v := range []*gocui.View{vs.Files, vs.Log, vs.Result} {
		v.FrameRunes = frameRunes
		v.Highlight = true
		v.SelBgColor = gocui.ColorBlue
		v.SelFgColor = gocui.ColorWhite
	}

	return nil
}
