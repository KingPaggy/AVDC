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
	// 弹窗 context 栈操作（menu/confirm/help/config 接入）
	PushContext(name string) error
	PopContext() error
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
	// 搜索状态
	allFiles     []types.VideoFile // 原始完整列表
	searchActive bool
	searchQuery  string
	// 多选状态（key = 文件 Path）
	marked map[string]bool
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
		{'/', gocui.ModNone, c.handleSearch},
		{' ', gocui.ModNone, c.handleToggleMark},
		{'a', gocui.ModNone, c.handleToggleAll},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(v, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}

	// files 专属 esc：搜索中取消搜索，否则弹栈回退
	// （全局 esc 不再绑定 files，见 keybindings.go）
	if err := g.SetKeybinding(v, gocui.KeyEsc, gocui.ModNone,
		c.handleEsc); err != nil {
		return err
	}

	// x: cancel current scrape（files + log 全局语义）
	if err := g.SetKeybinding(v, 'x', gocui.ModNone,
		c.handleCancelScrape); err != nil {
		return err
	}
	if err := g.SetKeybinding("log", 'x', gocui.ModNone,
		c.handleCancelScrape); err != nil {
		return err
	}
	return nil
}

// handleCancelScrape 取消当前刮削任务。
func (c *FilesController) handleCancelScrape(g *gocui.Gui, v *gocui.View) error {
	if c.scraper != nil {
		c.scraper.Cancel()
	}
	return nil
}

// --- 搜索过滤 ---

// searchEditor 包装默认编辑器，输入变化时回调过滤。
type searchEditor struct {
	onChanged func(query string)
}

func (e *searchEditor) Edit(v *gocui.View, key gocui.Key, ch rune,
	mod gocui.Modifier) bool {
	handled := gocui.DefaultEditor.Edit(v, key, ch, mod)
	if e.onChanged != nil {
		e.onChanged(v.TextArea.GetContent())
	}
	return handled
}

// handleSearch 进入搜索模式（/ 键）：view 可编辑，
// 输入实时过滤文件列表。
func (c *FilesController) handleSearch(g *gocui.Gui, v *gocui.View) error {
	if len(c.allFiles) == 0 {
		return nil
	}
	c.searchActive = true
	c.searchQuery = ""
	v.Editable = true
	v.Editor = &searchEditor{onChanged: c.applySearch}
	c.gui.SetViewTitle(v, "Search: ")
	v.Clear()
	v.SetCursor(0, 0)
	return nil
}

// applySearch 按查询过滤列表并重渲染（输入回调）。
func (c *FilesController) applySearch(q string) {
	c.searchQuery = q
	v, _ := c.gui.GetView("files")
	c.gui.SetViewTitle(v, "Search: "+q)

	var filtered []types.VideoFile
	ql := strings.ToLower(q)
	for _, f := range c.allFiles {
		if ql == "" || strings.Contains(strings.ToLower(f.Name), ql) {
			filtered = append(filtered, f)
		}
	}
	c.files.SetItems(filtered)
	v.Clear()
	c.renderFileList(v)
}

// handleEsc files 专属 esc：搜索中取消并恢复全部，
// 否则弹栈回退（与全局 esc 语义一致）。
func (c *FilesController) handleEsc(g *gocui.Gui, v *gocui.View) error {
	if c.searchActive {
		c.searchActive = false
		c.searchQuery = ""
		v.Editable = false
		c.files.SetItems(c.allFiles)
		v.Clear()
		c.renderFileList(v)
		c.gui.SetViewTitle(v, "Files")
		return nil
	}
	return c.gui.PopContext()
}

// --- 多选 ---

// handleToggleMark space：标记/取消当前选中文件。
func (c *FilesController) handleToggleMark(g *gocui.Gui, v *gocui.View) error {
	f, ok := c.files.Selected()
	if !ok {
		return nil
	}
	if c.marked[f.Path] {
		delete(c.marked, f.Path)
	} else {
		c.marked[f.Path] = true
	}
	v.Clear()
	c.renderFileList(v)
	return nil
}

// handleToggleAll a：全选/取消全选当前列表。
func (c *FilesController) handleToggleAll(g *gocui.Gui, v *gocui.View) error {
	items := c.files.Items()
	if len(items) == 0 {
		return nil
	}
	allMarked := true
	for _, f := range items {
		if !c.marked[f.Path] {
			allMarked = false
			break
		}
	}
	for _, f := range items {
		if allMarked {
			delete(c.marked, f.Path)
		} else {
			c.marked[f.Path] = true
		}
	}
	v.Clear()
	c.renderFileList(v)
	return nil
}

// markedFiles 返回已标记文件的路径列表（按原始列表顺序）。
func (c *FilesController) markedFiles() []string {
	var out []string
	for _, f := range c.allFiles {
		if c.marked[f.Path] {
			out = append(out, f.Path)
		}
	}
	return out
}

func (c *FilesController) handleEnter(g *gocui.Gui, v *gocui.View) error {
	// 搜索模式：Enter 确认搜索（退出输入，保留过滤）
	if c.searchActive {
		c.searchActive = false
		v.Editable = false
		return nil
	}

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

	// Show mode selection menu（含批量刮削项，有标记时）
	items := []components.MenuItem{
		{Display: "1 - Scrape (download metadata)", Value: "1"},
		{Display: "2 - Organize (rename & move)", Value: "2"},
	}
	if marked := c.markedFiles(); len(marked) > 0 {
		items = append(items, components.MenuItem{
			Display: fmt.Sprintf("3 - Batch scrape %d marked file(s)",
				len(marked)),
			Value: "3",
		})
	}
	menu := components.NewMenu(components.MenuConfig{
		Title: "Scrape Mode",
		Items: items,
		OnDone: func(selected string) {
			switch selected {
			case "3":
				if c.scraper != nil {
					c.scraper.StartBatch(c.markedFiles(), 1)
				}
			default:
				mode := 1
				if selected == "2" {
					mode = 2
				}
				if c.scraper != nil {
					c.scraper.StartScrape(c.gui.GetScanDir(), mode)
				}
			}
			// 焦点由 PopContext 切回 files
		},
		OnCancel: func() {
			// 焦点由 PopContext 切回 files
		},
	})
	return menu.Show(c.gui)
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
	c.allFiles = files
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
		if c.marked[f.Path] {
			icon = "[x]"
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
		marked:  make(map[string]bool),
	}
}
