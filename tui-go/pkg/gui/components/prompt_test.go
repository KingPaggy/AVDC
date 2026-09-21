package components

import "testing"

func TestPrompt_Config(t *testing.T) {
	p := NewPrompt(PromptConfig{
		Title:   "Directory",
		Initial: "/tmp",
	})
	if p.config.Title != "Directory" {
		t.Errorf("expected title 'Directory', got %q", p.config.Title)
	}
	if p.config.Initial != "/tmp" {
		t.Errorf("expected initial '/tmp', got %q", p.config.Initial)
	}
}

// TestPrompt_HideWithoutShow 验证未 Show 时 Hide 不 panic
// （gui 为 nil 的保护）。
func TestPrompt_HideWithoutShow(t *testing.T) {
	p := NewPrompt(PromptConfig{})
	p.Hide()
}

// TestMenu_CloseWithoutShow 验证未 Show 时 close 不 panic。
func TestMenu_CloseWithoutShow(t *testing.T) {
	m := NewMenu(MenuConfig{})
	m.close()
}

// TestConfirmation_CloseWithoutShow 验证未 Show 时 close
// 不 panic。
func TestConfirmation_CloseWithoutShow(t *testing.T) {
	c := NewConfirmation(ConfirmationConfig{})
	c.close()
}
