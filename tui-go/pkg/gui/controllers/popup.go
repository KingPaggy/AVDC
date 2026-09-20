package controllers

import (
	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"
)

// showPopup 创建/更新弹窗 view 并置顶显示。
//
// 常驻策略：view 首次创建后复用，之后仅更新坐标与可见性
// （v.Visible），不 DeleteView 重建——避免闪烁与键位重注册。
// 隐藏用 hidePopup；显隐由 controller 控制，布局回调不参与。
func showPopup(g *gocui.Gui, name string, x0, y0, x1, y1 int,
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
func hidePopup(g *gocui.Gui, name string) {
	if v, err := g.View(name); err == nil {
		v.Visible = false
	}
}
