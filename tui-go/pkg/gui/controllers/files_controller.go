package controllers

import (
	"fmt"
	"strings"

	"avdc-tui/pkg/util"

	"github.com/jesseduffield/gocui"
)

// GUI defines the minimal interface that controllers need from the GUI.
type GUI interface {
	SetView(name string) error
	GetView(name string) (*gocui.View, error)
	SetViewTitle(v *gocui.View, title string)
	GetScanDir() string
	SetScanDir(dir string)
	SetFileList(files []util.VideoFile)
	UpdateStatusReady(dir string, fileCount int)
	UpdateStatusScraping(current, total int, dir string)
	UpdateStatusDone(success, failed, total int, dir string)
	AppendLog(msg string, color gocui.Attribute) error
	AddResult(line string, color gocui.Attribute) error
	ClearResults()
	GetGui() *gocui.Gui
}

// FilesController handles file list interactions.
type FilesController struct {
	gui     GUI
	scraper *Scraper
}

// Setup registers file-specific keybindings.
func (c *FilesController) Setup() error {
	g := c.gui.GetGui()
	v := "files"

	// Add list navigation
	listCtrl := NewListController(c.gui)
	if err := listCtrl.Setup(v); err != nil {
		return err
	}

	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEnter, gocui.ModNone, c.handleEnter},
		{'r', gocui.ModNone, c.handleRefresh},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(v, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

func (c *FilesController) handleEnter(g *gocui.Gui, v *gocui.View) error {
	if c.gui.GetScanDir() == "" {
		// In editable mode: read the input as directory path
		if v.Editable {
			return c.handlePathInput(v)
		}
		// Not editable: switch to input mode
		return c.promptDirectory(v)
	}

	// Check if scrape is running
	if c.scraper != nil && c.scraper.GetState().IsRunning() {
		return nil // Ignore Enter during scraping
	}

	// Show mode selection menu
	menuCtx := NewMenuContext(c.gui, "Scrape Mode", []MenuItem{
		{Display: "1 - Scrape (download metadata)", Value: "1"},
		{Display: "2 - Organize (rename & move)", Value: "2"},
	})
	mc := NewMenuController(c.gui, menuCtx, func(selected string) {
		mode := 1
		if selected == "2" {
			mode = 2
		}
		if c.scraper != nil {
			c.scraper.StartScrape(c.gui.GetScanDir(), mode)
		}
	})
	if err := mc.Setup(); err != nil {
		return err
	}
	return menuCtx.Show()
}

func (c *FilesController) handlePathInput(v *gocui.View) error {
	buf := v.TextArea.GetContent()
	buf = strings.TrimSpace(buf)
	if buf == "" {
		return nil
	}
	// Disable editing
	v.Editable = false
	v.ClearTextArea()
	c.gui.SetScanDir(buf)
	return c.scanAndDisplay(buf)
}

func (c *FilesController) handleRefresh(g *gocui.Gui, v *gocui.View) error {
	dir := c.gui.GetScanDir()
	if dir == "" {
		return c.promptDirectory(v)
	}
	return c.scanAndDisplay(dir)
}

func (c *FilesController) promptDirectory(v *gocui.View) error {
	v.Clear()
	v.Editable = true
	v.ClearTextArea()
	c.gui.SetViewTitle(v, "Enter directory path:")
	return nil
}

func (c *FilesController) scanAndDisplay(dir string) error {
	files, err := util.ScanDir(dir)
	if err != nil {
		return c.showError(err.Error())
	}

	v, _ := c.gui.GetView("files")
	v.Editable = false
	v.Clear()
	c.gui.SetViewTitle(v, "Files")

	if len(files) == 0 {
		fmt.Fprint(v, "[yellow]No video files found")
		return nil
	}

	c.gui.SetFileList(files)
	c.gui.UpdateStatusReady(dir, len(files))
	c.renderFileList(v, files)
	return nil
}

func (c *FilesController) renderFileList(v *gocui.View, files []util.VideoFile) {
	for i, f := range files {
		icon := "[ ]"
		if f.Number != "" {
			icon = "[*]"
		}
		line := icon + " " + f.Name
		if f.Number != "" && f.Number != f.Name {
			line += "  (" + f.Number + ")"
		}
		if i == 0 {
			fmt.Fprintf(v, "[green]%s[-]\n", line)
		} else {
			fmt.Fprintln(v, line)
		}
	}
}

func (c *FilesController) showError(msg string) error {
	v, _ := c.gui.GetView("files")
	v.Editable = false
	v.Clear()
	c.gui.SetViewTitle(v, "Error")
	fmt.Fprint(v, "[red]Failed to scan directory:\n\n")
	fmt.Fprintln(v, msg)
	fmt.Fprint(v, "\n[yellow]Press 'r' or Enter to try another directory")
	return nil
}

// NewFilesController creates a new files controller.
func NewFilesController(g GUI, s *Scraper) *FilesController {
	return &FilesController{gui: g, scraper: s}
}
