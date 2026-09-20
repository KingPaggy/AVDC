package controllers

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/helpers"
	"avdc-tui/pkg/gui/types"
	"avdc-tui/pkg/python"

	"github.com/jesseduffield/gocui"
)

// GUI defines the minimal interface that controllers need from the GUI.
type GUI interface {
	SetView(name string) error
	GetView(name string) (*gocui.View, error)
	SetViewTitle(v *gocui.View, title string)
	GetScanDir() string
	SetScanDir(dir string)
	SetFileList(files []types.VideoFile)
	UpdateStatusReady(dir string, fileCount int)
	UpdateStatusScraping(current, total int, dir string)
	UpdateStatusDone(success, failed, total int, dir string)
	AppendLog(msg string, color gocui.Attribute) error
	AddResult(line string, color gocui.Attribute) error
	ClearResults()
	GetGui() *gocui.Gui
}

// scanCache holds cached scan results to avoid repeated Python subprocess calls.
type scanCache struct {
	mu        sync.Mutex
	dir       string
	files     []types.VideoFile
	timestamp time.Time
}

// FilesController handles file list interactions.
type FilesController struct {
	gui     GUI
	scraper *Scraper
	client  *python.Client
	cache   scanCache
	files   *components.ListViewModel[types.VideoFile]
}

// Setup registers file-specific keybindings.
func (c *FilesController) Setup() error {
	g := c.gui.GetGui()
	v := "files"

	// Add list navigation (bound to the list model)
	listCtrl := NewListController(c.gui, c.files)
	if err := listCtrl.Setup(v, c.files); err != nil {
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
	// Check cache first (30 second TTL)
	c.cache.mu.Lock()
	if c.cache.dir == dir && time.Since(c.cache.timestamp) < 30*time.Second {
		files := c.cache.files
		c.cache.mu.Unlock()
		return c.displayFiles(dir, files)
	}
	c.cache.mu.Unlock()

	// Show loading indicator
	v, _ := c.gui.GetView("files")
	v.Editable = false
	v.Clear()
	c.gui.SetViewTitle(v, "Scanning...")
	fmt.Fprintln(v, helpers.Warning("Scanning directory via Python core..."))

	// Run scan asynchronously
	go func() {
		result, err := c.client.Scan(dir)
		g := c.gui.GetGui()
		g.Update(func(g *gocui.Gui) error {
			if err != nil {
				return c.showError(err.Error())
			}

			// Convert Scan results to VideoFile
			files := make([]types.VideoFile, len(result.Files))
			for i, f := range result.Files {
				files[i] = types.VideoFile{
					Path:   f.File,
					Name:   f.Name,
					Number: f.Number,
				}
			}

			// Update cache
			c.cache.mu.Lock()
			c.cache.dir = dir
			c.cache.files = files
			c.cache.timestamp = time.Now()
			c.cache.mu.Unlock()

			return c.displayFiles(dir, files)
		})
	}()

	return nil
}

func (c *FilesController) displayFiles(dir string, files []types.VideoFile) error {
	v, _ := c.gui.GetView("files")
	v.Editable = false
	v.Clear()
	c.gui.SetViewTitle(v, "Files")

	if len(files) == 0 {
		fmt.Fprintln(v, helpers.Warning("No video files found"))
		return nil
	}

	// Update the list model (single source of truth)
	c.files.SetItems(files)
	c.gui.SetFileList(files)
	c.gui.UpdateStatusReady(dir, len(files))
	c.renderFileList(v)
	return nil
}

// renderFileList draws the file list from the list model.
func (c *FilesController) renderFileList(v *gocui.View) {
	for i, f := range c.files.Items() {
		icon := "[ ]"
		if f.Number != "" {
			icon = "[*]"
		}
		line := icon + " " + f.Name
		if f.Number != "" && f.Number != f.Name {
			line += "  (" + f.Number + ")"
		}
		if i == c.files.SelectedIndex() {
			fmt.Fprintln(v, helpers.Info(line))
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
	fmt.Fprintln(v, helpers.Error("Failed to scan directory:"))
	fmt.Fprintln(v, msg)
	fmt.Fprintln(v, helpers.Warning("Press 'r' or Enter to try another directory"))
	return nil
}

// NewFilesController creates a new files controller.
func NewFilesController(g GUI, s *Scraper) *FilesController {
	projectRoot := python.FindProjectRoot()
	client := python.NewClient(projectRoot)
	return &FilesController{
		gui:     g,
		scraper: s,
		client:  client,
		files:   components.NewListViewModel[types.VideoFile](),
	}
}
