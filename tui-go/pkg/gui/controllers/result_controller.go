package controllers

import (
	"fmt"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/components"
	"avdc-tui/pkg/gui/helpers"
)

// ResultFilter 结果视图过滤模式。
type ResultFilter int

const (
	FilterAll ResultFilter = iota
	FilterSuccess
	FilterFailed
)

// ResultItem 表示结果列表中的一行。
type ResultItem struct {
	Line    string // 已含 [OK]/[FAIL] 前缀的完整行文本
	IsError bool   // 是否失败行（决定颜色）
}

// ResultController 管理结果列表：模型驱动渲染 + 列表导航 +
// 成功/失败过滤（t 键循环）。
type ResultController struct {
	gui    GUI
	items  *components.ListViewModel[ResultItem]
	filter ResultFilter
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
	if k := c.gui.GetKeys().Key("result.filter"); k != nil {
		// t: cycle result filter (all / success / failed)
		if err := g.SetKeybinding(v, k, gocui.ModNone,
			func(g *gocui.Gui, v *gocui.View) error {
				c.filter = (c.filter + 1) % 3
				return c.render()
			}); err != nil {
			return err
		}
	}

	// Enter: 在状态栏显示选中项全文（失败原因等）
	if err := g.SetKeybinding(v, gocui.KeyEnter, gocui.ModNone,
		c.handleDetail); err != nil {
		return err
	}
	return nil
}

// handleDetail Enter：在状态栏显示选中项全文。
func (c *ResultController) handleDetail(g *gocui.Gui,
	v *gocui.View) error {
	it, ok := c.items.Selected()
	if !ok {
		return nil
	}
	c.gui.SetStatus(helpers.Info("Detail") + "  |  " + it.Line)
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

// render redraws the result view from the model（按 filter 过滤）。
func (c *ResultController) render() error {
	v, err := c.gui.GetView("result")
	if err != nil {
		return err
	}
	v.Clear()
	v.Title = "Result [" + c.filterName() + "]"
	for _, it := range c.items.Items() {
		if !c.matchesFilter(it) {
			continue
		}
		if it.IsError {
			fmt.Fprintln(v, helpers.Error(it.Line))
		} else {
			fmt.Fprintln(v, helpers.Info(it.Line))
		}
	}
	return nil
}

// matchesFilter 判断结果行是否匹配当前过滤。
func (c *ResultController) matchesFilter(it ResultItem) bool {
	switch c.filter {
	case FilterSuccess:
		return !it.IsError
	case FilterFailed:
		return it.IsError
	default:
		return true
	}
}

// filterName 返回当前过滤的显示名。
func (c *ResultController) filterName() string {
	switch c.filter {
	case FilterSuccess:
		return "success"
	case FilterFailed:
		return "failed"
	default:
		return "all"
	}
}

// NewResultController creates a new result controller.
func NewResultController(g GUI) *ResultController {
	return &ResultController{
		gui:    g,
		items:  components.NewListViewModel[ResultItem](),
		filter: FilterAll,
	}
}
