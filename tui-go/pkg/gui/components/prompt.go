package components

import (
	"strings"

	"github.com/jesseduffield/gocui"
)

// PromptConfig 定义输入弹窗的标题、初始值与回调。
type PromptConfig struct {
	Title   string
	Initial string // 预填值（可为空）
	// OnChange 可空：输入变化时实时回调（如搜索过滤）。
	OnChange func(value string)
	// OnSubmit 提交回调（值为去首尾空白后的输入内容）。
	OnSubmit func(value string)
	// OnCancel 可空：Esc 取消时回调。
	OnCancel func()
}

// Prompt 是通用输入弹窗组件（Enter 提交 / Esc 取消 /
// Ctrl+U 清空）。常驻 view，无重建；与 Menu/Confirmation
// 共用弹窗约定（居中、常驻、Push/Pop context 栈）。
type Prompt struct {
	config PromptConfig
	keys   bool    // 键位是否已注册（常驻 view 只注册一次）
	gui    GuiLike // Show 时保存，关闭时走真实 PopContext
}

// NewPrompt 创建输入弹窗组件。
func NewPrompt(config PromptConfig) *Prompt {
	return &Prompt{config: config}
}

// Show 显示输入弹窗并聚焦（焦点由 PushContext 切换）。
func (p *Prompt) Show(gui GuiLike) error {
	g := gui.GetGui()
	if err := p.ensureKeys(g); err != nil {
		return err
	}
	p.gui = gui

	x0, y0, x1, y1 := CenterRect(g, 64, 5)
	_, err := ShowPopup(g, "prompt", x0, y0, x1, y1,
		func(v *gocui.View) {
			v.Frame = true
			v.Title = p.config.Title
			v.Wrap = false
			v.Editable = true
			if p.config.OnChange != nil {
				v.Editor = &onChangeEditor{
					onChanged: p.config.OnChange,
				}
			} else {
				// prompt view 常驻复用：显式恢复默认，
				// 避免残留上一次的 onChange 回调
				v.Editor = gocui.DefaultEditor
			}
			v.Clear()
			v.ClearTextArea()
			if p.config.Initial != "" {
				v.TextArea.TypeString(p.config.Initial)
			}
		})
	if err != nil {
		return err
	}
	if err := gui.SetView("prompt"); err != nil {
		return err
	}
	return gui.PushContext("prompt")
}

// Hide 隐藏输入弹窗（常驻 view，不删除）。
func (p *Prompt) Hide() {
	if p.gui != nil {
		HidePopup(p.gui.GetGui(), "prompt")
	}
}

// ensureKeys 幂等注册输入键位（enter/esc/ctrl+u）。
func (p *Prompt) ensureKeys(g *gocui.Gui) error {
	if p.keys {
		return nil
	}
	bindings := []struct {
		key     interface{}
		mod     gocui.Modifier
		handler func(*gocui.Gui, *gocui.View) error
	}{
		{gocui.KeyEnter, gocui.ModNone, p.handleSubmit},
		{gocui.KeyEsc, gocui.ModNone, p.handleCancel},
		{gocui.KeyCtrlU, gocui.ModNone, p.handleClear},
	}
	for _, b := range bindings {
		if err := g.SetKeybinding("prompt", b.key, b.mod,
			b.handler); err != nil {
			return err
		}
	}
	p.keys = true
	return nil
}

func (p *Prompt) handleSubmit(g *gocui.Gui, v *gocui.View) error {
	value := strings.TrimSpace(v.TextArea.GetContent())
	p.close()
	if p.config.OnSubmit != nil {
		p.config.OnSubmit(value)
	}
	return nil
}

func (p *Prompt) handleCancel(g *gocui.Gui, v *gocui.View) error {
	p.close()
	if p.config.OnCancel != nil {
		p.config.OnCancel()
	}
	return nil
}

// handleClear Ctrl+U：清空当前输入行。
func (p *Prompt) handleClear(g *gocui.Gui, v *gocui.View) error {
	v.ClearTextArea()
	v.Clear()
	return nil
}

// close 隐藏弹窗并真实弹栈（焦点恢复由 PopContext 负责）。
func (p *Prompt) close() {
	p.Hide()
	if p.gui != nil {
		_ = p.gui.PopContext()
	}
}

// onChangeEditor 包装默认编辑器，输入变化时回调（实时
// 过滤等场景）。
type onChangeEditor struct {
	onChanged func(content string)
}

func (e *onChangeEditor) Edit(v *gocui.View, key gocui.Key,
	ch rune, mod gocui.Modifier) bool {
	handled := gocui.DefaultEditor.Edit(v, key, ch, mod)
	if e.onChanged != nil {
		e.onChanged(v.TextArea.GetContent())
	}
	return handled
}
