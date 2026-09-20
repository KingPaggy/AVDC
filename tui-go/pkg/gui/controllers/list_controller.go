package controllers

import (
	"github.com/jesseduffield/gocui"
)

// ListModel 是 ListController 依赖的列表模型接口。
// ListViewModel[T] 实现了该接口，作为选中状态的单一数据源。
type ListModel interface {
	Len() int
	SelectedIndex() int
	Select(idx int) bool
	Move(delta int) bool
}

// ListController 提供通用列表导航（j/k、g/G、翻页、方向键）。
// 导航操作更新模型选中索引，并同步 view cursor 作为视觉呈现。
type ListController struct {
	gui  GUI
	list ListModel
}

// Setup 为指定 view 注册导航键位。
// list 不能为 nil（调用方保证传入已初始化的模型）。
func (c *ListController) Setup(viewName string, list ListModel) error {
	g := c.gui.GetGui()

	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{'j', gocui.ModNone, c.HandleDown},
		{'k', gocui.ModNone, c.HandleUp},
		{gocui.KeyArrowDown, gocui.ModNone, c.HandleDown},
		{gocui.KeyArrowUp, gocui.ModNone, c.HandleUp},
		{'g', gocui.ModNone, c.HandleHome},
		{'G', gocui.ModNone, c.HandleEnd},
		{',', gocui.ModNone, c.HandlePageUp},
		{'.', gocui.ModNone, c.HandlePageDown},
		{gocui.KeyPgup, gocui.ModNone, c.HandlePageUp},
		{gocui.KeyPgdn, gocui.ModNone, c.HandlePageDown},
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(viewName, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

// syncCursor 将 view cursor 对齐到模型选中索引。
func (c *ListController) syncCursor(v *gocui.View) {
	idx := c.list.SelectedIndex()
	if idx < 0 {
		return
	}
	v.SetCursor(0, idx)
}

// HandleDown 下移一行（模型 + cursor 同步）。
func (c *ListController) HandleDown(g *gocui.Gui, v *gocui.View) error {
	if c.list.Move(1) {
		c.syncCursor(v)
	}
	return nil
}

// HandleUp 上移一行（模型 + cursor 同步）。
func (c *ListController) HandleUp(g *gocui.Gui, v *gocui.View) error {
	if c.list.Move(-1) {
		c.syncCursor(v)
	}
	return nil
}

// HandleHome 滚动到顶部。
func (c *ListController) HandleHome(g *gocui.Gui, v *gocui.View) error {
	if c.list.Select(0) {
		c.syncCursor(v)
	}
	v.SetOriginY(0)
	return nil
}

// HandleEnd 滚动到底部。
func (c *ListController) HandleEnd(g *gocui.Gui, v *gocui.View) error {
	if c.list.Select(c.list.Len() - 1) {
		c.syncCursor(v)
	}
	v.Autoscroll = true
	return nil
}

// HandlePageDown 下翻一页。
func (c *ListController) HandlePageDown(g *gocui.Gui, v *gocui.View) error {
	_, h := v.Size()
	step := h - 1
	if step < 1 {
		step = 1
	}
	for i := 0; i < step; i++ {
		if !c.list.Move(1) {
			break
		}
	}
	c.syncCursor(v)
	return nil
}

// HandlePageUp 上翻一页。
func (c *ListController) HandlePageUp(g *gocui.Gui, v *gocui.View) error {
	_, h := v.Size()
	step := h - 1
	if step < 1 {
		step = 1
	}
	for i := 0; i < step; i++ {
		if !c.list.Move(-1) {
			break
		}
	}
	c.syncCursor(v)
	return nil
}

// NewListController 创建列表导航控制器。
func NewListController(g GUI, list ListModel) *ListController {
	return &ListController{gui: g, list: list}
}
