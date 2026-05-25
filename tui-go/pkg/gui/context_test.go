package gui

import (
	"testing"
)

func TestContextMgr_InitialContext(t *testing.T) {
	mgr := NewContextMgr(nil)
	cur := mgr.Current()
	if cur.Name != "files" {
		t.Errorf("expected initial context 'files', got %q", cur.Name)
	}
}

func TestContextMgr_Push(t *testing.T) {
	mgr := NewContextMgr(nil)
	// Push with nil gui will fail on SetView, but stack should still change
	// We test the stack logic separately
	mgr.Push("log")

	cur := mgr.Current()
	if cur.Name != "log" {
		t.Errorf("expected context 'log', got %q", cur.Name)
	}
}

func TestContextMgr_Pop(t *testing.T) {
	mgr := NewContextMgr(nil)
	mgr.Push("log")
	mgr.Push("result")

	if mgr.Current().Name != "result" {
		t.Errorf("expected 'result', got %q", mgr.Current().Name)
	}

	mgr.Pop()
	if mgr.Current().Name != "log" {
		t.Errorf("expected 'log' after pop, got %q", mgr.Current().Name)
	}

	mgr.Pop()
	if mgr.Current().Name != "files" {
		t.Errorf("expected 'files' after pop, got %q", mgr.Current().Name)
	}
}

func TestContextMgr_PopLastDoesNotRemoveRoot(t *testing.T) {
	mgr := NewContextMgr(nil)
	mgr.Pop() // Should be no-op when only root remains

	if mgr.Current().Name != "files" {
		t.Errorf("root context should not be popped, got %q", mgr.Current().Name)
	}
}

func TestContextMgr_Switch(t *testing.T) {
	mgr := NewContextMgr(nil)
	mgr.Push("log")
	mgr.Switch("result")

	cur := mgr.Current()
	if cur.Name != "result" {
		t.Errorf("expected 'result', got %q", cur.Name)
	}

	// Switch replaces the top, so Pop goes back to the one before log (files)
	mgr.Pop()
	if mgr.Current().Name != "files" {
		t.Errorf("expected 'files' after pop, got %q", mgr.Current().Name)
	}
}

func TestContextMgr_PushInvalidName(t *testing.T) {
	mgr := NewContextMgr(nil)
	mgr.Push("nonexistent")

	// Should remain on files since "nonexistent" doesn't exist
	if mgr.Current().Name != "files" {
		t.Errorf("expected 'files' after invalid push, got %q", mgr.Current().Name)
	}
}
