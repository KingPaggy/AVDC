package controllers

import (
	"fmt"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/helpers"
)

// ResultItem 表示结果列表中的一行。
type ResultItem struct {
	Line    string // 已含 [OK]/[FAIL] 前缀的完整行文本
	IsError bool   // 是否失败行（决定颜色）
}

// ResultController 管理结果列表：模型驱动渲染 + 列表导航。
type ResultController struct {
	gui   GUI
	items *components.ListViewModel[ResultItem]
}

// Setup registers result-specific keybindings.
func (c *ResultController) Setup() error {
	g := c.gui.GetGui()
	v := "result"

	// List navigation (bound to the result model)
	listCtrl := NewListController(c.gui, c.items)
	if err := listCtrl.Setup(v, c.items); err != nil {
		return err
	}

	// Additional result-specific bindings
	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		// Tab: toggle between success/failed (future feature)
		// 't' is reserved for result filtering (Phase 6)
	}

	for _, b := range bindings {
		if err := g.SetKeybinding(v, b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	return nil
}

// Append adds a result line and re-renders the view.
func (c *ResultController) Append(line string, color gocui.Attribute) error {
	c.items.SetItems(append(c.items.Items(), ResultItem{
		Line:    line,
		IsError: color != 0,
	}))
	return c.render()
}

// Clear empties the result list and the view.
func (c *ResultController) Clear() error {
	c.items.SetItems(nil)
	return c.render()
}

// render redraws the result view from the model.
func (c *ResultController) render() error {
	v, err := c.gui.GetView("result")
	if err != nil {
		return err
	}
	v.Clear()
	v.Title = "Result"
	for _, it := range c.items.Items() {
		if it.IsError {
			fmt.Fprintln(v, helpers.Error(it.Line))
		} else {
			fmt.Fprintln(v, helpers.Info(it.Line))
		}
	}
	return nil
}

// NewResultController creates a new result controller.
func NewResultController(g GUI) *ResultController {
	return &ResultController{
		gui:   g,
		items: components.NewListViewModel[ResultItem](),
	}
}
