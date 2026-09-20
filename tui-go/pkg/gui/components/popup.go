package components

import (
	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"
)

// GuiLike 是弹窗组件依赖的 GUI 最小接口。
// controllers.GUI 与 gui.Gui 均满足，避免组件反向依赖
// controllers/gui 包（防循环 import）。
type GuiLike interface {
	GetGui() *gocui.Gui
	SetView(name string) error
	PushContext(name string) error
	PopContext() error
}

// showPopup 创建/更新弹窗 view 并置顶显示。
//
// 常驻策略：view 首次创建后复用，之后仅更新坐标与可见性
// （v.Visible），不 DeleteView 重建——避免闪烁与键位重注册。
func ShowPopup(g *gocui.Gui, name string, x0, y0, x1, y1 int,
	configure func(v *gocui.View)) (*gocui.View, error) {
	v, err := g.SetView(name, x0, y0, x1, y1, 0)
	if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
		return nil, err
	}
	if configure != nil {
		configure(v)
	}
	v.Visible = true
	if _, err := g.SetViewOnTop(name); err != nil {
		return nil, err
	}
	return v, nil
}

// hidePopup 隐藏弹窗 view（常驻保留，不删除）。
func HidePopup(g *gocui.Gui, name string) {
	if v, err := g.View(name); err == nil {
		v.Visible = false
	}
}

// centerRect 计算居中的弹窗区域（宽 w 高 h）。
func CenterRect(g *gocui.Gui, w, h int) (x0, y0, x1, y1 int) {
	gw, gh := g.Size()
	x0 = (gw - w) / 2
	if x0 < 0 {
		x0 = 0
	}
	y0 = (gh - h) / 2
	if y0 < 0 {
		y0 = 0
	}
	return x0, y0, x0 + w, y0 + h
}
