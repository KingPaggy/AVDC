package components

import (
	"fmt"

	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

// ConfirmationConfig 定义确认弹窗的内容与回调。
type ConfirmationConfig struct {
	Title   string
	Message string
	OnYes   func()
	OnNo    func()
	// OnCancel 可空：Esc 取消时回调。
	OnCancel func()
}

// Confirmation 是通用确认弹窗组件（y/n/Esc）。
// 破坏性操作（如 organize 移动文件）前必须经它确认。
type Confirmation struct {
	config ConfirmationConfig
	keys   bool    // 键位是否已注册
	gui    GuiLike // Show 时保存，关闭时走真实 PopContext
}

// NewConfirmation 创建确认弹窗组件。
func NewConfirmation(config ConfirmationConfig) *Confirmation {
	return &Confirmation{config: config}
}

// Show 显示确认弹窗（常驻 view，无重建）。
func (c *Confirmation) Show(gui GuiLike) error {
	g := gui.GetGui()
	if err := c.ensureKeys(g); err != nil {
		return err
	}
	c.gui = gui
	x0, y0, x1, y1 := CenterRect(g, 50, 3)
	v, err := ShowPopup(g, "confirm", x0, y0, x1, y1,
		func(v *gocui.View) {
			v.Frame = true
			v.Title = c.config.Title
			v.Clear()
		})
	if err != nil {
		return err
	}
	fmt.Fprintln(v, c.config.Message)
	fmt.Fprint(v, "\n  "+helpers.Info("y")+" Yes  |  "+
		helpers.Error("n")+" No  |  "+
		helpers.Warning("Esc")+" Cancel")
	if err := gui.SetView("confirm"); err != nil {
		return err
	}
	return gui.PushContext("confirm")
}

// Hide 隐藏确认弹窗（常驻 view）。
func (c *Confirmation) Hide(gui GuiLike) {
	HidePopup(gui.GetGui(), "confirm")
}

// ensureKeys 幂等注册确认键位（y/n/enter/esc）。
func (c *Confirmation) ensureKeys(g *gocui.Gui) error {
	if c.keys {
		return nil
	}
	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{'y', gocui.ModNone, c.handleYes},
		{gocui.KeyEnter, gocui.ModNone, c.handleYes},
		{'n', gocui.ModNone, c.handleNo},
		{gocui.KeyEsc, gocui.ModNone, c.handleCancel},
	}
	for _, b := range bindings {
		if err := g.SetKeybinding("confirm", b.key, b.mod, b.handler); err != nil {
			return err
		}
	}
	c.keys = true
	return nil
}

func (c *Confirmation) handleYes(g *gocui.Gui, v *gocui.View) error {
	c.close()
	if c.config.OnYes != nil {
		c.config.OnYes()
	}
	return nil
}

func (c *Confirmation) handleNo(g *gocui.Gui, v *gocui.View) error {
	c.close()
	if c.config.OnNo != nil {
		c.config.OnNo()
	}
	return nil
}

func (c *Confirmation) handleCancel(g *gocui.Gui, v *gocui.View) error {
	c.close()
	if c.config.OnCancel != nil {
		c.config.OnCancel()
	}
	return nil
}

// close 隐藏弹窗并真实弹栈（焦点恢复由 PopContext 负责）。
func (c *Confirmation) close() {
	if c.gui != nil {
		c.Hide(c.gui)
		_ = c.gui.PopContext()
	}
}
