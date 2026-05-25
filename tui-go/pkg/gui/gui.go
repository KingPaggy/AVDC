package gui

import (
	"avdc-tui/pkg/gui/controllers"
	"avdc-tui/pkg/util"
	"strconv"
	"sync"

	"github.com/jesseduffield/gocui"
)

// Gui wraps the gocui Gui object which handles rendering and events.
type Gui struct {
	g           *gocui.Gui
	version     string
	layout      *Layout
	views       *Views
	contexts    *ContextMgr
	keybindings *Keybindings
	scraper     *controllers.Scraper
	filesCtrl   *controllers.FilesController
	helpPanel   *controllers.HelpPanel
	configEdit  *controllers.ConfigEditor

	// State
	scanDir  string
	fileList []util.VideoFile
	mu       sync.Mutex
}

// New creates a new Gui instance.
func New(version string) (*Gui, error) {
	g := &Gui{}
	g.layout = &Layout{gui: g}
	g.views = &Views{}
	g.contexts = NewContextMgr(g)
	g.keybindings = &Keybindings{gui: g}
	return g, nil
}

// Run starts the GUI main loop.
func (g *Gui) Run() error {
	gui, err := gocui.NewGui(gocui.NewGuiOpts{
		OutputMode:      gocui.OutputTrue,
		SupportOverlaps: true,
	})
	if err != nil {
		return err
	}
	defer gui.Close()

	g.g = gui

	// Enable Highlight so SelFrameColor is used for the focused panel border.
	gui.Highlight = true

	// Border colors matching lazygit defaults:
	// - Inactive panels: default color (terminal adapts, typically gray/white)
	// - Active panel border: green + bold
	gui.FrameColor = gocui.ColorDefault
	gui.SelFrameColor = gocui.ColorGreen | gocui.AttrBold

	// Selection colors: SelBgColor/SelFgColor on the GUI level should stay
	// at default so the frame border itself has no background fill.
	// Each view sets its own SelBgColor/SelFgColor for the selected line.
	gui.SelBgColor = gocui.ColorDefault
	gui.SelFgColor = gocui.ColorDefault

	gui.SetManagerFunc(g.layout.layout)

	if err := g.createViews(); err != nil {
		return err
	}

	// Set initial focus to files view
	if _, err := g.g.SetCurrentView("files"); err != nil {
		return err
	}

	if err := g.setupKeybindings(); err != nil {
		return err
	}

	return gui.MainLoop()
}

// GetScanDir returns the currently scanned directory.
func (g *Gui) GetScanDir() string {
	g.mu.Lock()
	defer g.mu.Unlock()
	return g.scanDir
}

// SetScanDir sets the currently scanned directory.
func (g *Gui) SetScanDir(dir string) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.scanDir = dir
}

// GetFileList returns the current file list.
func (g *Gui) GetFileList() []util.VideoFile {
	g.mu.Lock()
	defer g.mu.Unlock()
	return g.fileList
}

// SetFileList sets the file list.
func (g *Gui) SetFileList(files []util.VideoFile) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.fileList = files
}

// createViews initializes all the views (panels).
func (g *Gui) createViews() error {
	return g.views.create(g.g)
}

// setupKeybindings registers all keyboard shortcuts.
func (g *Gui) setupKeybindings() error {
	if err := g.keybindings.setup(); err != nil {
		return err
	}
	// Create scraper
	g.scraper = controllers.NewScraper(g)
	// Register file-specific bindings
	g.filesCtrl = controllers.NewFilesController(g, g.scraper)
	if err := g.filesCtrl.Setup(); err != nil {
		return err
	}
	// Register result-specific bindings
	resultCtrl := controllers.NewResultController(g)
	if err := resultCtrl.Setup(); err != nil {
		return err
	}
	// Register help panel
	g.helpPanel = controllers.NewHelpPanel(g)
	if err := g.helpPanel.Setup(); err != nil {
		return err
	}
	// Register config editor
	g.configEdit = controllers.NewConfigEditor(g)
	return g.configEdit.Setup()
}

// SetView sets the current view for gocui input capture.
func (g *Gui) SetView(name string) error {
	_, err := g.g.SetCurrentView(name)
	return err
}

// GetView returns a view by name.
func (g *Gui) GetView(name string) (*gocui.View, error) {
	return g.g.View(name)
}

// getView (lowercase) for internal use.
func (g *Gui) getView(name string) (*gocui.View, error) {
	return g.g.View(name)
}

// SetViewTitle sets the frame title of a view.
func (g *Gui) SetViewTitle(v *gocui.View, title string) {
	v.Title = title
}

// UpdateStatusReady updates the status bar to ready state.
func (g *Gui) UpdateStatusReady(dir string, fileCount int) {
	v, err := g.getView("status")
	if err != nil {
		return
	}
	v.Clear()
	v.FgColor = gocui.ColorGreen
	v.WriteString("Ready  |  Path: " + dir + "  |  " +
		itoa(fileCount) + " files  |  Press Enter to scrape")
}

// UpdateStatusScraping updates the status bar during scraping.
func (g *Gui) UpdateStatusScraping(current, total int, dir string) {
	pct := 0
	if total > 0 {
		pct = current * 100 / total
	}
	v, err := g.getView("status")
	if err != nil {
		return
	}
	v.Clear()
	v.FgColor = gocui.ColorYellow
	v.WriteString("Scraping: " +
		itoa(current) + "/" + itoa(total) + " (" + itoa(pct) + "%)  |  Path: " + dir)
}

// UpdateStatusDone updates the status bar after scraping completes.
func (g *Gui) UpdateStatusDone(success, failed, total int, dir string) {
	v, err := g.getView("status")
	if err != nil {
		return
	}
	v.Clear()
	v.FgColor = gocui.ColorGreen
	v.WriteString("Done  |  " +
		itoa(total) + " total, " + itoa(success) + " success, " + itoa(failed) + " failed  |  Path: " + dir)
}

// AppendLog adds a line to the log view.
func (g *Gui) AppendLog(msg string, color gocui.Attribute) error {
	v, err := g.getView("log")
	if err != nil {
		return err
	}
	v.FgColor = color
	v.WriteString(msg + "\n")
	return nil
}

// AddResult adds a line to the result view.
func (g *Gui) AddResult(line string, color gocui.Attribute) error {
	v, err := g.getView("result")
	if err != nil {
		return err
	}
	v.FgColor = color
	v.WriteString(line + "\n")
	return nil
}

// ClearResults clears the result view.
func (g *Gui) ClearResults() {
	v, err := g.getView("result")
	if err != nil {
		return
	}
	v.Clear()
	v.FgColor = gocui.ColorGreen
	v.Title = "Result"
}

// GetGui returns the underlying gocui.Gui.
func (g *Gui) GetGui() *gocui.Gui {
	return g.g
}

func itoa(n int) string {
	return strconv.Itoa(n)
}
