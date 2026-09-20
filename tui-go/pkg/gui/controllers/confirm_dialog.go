package controllers

import (
	"fmt"

	"avdc-tui/pkg/gui/helpers"

	"github.com/jesseduffield/gocui"
)

// ConfirmDialog shows a yes/no confirmation popup.
type ConfirmDialog struct {
	gui     GUI
	message string
	onYes   func()
	onNo    func()
}

// NewConfirmDialog creates a new confirmation dialog.
func NewConfirmDialog(g GUI, message string, onYes, onNo func()) *ConfirmDialog {
	return &ConfirmDialog{gui: g, message: message, onYes: onYes, onNo: onNo}
}

// Show displays the confirmation popup.
func (cd *ConfirmDialog) Show() error {
	g := cd.gui.GetGui()

	// Center the confirm dialog
	x0, y0, x1, y1 := centerRect(g, 50, 3)

	// Create/update the persistent confirm view
	v, err := showPopup(g, "confirm", x0, y0, x1, y1, func(v *gocui.View) {
		v.Frame = true
		v.Title = "Confirm"
		v.Clear()
	})
	if err != nil {
		return err
	}
	fmt.Fprint(v, cd.message)
	fmt.Fprint(v, "\n\n  "+helpers.Info("y")+
		" Yes  |  "+helpers.Error("n")+
		" No  |  "+helpers.Warning("Esc")+" Cancel")

	// Register keys
	bindings := []struct {
		key  interface{}
		mod  gocui.Modifier
		fn   func(*gocui.Gui, *gocui.View) error
	}{
		{'y', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return cd.dismiss("yes")
		}},
		{'n', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return cd.dismiss("no")
		}},
		{gocui.KeyEsc, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return cd.dismiss("cancel")
		}},
	}
	for _, b := range bindings {
		if err := g.SetKeybinding("confirm", b.key, b.mod, b.fn); err != nil {
			return err
		}
	}

	return cd.gui.SetView("confirm")
}

func (cd *ConfirmDialog) dismiss(action string) error {
	hidePopup(cd.gui.GetGui(), "confirm")

	switch action {
	case "yes":
		if cd.onYes != nil {
			cd.onYes()
		}
	case "no":
		if cd.onNo != nil {
			cd.onNo()
		}
	}
	return cd.gui.SetView("files")
}
