package context

import "testing"

func TestManager_InitialContext(t *testing.T) {
	m := NewManager(nil)
	if got := m.Current().Name; got != "files" {
		t.Errorf("expected initial context 'files', got %q", got)
	}
	if m.IsTemporary() {
		t.Error("files should not be temporary")
	}
}

func TestManager_Push(t *testing.T) {
	m := NewManager(nil)
	if err := m.Push("log"); err != nil {
		t.Fatalf("Push(log): %v", err)
	}
	if got := m.Current().Name; got != "log" {
		t.Errorf("expected 'log', got %q", got)
	}
}

func TestManager_PushDuplicateTop(t *testing.T) {
	m := NewManager(nil)
	m.Push("log")
	m.Push("log") // no-op
	if len(m.stack) != 2 {
		t.Errorf("expected stack depth 2, got %d", len(m.stack))
	}
}

func TestManager_Pop(t *testing.T) {
	m := NewManager(nil)
	m.Push("log")
	m.Push("result")
	m.Pop()
	if got := m.Current().Name; got != "log" {
		t.Errorf("expected 'log' after pop, got %q", got)
	}
	m.Pop()
	if got := m.Current().Name; got != "files" {
		t.Errorf("expected 'files' after pop, got %q", got)
	}
}

func TestManager_PopDoesNotRemoveRoot(t *testing.T) {
	m := NewManager(nil)
	if err := m.Pop(); err != nil {
		t.Fatalf("Pop on root: %v", err)
	}
	if got := m.Current().Name; got != "files" {
		t.Errorf("expected root 'files' preserved, got %q", got)
	}
}

func TestManager_Switch(t *testing.T) {
	m := NewManager(nil)
	m.Push("log")
	if err := m.Switch("result"); err != nil {
		t.Fatalf("Switch(result): %v", err)
	}
	if got := m.Current().Name; got != "result" {
		t.Errorf("expected 'result', got %q", got)
	}
	if len(m.stack) != 2 {
		t.Errorf("Switch should not change stack depth, got %d", len(m.stack))
	}
	// Pop 回到 files（switch 替换的是栈顶 log）
	m.Pop()
	if got := m.Current().Name; got != "files" {
		t.Errorf("expected 'files' after pop, got %q", got)
	}
}

func TestManager_PushInvalidName(t *testing.T) {
	m := NewManager(nil)
	if err := m.Push("nonexistent"); err == nil {
		t.Error("expected error for unknown context")
	}
}

func TestManager_TemporaryContexts(t *testing.T) {
	m := NewManager(nil)
	for _, name := range []string{"menu", "confirm", "prompt", "config", "help"} {
		if err := m.Push(name); err != nil {
			t.Fatalf("Push(%s): %v", name, err)
		}
		if !m.IsTemporary() {
			t.Errorf("context %q should be temporary", name)
		}
		m.Pop()
	}
}

func TestManager_FocusNextPrev(t *testing.T) {
	m := NewManager(nil)

	m.FocusNext() // files → log
	if got := m.Current().Name; got != "log" {
		t.Errorf("expected 'log', got %q", got)
	}
	m.FocusNext() // log → result
	if got := m.Current().Name; got != "result" {
		t.Errorf("expected 'result', got %q", got)
	}
	m.FocusNext() // result → files（循环）
	if got := m.Current().Name; got != "files" {
		t.Errorf("expected 'files' (wrap), got %q", got)
	}
	m.FocusPrev() // files → result
	if got := m.Current().Name; got != "result" {
		t.Errorf("expected 'result' (prev wrap), got %q", got)
	}
}

func TestManager_FocusFromTemporary(t *testing.T) {
	m := NewManager(nil)
	m.Push("menu")
	m.FocusNext() // 临时 context 下从 files 开始循环
	if got := m.Current().Name; got != "log" {
		t.Errorf("expected 'log' after focus from temporary, got %q", got)
	}
}

func TestManager_SideContexts(t *testing.T) {
	m := NewManager(nil)
	side := m.SideContexts()
	if len(side) != 3 {
		t.Fatalf("expected 3 side contexts, got %d", len(side))
	}
	for i, want := range []string{"files", "log", "result"} {
		if side[i].Name != want {
			t.Errorf("side[%d] = %q, want %q", i, side[i].Name, want)
		}
	}
}

// mockFocuser 记录 SetView 调用，验证焦点切换。
type mockFocuser struct {
	views []string
}

func (m *mockFocuser) SetView(name string) error {
	m.views = append(m.views, name)
	return nil
}

func TestManager_FocusCalls(t *testing.T) {
	f := &mockFocuser{}
	m := NewManager(f)

	m.Push("menu")
	if len(f.views) != 1 || f.views[0] != "menu" {
		t.Errorf("expected SetView(menu), got %v", f.views)
	}
	m.Pop()
	if len(f.views) != 2 || f.views[1] != "files" {
		t.Errorf("expected SetView(files) after pop, got %v", f.views)
	}
}
