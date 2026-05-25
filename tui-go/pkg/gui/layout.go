package gui

import (
	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"
)

// Layout handles view positioning and resizing.
type Layout struct {
	gui *Gui
}

// layout is called on every screen re-render (e.g., resize).
func (l *Layout) layout(g *gocui.Gui) error {
	width, height := g.Size()

	topLines := 1
	bottomLines := 1

	// All views get frameOffset=1 (expand by 1 char each side).
	// Panels are spaced 1 char apart so their borders don't overlap:
	//   Files [0..W/4-1]  gap  Log [W/4+1..W/4+W/2]  gap  Result [W/4+W/2+1..W-2]
	filesWidth := width / 4
	logWidth := width / 2

	views := []struct {
		name            string
		x0, y0, x1, y1 int
	}{
		{"options", 0, 0, width, topLines},
		{"files", 0, topLines, filesWidth - 1, height - bottomLines - 1},
		{"log", filesWidth + 1, topLines, filesWidth + logWidth, height - bottomLines - 1},
		{"result", filesWidth + logWidth + 1, topLines, width - 2, height - bottomLines - 1},
		{"status", 0, height - bottomLines, width, height - 1},
	}

	for _, v := range views {
		frameOffset := 1
		_, err := g.SetView(v.name,
			v.x0-frameOffset, v.y0-frameOffset,
			v.x1+frameOffset, v.y1+frameOffset, 0)
		if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
			return err
		}
	}

	l.renderOptions()
	l.renderStatus()

	return nil
}

// renderOptions draws the top options bar.
func (l *Layout) renderOptions() {
	v, err := l.gui.getView("options")
	if err != nil {
		return
	}
	v.Clear()
	v.WriteString("j/k: Nav  |  h/l: Panel  |  Enter: Scrape  |  c: Config  |  q: Quit  |  ?: Help")
}

// renderStatus draws the bottom status bar.
func (l *Layout) renderStatus() {
	v, err := l.gui.getView("status")
	if err != nil {
		return
	}
	v.Clear()
	v.WriteString("Ready  |  Select a directory to begin  |  AVDC TUI v0.1.0")
}
