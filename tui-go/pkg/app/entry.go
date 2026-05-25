package app

import (
	"avdc-tui/pkg/gui"
)

// Start initializes and runs the TUI application.
func Start(info *BuildInfo) error {
	g, err := gui.New(info.Version)
	if err != nil {
		return err
	}
	return g.Run()
}
