package main

import (
	"avdc-tui/pkg/app"
	"fmt"
	"os"

	"github.com/jesseduffield/gocui"
)

const version = "0.1.0"

func main() {
	buildInfo := &app.BuildInfo{
		Version: version,
	}
	if err := app.Start(buildInfo); err != nil {
		if err == gocui.ErrQuit {
			os.Exit(0)
		}
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
