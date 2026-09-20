// Package context 实现 Window/Context 三层中的 Context 层：
// context 绑定 view 与 window，是输入路由与焦点管理的入口。
package context

import "avdc-tui/pkg/gui/types"

// Context 表示一个可聚焦的逻辑面板。
// Name 是 context 标识；View 是对应 gocui view；Window 是
// 布局区域（弹窗无固定 window）；Kind 决定焦点行为。
type Context struct {
	Name   string
	View   string
	Window types.WindowName
	Kind   types.ContextKind
}

// IsTemporary 是否为临时弹窗 context（menu/confirm/...）。
func (c *Context) IsTemporary() bool {
	return c.Kind == types.ContextTemporary
}

// defineContexts 一次性定义全部 context（全局注册表）。
func defineContexts() map[string]*Context {
	return map[string]*Context{
		"files": {
			Name: "files", View: "files",
			Window: types.WindowFiles, Kind: types.ContextSide,
		},
		"log": {
			Name: "log", View: "log",
			Window: types.WindowMain, Kind: types.ContextMain,
		},
		"result": {
			Name: "result", View: "result",
			Window: types.WindowMain, Kind: types.ContextMain,
		},
		"menu": {
			Name: "menu", View: "menu",
			Kind: types.ContextTemporary,
		},
		"confirm": {
			Name: "confirm", View: "confirm",
			Kind: types.ContextTemporary,
		},
		"prompt": {
			Name: "prompt", View: "prompt",
			Kind: types.ContextTemporary,
		},
		"config": {
			Name: "config", View: "config",
			Kind: types.ContextTemporary,
		},
		"help": {
			Name: "help", View: "help",
			Kind: types.ContextTemporary,
		},
	}
}
