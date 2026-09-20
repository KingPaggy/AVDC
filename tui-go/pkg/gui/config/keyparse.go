package config

import (
	"fmt"
	"strings"

	"github.com/jesseduffield/gocui"
)

// ParseKey 把键位字符串解析为 gocui key（rune 或 gocui.Key）。
//
// 支持语法：
//   - 单字符："q"、"j"、"/"
//   - 功能键："esc"、"enter"、"tab"、"space"、"backspace"、
//     "left"/"right"/"up"/"down"、"pgup"/"pgdn"、"home"、"end"、
//     "delete"
//   - 组合键："ctrl+c"、"ctrl+d" 等
func ParseKey(s string) (any, error) {
	switch strings.ToLower(s) {
	case "esc":
		return gocui.KeyEsc, nil
	case "enter":
		return gocui.KeyEnter, nil
	case "tab":
		return gocui.KeyTab, nil
	case "space":
		return ' ', nil
	case "backspace":
		return gocui.KeyBackspace, nil
	case "left":
		return gocui.KeyArrowLeft, nil
	case "right":
		return gocui.KeyArrowRight, nil
	case "up":
		return gocui.KeyArrowUp, nil
	case "down":
		return gocui.KeyArrowDown, nil
	case "pgup":
		return gocui.KeyPgup, nil
	case "pgdn":
		return gocui.KeyPgdn, nil
	case "home":
		return gocui.KeyHome, nil
	case "end":
		return gocui.KeyEnd, nil
	case "delete":
		return gocui.KeyDelete, nil
	}

	lower := strings.ToLower(s)
	if strings.HasPrefix(lower, "ctrl+") {
		ch := strings.TrimPrefix(lower, "ctrl+")
		// 全部字母 ctrl 组合（gocui KeyCtrlA=0x01 顺序递增）
		if len(ch) == 1 && ch >= "a" && ch <= "z" {
			return gocui.KeyCtrlA + gocui.Key(ch[0]-'a'), nil
		}
		return nil, fmt.Errorf("unsupported ctrl key: %s", s)
	}

	runes := []rune(s)
	if len(runes) == 1 {
		return runes[0], nil
	}
	return nil, fmt.Errorf("unknown key: %q", s)
}

// ParseAttribute 把颜色字符串解析为 gocui.Attribute。
//
// 支持空格分隔的多属性："green bold"、"default"、"red"。
// 颜色：black/red/green/yellow/blue/magenta/cyan/white/default；
// 修饰：bold/dim/reverse。
func ParseAttribute(s string) (gocui.Attribute, error) {
	var attr gocui.Attribute
	for _, part := range strings.Fields(s) {
		switch strings.ToLower(part) {
		case "default":
			attr |= gocui.ColorDefault
		case "black":
			attr |= gocui.ColorBlack
		case "red":
			attr |= gocui.ColorRed
		case "green":
			attr |= gocui.ColorGreen
		case "yellow":
			attr |= gocui.ColorYellow
		case "blue":
			attr |= gocui.ColorBlue
		case "magenta":
			attr |= gocui.ColorMagenta
		case "cyan":
			attr |= gocui.ColorCyan
		case "white":
			attr |= gocui.ColorWhite
		case "bold":
			attr |= gocui.AttrBold
		case "dim":
			attr |= gocui.AttrDim
		case "reverse":
			attr |= gocui.AttrReverse
		default:
			return 0, fmt.Errorf("unknown color/attribute: %q", part)
		}
	}
	return attr, nil
}
