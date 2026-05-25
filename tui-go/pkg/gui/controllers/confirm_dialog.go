package controllers

import (
	"fmt"

	"github.com/go-errors/errors"
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
	_, height := g.Size()
	y0 := height/2 - 1
	if y0 < 2 {
		y0 = 2
	}
	y1 := y0 + 3

	w := 50
	x0 := 15
	x1 := x0 + w

	g.DeleteView("confirm")
	v, err := g.SetView("confirm", x0, y0, x1, y1, 0)
	if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
		return err
	}
	v.Frame = true
	v.Title = "Confirm"
	v.Clear()
	fmt.Fprint(v, cd.message)
	fmt.Fprint(v, "\n\n  [green]y[/] Yes  |  [red]n[/] No  |  [yellow]Esc[/] Cancel")

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
	g := cd.gui.GetGui()
	g.DeleteView("confirm")

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
