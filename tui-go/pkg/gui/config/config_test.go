package config

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

func TestParseKey(t *testing.T) {
	tests := []struct {
		input string
		want  any
	}{
		{"q", 'q'},
		{"/", '/'},
		{"esc", gocui.KeyEsc},
		{"enter", gocui.KeyEnter},
		{"space", ' '},
		{"left", gocui.KeyArrowLeft},
		{"pgup", gocui.KeyPgup},
		{"ctrl+c", gocui.KeyCtrlC},
		{"ctrl+r", gocui.KeyCtrlR},
		{"ctrl+z", gocui.KeyCtrlZ},
		{"ctrl+u", gocui.KeyCtrlU},
		{"home", gocui.KeyHome},
	}
	for _, tt := range tests {
		got, err := ParseKey(tt.input)
		if err != nil {
			t.Errorf("ParseKey(%q): %v", tt.input, err)
			continue
		}
		if got != tt.want {
			t.Errorf("ParseKey(%q) = %v, want %v", tt.input, got, tt.want)
		}
	}
}

func TestParseKey_Invalid(t *testing.T) {
	for _, input := range []string{"", "abc", "ctrl+", "shift+x"} {
		if _, err := ParseKey(input); err == nil {
			t.Errorf("ParseKey(%q): expected error", input)
		}
	}
}

func TestParseAttribute(t *testing.T) {
	attr, err := ParseAttribute("green bold")
	if err != nil {
		t.Fatalf("ParseAttribute: %v", err)
	}
	want := gocui.ColorGreen | gocui.AttrBold
	if attr != want {
		t.Errorf("attr = %v, want %v", attr, want)
	}

	attr, err = ParseAttribute("default")
	if err != nil || attr != gocui.ColorDefault {
		t.Errorf("default attr = %v (err %v)", attr, err)
	}

	if _, err := ParseAttribute("neon"); err == nil {
		t.Error("expected error for unknown color")
	}
}

func TestRegistry_Merge(t *testing.T) {
	r := NewRegistry(KeybindingConfig{
		"global.quit": "Q",       // 覆盖
		"files.refresh": "ctrl+r", // 覆盖
		"unknown.action": "x",     // 未知 action：忽略
		"list.down": "",           // 空值：保持默认
	})

	if got := r.Key("global.quit"); got != 'Q' {
		t.Errorf("global.quit = %v, want 'Q'", got)
	}
	if got := r.Key("files.refresh"); got != gocui.KeyCtrlR {
		t.Errorf("files.refresh = %v, want ctrl+r", got)
	}
	if got := r.Key("unknown.action"); got != nil {
		t.Errorf("unknown action should return nil, got %v", got)
	}
	if got := r.Key("list.down"); got != 'j' {
		t.Errorf("list.down (empty override) = %v, want 'j'", got)
	}
}

func TestRegistry_InvalidOverrideFallsBack(t *testing.T) {
	r := NewRegistry(KeybindingConfig{
		"global.quit": "boguskey",
	})
	// 解析失败回退默认 q
	if got := r.Key("global.quit"); got != 'q' {
		t.Errorf("global.quit = %v, want fallback 'q'", got)
	}
}

func TestLoad_WithConfigFile(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", dir)
	cfgDir := filepath.Join(dir, "avdc")
	os.MkdirAll(cfgDir, 0755)
	content := `theme:
  borderFocused: "yellow bold"
keybindings:
  global.quit: "Q"
`
	if err := os.WriteFile(filepath.Join(cfgDir, "tui.yml"),
		[]byte(content), 0644); err != nil {
		t.Fatal(err)
	}

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.Theme.BorderFocused != "yellow bold" {
		t.Errorf("borderFocused = %q, want yellow bold",
			cfg.Theme.BorderFocused)
	}
	// 未配置字段回填默认
	if cfg.Theme.SelectedBg != "blue" {
		t.Errorf("selectedBg = %q, want default blue",
			cfg.Theme.SelectedBg)
	}
	if cfg.Keybindings["global.quit"] != "Q" {
		t.Errorf("global.quit = %q, want Q",
			cfg.Keybindings["global.quit"])
	}
}

func TestLoad_NoFileReturnsDefaults(t *testing.T) {
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.Theme.BorderFocused != DefaultTheme.BorderFocused {
		t.Error("expected default theme without config file")
	}
}

func TestLoad_InvalidYAMLReturnsError(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", dir)
	cfgDir := filepath.Join(dir, "avdc")
	os.MkdirAll(cfgDir, 0755)
	os.WriteFile(filepath.Join(cfgDir, "tui.yml"),
		[]byte("not: [valid yaml"), 0644)

	if _, err := Load(); err == nil {
		t.Error("expected error for invalid YAML")
	}
}

func TestApplyTheme(t *testing.T) {
	// 先应用一套主题
	err := ApplyTheme(ThemeConfig{
		BorderFocused: "red bold",
		SelectedBg:    "magenta",
	})
	if err != nil {
		t.Fatalf("ApplyTheme: %v", err)
	}
	if helpers.Theme.BorderFocused != gocui.ColorRed|gocui.AttrBold {
		t.Errorf("BorderFocused = %v, want red bold",
			helpers.Theme.BorderFocused)
	}
	if helpers.Theme.SelectedBg != gocui.ColorMagenta {
		t.Errorf("SelectedBg = %v, want magenta",
			helpers.Theme.SelectedBg)
	}

	// 恢复默认（避免影响其他测试）
	ApplyTheme(DefaultTheme)
}
