package components

import "testing"

func TestListViewModel_Empty(t *testing.T) {
	m := NewListViewModel[int]()
	if m.Len() != 0 {
		t.Errorf("expected Len=0, got %d", m.Len())
	}
	if m.SelectedIndex() != -1 {
		t.Errorf("expected SelectedIndex=-1, got %d", m.SelectedIndex())
	}
	if _, ok := m.Selected(); ok {
		t.Error("expected Selected ok=false on empty list")
	}
	if m.Select(0) {
		t.Error("expected Select(0) to fail on empty list")
	}
}

func TestListViewModel_SetItems(t *testing.T) {
	m := NewListViewModel[string]()
	m.SetItems([]string{"a", "b", "c"})

	if m.Len() != 3 {
		t.Fatalf("expected Len=3, got %d", m.Len())
	}
	if m.SelectedIndex() != 0 {
		t.Errorf("expected initial selection 0, got %d", m.SelectedIndex())
	}
	item, ok := m.Selected()
	if !ok || item != "a" {
		t.Errorf("expected Selected=a, got %q ok=%v", item, ok)
	}
}

func TestListViewModel_Move(t *testing.T) {
	m := NewListViewModel[int]()
	m.SetItems([]int{10, 20, 30})

	// 下移两格
	if !m.Move(1) {
		t.Error("expected Move(1) to change selection")
	}
	if m.SelectedIndex() != 1 {
		t.Errorf("expected idx=1, got %d", m.SelectedIndex())
	}
	if !m.Move(1) {
		t.Error("expected Move(1) to change selection")
	}
	if m.SelectedIndex() != 2 {
		t.Errorf("expected idx=2, got %d", m.SelectedIndex())
	}

	// 越界下移被夹住，不报错
	if m.Move(1) {
		t.Error("expected Move(1) past end to be clamped (no change)")
	}
	if m.SelectedIndex() != 2 {
		t.Errorf("expected idx stays 2, got %d", m.SelectedIndex())
	}

	// 上移越界被夹住
	if !m.Move(-5) {
		t.Error("expected Move(-5) to clamp to 0")
	}
	if m.SelectedIndex() != 0 {
		t.Errorf("expected idx=0, got %d", m.SelectedIndex())
	}
}

func TestListViewModel_Select(t *testing.T) {
	m := NewListViewModel[int]()
	m.SetItems([]int{1, 2, 3})

	if !m.Select(2) {
		t.Error("expected Select(2) ok")
	}
	if m.SelectedIndex() != 2 {
		t.Errorf("expected idx=2, got %d", m.SelectedIndex())
	}
	if m.Select(3) {
		t.Error("expected Select(3) to fail (out of range)")
	}
	if m.Select(-1) {
		t.Error("expected Select(-1) to fail")
	}
	if m.SelectedIndex() != 2 {
		t.Errorf("selection should be unchanged, got %d", m.SelectedIndex())
	}
}

func TestListViewModel_ResetSelection(t *testing.T) {
	m := NewListViewModel[int]()
	m.SetItems([]int{1, 2, 3})
	m.Select(2)
	m.ResetSelection()
	if m.SelectedIndex() != 0 {
		t.Errorf("expected idx=0 after reset, got %d", m.SelectedIndex())
	}
}
