package controllers

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/go-errors/errors"
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

// ReadConfig reads current values from config.ini.
func (ce *ConfigEditor) ReadConfig(configPath string) error {
	data, err := readIniFile(configPath)
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

// SaveConfig writes all fields back to config.ini.
func (ce *ConfigEditor) SaveConfig(configPath string) error {
	data, _ := readIniFile(configPath)
	if data == nil {
		data = make(map[string]map[string]string)
	}

	for _, f := range ce.fields {
		if _, ok := data[f.Section]; !ok {
			data[f.Section] = make(map[string]string)
		}
		data[f.Section][f.Key] = f.Value
	}

	return writeIniFile(configPath, data)
}

// Show displays the config editor.
func (ce *ConfigEditor) Show() error {
	ce.visible = true
	ce.curIdx = 0
	ce.defineFields()
	return nil
}

// Hide removes the config editor.
func (ce *ConfigEditor) Hide() error {
	ce.visible = false
	g := ce.gui.GetGui()
	g.DeleteView("config")
	return ce.gui.SetView("files")
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

	g.DeleteView("config")
	v, err := g.SetView("config", x0, y0, x1, y1, 0)
	if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
		return err
	}
	v.Frame = true
	v.Title = "Config Editor (s: save, Esc: close)"
	v.Wrap = false
	v.Clear()

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
			fmt.Fprintf(v, "\n  [cyan]-- %s --[-]\n", strings.ToUpper(f.Section))
			lineIdx++
		}

		masked := f.Value
		if f.Key == "api_key" && len(f.Value) > 8 {
			masked = f.Value[:4] + "****"
		}

		if i == ce.curIdx {
			fmt.Fprintf(v, "> [green]%s: %s[-]\n", f.Display, masked)
		} else {
			fmt.Fprintf(v, "  %s: %s\n", f.Display, masked)
		}
		lineIdx++
	}
	fmt.Fprintf(v, "\n  [dim]j/k: navigate | Enter: edit field | s: save | Esc: close[-]")
}

// Setup registers config editor keybindings.
func (ce *ConfigEditor) Setup() error {
	g := ce.gui.GetGui()

	// 'c' to open config editor
	bindings := []struct {
		view string
		key  interface{}
		mod  gocui.Modifier
		fn   func(*gocui.Gui, *gocui.View) error
	}{
		{"files", 'c', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return ce.ShowAndRender(g, v)
		}},
		{"log", 'c', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return ce.ShowAndRender(g, v)
		}},
		{"result", 'c', gocui.ModNone, func(g *gocui.Gui, v *gocui.View) error {
			return ce.ShowAndRender(g, v)
		}},
	}
	for _, b := range bindings {
		if err := g.SetKeybinding(b.view, b.key, b.mod, b.fn); err != nil {
			return err
		}
	}

	// Config view keybindings
	cfgBindings := []struct {
		key  interface{}
		mod  gocui.Modifier
		fn   func(*gocui.Gui, *gocui.View) error
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
			if err := ce.SaveConfig("config.ini"); err != nil {
				ce.gui.AppendLog("Config save failed: "+err.Error(), 1)
			} else {
				ce.gui.AppendLog("Config saved", 0)
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
	_ = ce.ReadConfig("config.ini") // ignore error, use defaults
	return ce.Render(g)
}

func (ce *ConfigEditor) promptEditField(g *gocui.Gui, v *gocui.View) error {
	if ce.curIdx >= len(ce.fields) {
		return nil
	}
	f := ce.fields[ce.curIdx]

	// Use a simple inline prompt via the view
	v.Clear()
	fmt.Fprintf(v, "Edit: %s\nCurrent: %s\nNew value: ", f.Display, f.Value)

	v.Editable = true
	v.ClearTextArea()

	// For simplicity, we'll use the existing gocui editor
	// User types value, presses Enter to confirm
	// We'll handle the actual value capture on next Enter
	v.Title = "Editing: " + f.Display + " (Enter to confirm, Esc to cancel)"

	// Register temporary edit-done handler
	return g.SetKeybinding("config", gocui.KeyEnter, gocui.ModNone,
		func(g2 *gocui.Gui, v2 *gocui.View) error {
			newVal := strings.TrimSpace(v2.TextArea.GetContent())
			v2.Editable = false
			v2.ClearTextArea()
			v2.Title = "Config Editor (s: save, Esc: close)"

			if newVal != "" {
				ce.fields[ce.curIdx].Value = newVal
			}
			return ce.Render(g2)
		})
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

// Itoa helper
func itoa(n int) string {
	return strconv.Itoa(n)
}
