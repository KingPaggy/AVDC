// Package config 加载用户配置（~/.config/avdc/tui.yml），
// 默认值与用户配置合并（lazygit config 模式）。
//
// 支持两项：theme（颜色覆盖）与 keybindings（动作键位覆盖）。
// 配置可热重载：重新调用 Load+Apply 即生效。
package config

import (
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// Config 用户可配置项。
type Config struct {
	Theme       ThemeConfig      `yaml:"theme"`
	Keybindings KeybindingConfig `yaml:"keybindings"`
}

// ThemeConfig 主题颜色（字符串形式，如 "green bold"）。
// 空字段表示使用默认值。
type ThemeConfig struct {
	BorderFocused   string `yaml:"borderFocused"`
	BorderUnfocused string `yaml:"borderUnfocused"`
	SelectedBg      string `yaml:"selectedBg"`
	SelectedFg      string `yaml:"selectedFg"`
	MenuSelectedBg  string `yaml:"menuSelectedBg"`
	MenuSelectedFg  string `yaml:"menuSelectedFg"`
	StatusBarFg     string `yaml:"statusBarFg"`
	OptionsBarFg    string `yaml:"optionsBarFg"`
}

// KeybindingConfig 键位覆盖（action → key string）。
// 未出现的 action 使用默认键位；空值表示保持默认。
// action 命名见 registry.go 的 DefaultKeybindings。
type KeybindingConfig map[string]string

// DefaultTheme 默认主题（与 helpers 包默认值一致）。
var DefaultTheme = ThemeConfig{
	BorderFocused:   "green bold",
	BorderUnfocused: "default",
	SelectedBg:      "blue",
	SelectedFg:      "white",
	MenuSelectedBg:  "green",
	MenuSelectedFg:  "black",
	StatusBarFg:     "cyan",
	OptionsBarFg:    "green",
}

// Load 加载用户配置。
// 配置文件不存在或解析失败时返回默认配置（不报错，
// 解析错误通过日志可见）。
func Load() (*Config, error) {
	cfg := &Config{Theme: DefaultTheme}

	path, err := configPath()
	if err != nil {
		return cfg, nil // 无法定位路径：用默认
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return cfg, nil // 文件不存在：用默认
	}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return cfg, err
	}
	cfg.fillThemeDefaults()
	return cfg, nil
}

// configPath 返回用户配置文件路径。
// 优先 $XDG_CONFIG_HOME/avdc/tui.yml，否则 ~/.config/avdc/tui.yml。
func configPath() (string, error) {
	if xdg := os.Getenv("XDG_CONFIG_HOME"); xdg != "" {
		return filepath.Join(xdg, "avdc", "tui.yml"), nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", "avdc", "tui.yml"), nil
}

// fillThemeDefaults 将空主题字段回填默认值。
func (c *Config) fillThemeDefaults() {
	d := DefaultTheme
	t := &c.Theme
	if t.BorderFocused == "" {
		t.BorderFocused = d.BorderFocused
	}
	if t.BorderUnfocused == "" {
		t.BorderUnfocused = d.BorderUnfocused
	}
	if t.SelectedBg == "" {
		t.SelectedBg = d.SelectedBg
	}
	if t.SelectedFg == "" {
		t.SelectedFg = d.SelectedFg
	}
	if t.MenuSelectedBg == "" {
		t.MenuSelectedBg = d.MenuSelectedBg
	}
	if t.MenuSelectedFg == "" {
		t.MenuSelectedFg = d.MenuSelectedFg
	}
	if t.StatusBarFg == "" {
		t.StatusBarFg = d.StatusBarFg
	}
	if t.OptionsBarFg == "" {
		t.OptionsBarFg = d.OptionsBarFg
	}
}
