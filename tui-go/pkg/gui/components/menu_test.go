package components

import "testing"

func TestMenu_InitialSelection(t *testing.T) {
	m := NewMenu(MenuConfig{
		Title: "Test",
		Items: []MenuItem{
			{Display: "A", Value: "a"},
			{Display: "B", Value: "b"},
		},
	})
	if got := m.Selected(); got != "a" {
		t.Errorf("expected initial selection 'a', got %q", got)
	}
}

func TestMenu_Empty(t *testing.T) {
	m := NewMenu(MenuConfig{})
	if got := m.Selected(); got != "" {
		t.Errorf("expected empty selection, got %q", got)
	}
}

func TestMenu_SingleItem(t *testing.T) {
	m := NewMenu(MenuConfig{
		Items: []MenuItem{{Display: "Only", Value: "1"}},
	})
	if got := m.Selected(); got != "1" {
		t.Errorf("expected '1', got %q", got)
	}
}

func TestConfirmation_Config(t *testing.T) {
	c := NewConfirmation(ConfirmationConfig{
		Title:   "Confirm",
		Message: "Do it?",
	})
	if c.config.Title != "Confirm" {
		t.Errorf("expected title 'Confirm', got %q", c.config.Title)
	}
	if c.config.Message != "Do it?" {
		t.Errorf("expected message 'Do it?', got %q", c.config.Message)
	}
}
