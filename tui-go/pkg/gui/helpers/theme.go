// Package helpers 提供控制器间共享的辅助能力。
// theme.go 是颜色/样式唯一来源：所有 view 的颜色设置
// 必须引用 Theme 或 style 辅助，禁止散落的 gocui.ColorXxx。
package helpers

import "github.com/jesseduffield/gocui"

// ThemeConfig 定义 TUI 全局配色。
// 默认值沿用重构前观感（绿边框/蓝选中/青状态栏）。
// Phase 6 用户配置时改为实例注入（默认值 + 用户覆盖合并）。
type ThemeConfig struct {
	// 边框
	BorderFocused   gocui.Attribute // 焦点面板边框
	BorderUnfocused gocui.Attribute // 非焦点面板边框
	// 列表选中行
	SelectedBg gocui.Attribute
	SelectedFg gocui.Attribute
	// 菜单选中行
	MenuSelectedBg gocui.Attribute
	MenuSelectedFg gocui.Attribute
	// 状态/选项栏
	StatusBarFg  gocui.Attribute
	OptionsBarFg gocui.Attribute
}

// Default 是默认主题（唯一实例，全局引用）。
var Default = ThemeConfig{
	BorderFocused:   gocui.ColorGreen | gocui.AttrBold,
	BorderUnfocused: gocui.ColorDefault,
	SelectedBg:      gocui.ColorBlue,
	SelectedFg:      gocui.ColorWhite,
	MenuSelectedBg:  gocui.ColorGreen,
	MenuSelectedFg:  gocui.ColorBlack,
	StatusBarFg:     gocui.ColorCyan,
	OptionsBarFg:    gocui.ColorGreen,
}

// Theme 是包级默认主题的便捷别名（引用方式：
// helpers.Theme.BorderFocused）。
var Theme = &Default

// 事件级别（GUI 接口 color 参数语义）。
// AppendLog/AddResult 的 color 参数用这两个常量，
// 避免散落魔数 0/1。
const (
	LevelInfo  gocui.Attribute = 0
	LevelError gocui.Attribute = gocui.ColorRed
)
