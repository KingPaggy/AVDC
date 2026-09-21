package controllers

import (
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strconv"
	"strings"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/helpers"
	"avdc-tui/pkg/python"

	"github.com/jesseduffield/gocui"
)

// ConfigField represents a single editable config field.
type ConfigField struct {
	Section string
	Key     string
	Value   string
	Display string // human-readable label
}

// ConfigEditor manages the config editing UI.
type ConfigEditor struct {
	gui     GUI
	fields  []ConfigField
	curIdx  int
	visible bool
}

// NewConfigEditor creates a new config editor.
func NewConfigEditor(g GUI) *ConfigEditor {
	return &ConfigEditor{gui: g}
}

// defineFields specifies which config fields are editable.
func (ce *ConfigEditor) defineFields() {
	ce.fields = []ConfigField{
		// Common
		{Section: "common", Key: "main_mode", Display: "Main mode (1=scrape, 2=organize)"},
		{Section: "common", Key: "soft_link", Display: "Soft link (0=off, 1=on)"},
		{Section: "common", Key: "media_path", Display: "Media path"},
		{Section: "common", Key: "success_output_folder", Display: "Success output folder"},
		{Section: "common", Key: "failed_output_folder", Display: "Failed output folder"},
		// Proxy
		{Section: "proxy", Key: "proxy", Display: "Proxy URL"},
		{Section: "proxy", Key: "timeout", Display: "Timeout (seconds)"},
		{Section: "proxy", Key: "retry", Display: "Retry count"},
		// Name_Rule
		{Section: "Name_Rule", Key: "folder_name", Display: "Folder name rule"},
		{Section: "Name_Rule", Key: "naming_media", Display: "Media naming rule"},
		// Escape
		{Section: "escape", Key: "folders", Display: "Escape folders"},
		// Emby
		{Section: "emby", Key: "emby_url", Display: "Emby URL"},
		{Section: "emby", Key: "api_key", Display: "Emby API key"},
	}
}

// configPath 返回 config.ini 的绝对路径（项目根，
// 不依赖当前工作目录）。
func (ce *ConfigEditor) configPath() string {
	return filepath.Join(python.FindProjectRoot(), "config.ini")
}

// ReadConfig reads current values from config.ini.
func (ce *ConfigEditor) ReadConfig() error {
	data, err := readIniFile(ce.configPath())
	if err != nil {
		return err
	}
	for i := range ce.fields {
		f := &ce.fields[i]
		if sec, ok := data[f.Section]; ok {
			if val, ok2 := sec[f.Key]; ok2 {
				f.Value = val
			}
		}
	}
	return nil
}

// SaveConfig writes all fields back to config.ini，保留原文件
// 的注释、空行与键顺序（仅更新列出的键值）。
func (ce *ConfigEditor) SaveConfig() error {
	updates := make(map[string]map[string]string)
	for _, f := range ce.fields {
		if updates[f.Section] == nil {
			updates[f.Section] = make(map[string]string)
		}
		updates[f.Section][f.Key] = f.Value
	}
	return writeIniFilePreserving(ce.configPath(), updates)
}

// Show displays the config editor.
func (ce *ConfigEditor) Show() error {
	ce.visible = true
	ce.curIdx = 0
	ce.defineFields()
	return nil
}

// Hide hides the config editor (persistent view, no rebuild).
func (ce *ConfigEditor) Hide() error {
	ce.visible = false
	components.HidePopup(ce.gui.GetGui(), "config")
	return ce.gui.PopContext()
}

// Render draws the config editor to the view.
func (ce *ConfigEditor) Render(g *gocui.Gui) error {
	_, height := g.Size()
	y0 := 3
	y1 := height - 3
	if y1-y0 < 5 {
		return nil
	}
	w := 55
	x0 := 8
	x1 := x0 + w

	// Create/update the persistent config view
	v, err := components.ShowPopup(g, "config", x0, y0, x1, y1, func(v *gocui.View) {
		v.Frame = true
		v.Title = "Config Editor (s: save, Esc: close)"
		v.Wrap = false
		v.Clear()
	})
	if err != nil {
		return err
	}

	maxHeight := y1 - y0 - 2
	ce.renderContent(v, maxHeight)
	return ce.gui.SetView("config")
}

func (ce *ConfigEditor) renderContent(v *gocui.View, maxLines int) {
	currentSection := ""
	lineIdx := 0

	for i := 0; i < len(ce.fields); i++ {
		if lineIdx >= maxLines {
			break
		}
		f := ce.fields[i]

		// Section header
		if f.Section != currentSection {
			currentSection = f.Section
			fmt.Fprintln(v, "  "+helpers.Accent(
				"-- "+strings.ToUpper(f.Section)+" --"))
			lineIdx++
		}

		masked := f.Value
		if f.Key == "api_key" && len(f.Value) > 8 {
			masked = f.Value[:4] + "****"
		}

		if i == ce.curIdx {
			fmt.Fprintln(v, "> "+helpers.Info(
				f.Display+": "+masked))
		} else {
			fmt.Fprintf(v, "  %s: %s\n", f.Display, masked)
		}
		lineIdx++
	}
	fmt.Fprintln(v, "\n  "+helpers.Dim(
		"j/k: navigate | Enter: edit field | s: save | Esc: close"))
}

// Setup registers config editor keybindings.
func (ce *ConfigEditor) Setup() error {
	g := ce.gui.GetGui()

	// 'c' to open config editor（files/log/result；键位可配置）
	if k := ce.gui.GetKeys().Key("global.config"); k != nil {
		bindings := []struct {
			view string
			fn   func(*gocui.Gui, *gocui.View) error
		}{
			{"files", func(g *gocui.Gui, v *gocui.View) error {
				return ce.ShowAndRender(g, v)
			}},
			{"log", func(g *gocui.Gui, v *gocui.View) error {
				return ce.ShowAndRender(g, v)
			}},
			{"result", func(g *gocui.Gui, v *gocui.View) error {
				return ce.ShowAndRender(g, v)
			}},
		}
		for _, b := range bindings {
			if err := g.SetKeybinding(b.view, k, gocui.ModNone, b.fn); err != nil {
				return err
			}
		}
	}

	// Config view keybindings
	cfgBindings := []struct {
		key interface{}
		mod gocui.Modifier
		fn  func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEsc, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return ce.Hide()
		}},
		{'j', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			if ce.curIdx < len(ce.fields)-1 {
				ce.curIdx++
			}
			return ce.Render(g)
		}},
		{'k', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			if ce.curIdx > 0 {
				ce.curIdx--
			}
			return ce.Render(g)
		}},
		{gocui.KeyArrowDown, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			if ce.curIdx < len(ce.fields)-1 {
				ce.curIdx++
			}
			return ce.Render(g)
		}},
		{gocui.KeyArrowUp, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			if ce.curIdx > 0 {
				ce.curIdx--
			}
			return ce.Render(g)
		}},
		{gocui.KeyEnter, gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return ce.promptEditField(g, v)
		}},
		{'s', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			if err := ce.SaveConfig(); err != nil {
				ce.gui.AppendLog("Config save failed: "+err.Error(), helpers.LevelError)
			} else {
				ce.gui.AppendLog("Config saved", helpers.LevelInfo)
			}
			return ce.Hide()
		}},
	}
	for _, b := range cfgBindings {
		if err := g.SetKeybinding("config", b.key, b.mod, b.fn); err != nil {
			return err
		}
	}
	return nil
}

// ShowAndRender displays and renders the config editor.
func (ce *ConfigEditor) ShowAndRender(g *gocui.Gui, v *gocui.View) error {
	ce.Show()
	_ = ce.ReadConfig() // ignore error, use defaults
	if err := ce.gui.PushContext("config"); err != nil {
		return err
	}
	return ce.Render(g)
}

// promptEditField 弹输入弹窗编辑当前字段（PromptContext）。
// 不再复用 config view、不再临时重注册 Enter 键位。
func (ce *ConfigEditor) promptEditField(g *gocui.Gui, v *gocui.View) error {
	if ce.curIdx >= len(ce.fields) {
		return nil
	}
	idx := ce.curIdx
	f := ce.fields[idx]

	prompt := components.NewPrompt(components.PromptConfig{
		Title:   "Edit: " + f.Display,
		Initial: f.Value,
		OnSubmit: func(value string) {
			if value != "" {
				ce.fields[idx].Value = value
			}
			_ = ce.Render(g)
		},
		OnCancel: func() {
			_ = ce.Render(g)
		},
	})
	return prompt.Show(ce.gui)
}

// --- Minimal INI file reader/writer ---

func readIniFile(path string) (map[string]map[string]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	result := make(map[string]map[string]string)
	currentSection := "default"
	result[currentSection] = make(map[string]string)

	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, ";") {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			currentSection = line[1 : len(line)-1]
			if _, ok := result[currentSection]; !ok {
				result[currentSection] = make(map[string]string)
			}
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			result[currentSection][strings.TrimSpace(parts[0])] = strings.TrimSpace(parts[1])
		}
	}
	return result, nil
}

func writeIniFile(path string, data map[string]map[string]string) error {
	var sb strings.Builder
	sectionOrder := []string{"common", "proxy", "Name_Rule", "update", "log", "media", "escape", "debug_mode", "emby", "mark", "uncensored", "file_download", "extrafanart", "baidu"}

	for _, section := range sectionOrder {
		secData, ok := data[section]
		if !ok || len(secData) == 0 {
			continue
		}
		fmt.Fprintf(&sb, "[%s]\n", section)
		for k, v := range secData {
			fmt.Fprintf(&sb, "%s = %s\n", k, v)
		}
		fmt.Fprintln(&sb)
	}

	return os.WriteFile(path, []byte(sb.String()), 0644)
}

// writeIniFilePreserving 按行更新 INI：保留原文件的注释、
// 空行与键顺序，仅替换 updates 中列出的键值；缺失的键
// 追加到对应 section 末尾（section 不存在则新建）。
// 文件不存在时回退到 writeIniFile。
func writeIniFilePreserving(path string,
	updates map[string]map[string]string) error {
	original, err := os.ReadFile(path)
	if err != nil {
		return writeIniFile(path, updates)
	}
	lines := strings.Split(string(original), "\n")

	sectionEnd := map[string]int{} // section → 最后一行索引
	updated := map[string]map[string]bool{}
	current := ""
	for i, line := range lines {
		t := strings.TrimSpace(line)
		if strings.HasPrefix(t, "[") && strings.HasSuffix(t, "]") {
			current = t[1 : len(t)-1]
			sectionEnd[current] = i
			continue
		}
		if current != "" {
			sectionEnd[current] = i
		}
		k, ok := iniKey(t)
		if !ok || current == "" {
			continue
		}
		sec, ok := updates[current]
		if !ok {
			continue
		}
		val, ok := sec[k]
		if !ok {
			continue
		}
		indent := line[:len(line)-len(strings.TrimLeft(line, " \t"))]
		lines[i] = indent + k + " = " + val
		if updated[current] == nil {
			updated[current] = map[string]bool{}
		}
		updated[current][k] = true
	}

	// 未更新的键：追加到对应 section 末尾（从后往前插入）
	type insertion struct {
		idx  int
		text []string
	}
	var inserts []insertion
	for sec, kv := range updates {
		var missing []string
		for k, v := range kv {
			if !updated[sec][k] {
				missing = append(missing, k+" = "+v)
			}
		}
		if len(missing) == 0 {
			continue
		}
		slices.Sort(missing)
		if end, ok := sectionEnd[sec]; ok {
			inserts = append(inserts, insertion{idx: end + 1, text: missing})
		} else {
			inserts = append(inserts, insertion{
				idx:  len(lines),
				text: append([]string{"[" + sec + "]"}, missing...),
			})
		}
	}
	slices.SortFunc(inserts, func(a, b insertion) int {
		return b.idx - a.idx
	})
	for _, ins := range inserts {
		lines = slices.Insert(lines, ins.idx, ins.text...)
	}

	return os.WriteFile(path, []byte(strings.Join(lines, "\n")), 0644)
}

// iniKey 解析 "k = v" 行并返回键名。
func iniKey(line string) (string, bool) {
	if line == "" || strings.HasPrefix(line, "#") ||
		strings.HasPrefix(line, ";") || strings.HasPrefix(line, "[") {
		return "", false
	}
	parts := strings.SplitN(line, "=", 2)
	if len(parts) != 2 {
		return "", false
	}
	return strings.TrimSpace(parts[0]), true
}

// Itoa helper
func itoa(n int) string {
	return strconv.Itoa(n)
}
