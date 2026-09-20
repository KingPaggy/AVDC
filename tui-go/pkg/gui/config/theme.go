package config

import (
	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

// ApplyTheme 将主题配置应用到全局 helpers.Theme。
// 任一字段解析失败返回错误（该字段保持原值，前面字段已生效）。
func ApplyTheme(t ThemeConfig) error {
	fields := []struct {
		target *gocui.Attribute
		spec   string
	}{
		{&helpers.Theme.BorderFocused, t.BorderFocused},
		{&helpers.Theme.BorderUnfocused, t.BorderUnfocused},
		{&helpers.Theme.SelectedBg, t.SelectedBg},
		{&helpers.Theme.SelectedFg, t.SelectedFg},
		{&helpers.Theme.MenuSelectedBg, t.MenuSelectedBg},
		{&helpers.Theme.MenuSelectedFg, t.MenuSelectedFg},
		{&helpers.Theme.StatusBarFg, t.StatusBarFg},
		{&helpers.Theme.OptionsBarFg, t.OptionsBarFg},
	}
	for _, f := range fields {
		attr, err := ParseAttribute(f.spec)
		if err != nil {
			return err
		}
		*f.target = attr
	}
	return nil
}
