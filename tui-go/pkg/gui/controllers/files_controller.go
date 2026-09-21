package controllers

import (
	"fmt"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/config"
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
	// 状态栏文本（供详情等临时提示）
	SetStatus(text string)
	AppendLog(msg string, color gocui.Attribute) error
	AddResult(line string, color gocui.Attribute) error
	ClearResults()
	GetGui() *gocui.Gui
	// 弹窗 context 栈操作（menu/confirm/help/config 接入）
	PushContext(name string) error
	PopContext() error
	// 键位注册表（用户配置合并后）
	GetKeys() *config.Registry
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
	gui         GUI
	scraper     *Scraper
	client      *python.Client
	projectRoot string
	cache       scanCache
	files       *components.ListViewModel[types.VideoFile]
	// 原始完整列表（搜索过滤时保留全量）
	allFiles []types.VideoFile
	// 多选状态（key = 文件 Path）
	marked map[string]bool
	// 刮削状态（key = 文件 Path）
	status   map[string]types.FileStatus
	statusMu sync.Mutex
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
		action  string
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{"files.refresh", c.handleRefresh},
		{"files.search", c.handleSearch},
		{"files.mark", c.handleToggleMark},
		{"files.markAll", c.handleToggleAll},
		{"files.scrape", c.handleScrape},
		{"files.organize", c.handleOrganize},
	}

	for _, b := range bindings {
		if k := c.gui.GetKeys().Key(b.action); k != nil {
			if err := g.SetKeybinding(v, k, gocui.ModNone,
				b.handler); err != nil {
				return err
			}
		}
	}

	// Enter 固定（核心动作）：弹刮削模式菜单。
	// esc 不再局部绑定，走全局 escape（弹栈）。
	if err := g.SetKeybinding(v, gocui.KeyEnter, gocui.ModNone,
		c.handleEnter); err != nil {
		return err
	}

	// x: cancel current scrape（files + log + result 全局语义）
	if err := g.SetKeybinding(v, 'x', gocui.ModNone,
		c.handleCancelScrape); err != nil {
		return err
	}
	if err := g.SetKeybinding("log", 'x', gocui.ModNone,
		c.handleCancelScrape); err != nil {
		return err
	}
	if err := g.SetKeybinding("result", 'x', gocui.ModNone,
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

// handleSearch /：弹搜索输入框（PromptContext），
// 输入实时过滤文件列表（不再用 files view 的 Editable 模式）。
func (c *FilesController) handleSearch(g *gocui.Gui, v *gocui.View) error {
	if len(c.allFiles) == 0 {
		return nil
	}
	prompt := components.NewPrompt(components.PromptConfig{
		Title:    "Search files",
		OnChange: c.applySearch,
		OnCancel: func() { c.applySearch("") },
	})
	return prompt.Show(c.gui)
}

// applySearch 按查询过滤列表并重渲染（输入回调）。
func (c *FilesController) applySearch(q string) {
	v, err := c.gui.GetView("files")
	if err != nil {
		return
	}
	var filtered []types.VideoFile
	ql := strings.ToLower(q)
	for _, f := range c.allFiles {
		if ql == "" || strings.Contains(strings.ToLower(f.Name), ql) {
			filtered = append(filtered, f)
		}
	}
	c.files.SetItems(filtered)
	c.gui.SetViewTitle(v, fmt.Sprintf("Files (%d/%d)",
		len(filtered), len(c.allFiles)))
	v.Clear()
	c.renderFileList(v)
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
	if c.gui.GetScanDir() == "" {
		return c.promptDir()
	}

	// Check if scrape is running
	if c.scraper != nil && c.scraper.GetState().IsRunning() {
		_ = c.gui.AppendLog("A task is already running (x to cancel)",
			helpers.LevelInfo)
		return nil
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
					_ = c.scraper.StartBatch(c.markedFiles(), 1)
				}
			case "2":
				_ = c.confirmOrganize()
			default:
				_ = c.startScrape(1)
			}
		},
	})
	return menu.Show(c.gui)
}

// handleScrape s：直接刮削当前目录（跳过菜单）。
func (c *FilesController) handleScrape(g *gocui.Gui, v *gocui.View) error {
	return c.startScrape(1)
}

// handleOrganize o：直接整理当前目录（破坏性操作，先确认）。
func (c *FilesController) handleOrganize(g *gocui.Gui, v *gocui.View) error {
	return c.confirmOrganize()
}

// startScrape 启动刮削/整理（mode 1=scrape, 2=organize）。
// 无扫描目录时先弹目录输入；任务运行中时忽略并提示。
func (c *FilesController) startScrape(mode int) error {
	if c.scraper == nil {
		return nil
	}
	dir := c.gui.GetScanDir()
	if dir == "" {
		return c.promptDir()
	}
	if c.scraper.GetState().IsRunning() {
		_ = c.gui.AppendLog("A task is already running (x to cancel)",
			helpers.LevelInfo)
		return nil
	}
	return c.scraper.StartScrape(dir, mode)
}

// confirmOrganize 弹整理确认（会重命名/移动文件，
// 必须经 Confirmation 二次确认）。
func (c *FilesController) confirmOrganize() error {
	dir := c.gui.GetScanDir()
	if dir == "" {
		return c.promptDir()
	}
	confirm := components.NewConfirmation(components.ConfirmationConfig{
		Title: "Confirm Organize",
		Message: "Organize will rename and move files under:\n  " +
			dir,
		OnYes: func() { _ = c.startScrape(2) },
	})
	return confirm.Show(c.gui)
}

// promptDir 弹目录输入弹窗（PromptContext，不再复用 files
// view）。默认值：已扫描目录 > config.ini 的 media_path。
func (c *FilesController) promptDir() error {
	prompt := components.NewPrompt(components.PromptConfig{
		Title:   "Directory to scan",
		Initial: c.defaultScanDir(),
		OnSubmit: func(value string) {
			if value == "" {
				return
			}
			c.gui.SetScanDir(value)
			_ = c.scanAndDisplay(value)
		},
	})
	return prompt.Show(c.gui)
}

// defaultScanDir 返回目录输入的默认值：优先当前已扫描
// 目录，其次 config.ini 的 common.media_path。
func (c *FilesController) defaultScanDir() string {
	if d := c.gui.GetScanDir(); d != "" {
		return d
	}
	if c.projectRoot == "" {
		return ""
	}
	data, err := readIniFile(filepath.Join(c.projectRoot, "config.ini"))
	if err != nil {
		return ""
	}
	if sec, ok := data["common"]; ok {
		return sec["media_path"]
	}
	return ""
}

func (c *FilesController) handleRefresh(g *gocui.Gui, v *gocui.View) error {
	dir := c.gui.GetScanDir()
	if dir == "" {
		return c.promptDir()
	}
	return c.scanAndDisplay(dir)
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

	// 新扫描：重置刮削状态表
	c.statusMu.Lock()
	c.status = make(map[string]types.FileStatus)
	c.statusMu.Unlock()

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
	c.statusMu.Lock()
	defer c.statusMu.Unlock()
	for i, f := range c.files.Items() {
		line := c.fileIcon(f.Path) + " " + f.Name
		if f.Number != "" && f.Number != f.Name {
			line += "  (" + f.Number + ")"
		}
		if i == c.files.SelectedIndex() {
			fmt.Fprintln(v, helpers.Info(line))
			continue
		}
		fmt.Fprintln(v, c.styleForStatus(f.Path, line))
	}
}

// fileIcon 返回文件行前缀：刮削状态优先，其次多选标记。
func (c *FilesController) fileIcon(path string) string {
	switch c.status[path] {
	case types.FileActive:
		return "[>]"
	case types.FileOK:
		return "[✓]"
	case types.FileFailed:
		return "[✗]"
	}
	if c.marked[path] {
		return "[x]"
	}
	return "[ ]"
}

// styleForStatus 按刮削状态着色（非选中行）。
func (c *FilesController) styleForStatus(path, line string) string {
	switch c.status[path] {
	case types.FileActive:
		return helpers.Warning(line)
	case types.FileOK:
		return helpers.Info(line)
	case types.FileFailed:
		return helpers.Error(line)
	}
	return line
}

// onFileStatus 接收刮削状态变更（可能来自子进程 goroutine），
// 更新状态表并在事件循环内重绘文件列表。
func (c *FilesController) onFileStatus(path string, st types.FileStatus) {
	c.statusMu.Lock()
	c.status[path] = st
	c.statusMu.Unlock()

	g := c.gui.GetGui()
	g.Update(func(*gocui.Gui) error {
		v, err := c.gui.GetView("files")
		if err != nil {
			return nil
		}
		v.Clear()
		c.renderFileList(v)
		return nil
	})
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
	fc := &FilesController{
		gui:         g,
		scraper:     s,
		client:      client,
		projectRoot: projectRoot,
		files:       components.NewListViewModel[types.VideoFile](),
		marked:      make(map[string]bool),
		status:      make(map[string]types.FileStatus),
	}
	// 注册文件状态钩子：刮削事件 → 列表行状态
	if s != nil {
		s.SetStatusHook(fc.onFileStatus)
	}
	return fc
}
