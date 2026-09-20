package commands

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

// writeMockCLI 生成一个模拟 cli.py 的 Python 脚本。
// mode=normal：输出完整事件流（log/progress/success/done）
// 并在 stderr 打印一行非 JSON；mode=sleep：持续输出
// progress 并 sleep（用于取消测试）。
func writeMockCLI(t *testing.T, mode string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "mock_cli.py")

	var src string
	if mode == "sleep" {
		src = `import json, sys, time
for i in range(100):
    print(json.dumps({"type": "progress", "current": i, "total": 100}), flush=True)
    time.sleep(0.2)
`
	} else {
		src = `import json, sys
def emit(ev):
    print(json.dumps(ev), flush=True)
emit({"type": "log", "msg": "start"})
emit({"type": "progress", "current": 1, "total": 2, "file": "a.mp4"})
emit({"type": "success", "file": "a.mp4", "suffix": "ok"})
emit({"type": "progress", "current": 2, "total": 2, "file": "b.mp4"})
emit({"type": "failure", "file": "b.mp4", "reason": "404"})
emit({"type": "done", "total": 2, "success": 1, "failed": 1})
print("WARN: non-json stderr", file=sys.stderr)
`
	}
	if err := os.WriteFile(path, []byte(src), 0755); err != nil {
		t.Fatal(err)
	}
	return path
}

// mockFactory 让 runner 指向 mock 脚本而不是真 cli.py。
func mockFactory(mockPath string) CmdFactory {
	return func(cliPath string, args []string) *exec.Cmd {
		return exec.Command("python3", mockPath)
	}
}

func TestProcessRunner_EventStream(t *testing.T) {
	mock := writeMockCLI(t, "normal")
	r := NewProcessRunner(t.TempDir(), "unused")
	r.SetCmdFactory(mockFactory(mock))

	var events []Event
	err := r.Run([]string{"--path", "/tmp"}, func(ev Event) {
		events = append(events, ev)
	}, nil)
	if err != nil {
		t.Fatalf("Run: %v", err)
	}

	// 事件顺序：log → progress → success → progress → failure → done
	wantTypes := []string{"log", "progress", "success", "progress", "failure", "done"}
	if len(events) != len(wantTypes) {
		t.Fatalf("expected %d events, got %d", len(wantTypes), len(events))
	}
	for i, want := range wantTypes {
		if events[i].Type != want {
			t.Errorf("event[%d].Type = %q, want %q", i, events[i].Type, want)
		}
	}
	// 校验字段透传
	if events[3].File != "b.mp4" || events[3].Current != 2 {
		t.Errorf("progress payload mismatch: %+v", events[3])
	}
	if events[4].Reason != "404" {
		t.Errorf("failure reason = %q, want 404", events[4].Reason)
	}
	done := events[5]
	if done.Success != 1 || done.Failed != 1 || done.Total != 2 {
		t.Errorf("done payload mismatch: %+v", done)
	}
}

func TestProcessRunner_StderrPassthrough(t *testing.T) {
	mock := writeMockCLI(t, "normal")
	r := NewProcessRunner(t.TempDir(), "unused")
	r.SetCmdFactory(mockFactory(mock))

	var stderrLines []string
	err := r.Run([]string{}, func(ev Event) {}, func(line string) {
		stderrLines = append(stderrLines, line)
	})
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if len(stderrLines) == 0 {
		t.Fatal("expected stderr passthrough")
	}
	if stderrLines[0] != "WARN: non-json stderr" {
		t.Errorf("stderr line = %q, want WARN line", stderrLines[0])
	}
}

func TestProcessRunner_NonJSONStdout(t *testing.T) {
	// mock 输出一行非 JSON 到 stdout，应走 onStderr 且不中断
	dir := t.TempDir()
	path := filepath.Join(dir, "mock.py")
	src := `import json, sys
print("NOT JSON", flush=True)
print(json.dumps({"type": "log", "msg": "after"}), flush=True)
`
	if err := os.WriteFile(path, []byte(src), 0755); err != nil {
		t.Fatal(err)
	}
	r := NewProcessRunner(t.TempDir(), "unused")
	r.SetCmdFactory(func(cliPath string, args []string) *exec.Cmd {
		return exec.Command("python3", path)
	})

	var types []string
	var stderr []string
	err := r.Run([]string{}, func(ev Event) {
		types = append(types, ev.Type)
	}, func(line string) {
		stderr = append(stderr, line)
	})
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if len(types) != 1 || types[0] != "log" {
		t.Errorf("expected 1 log event, got %v", types)
	}
	if len(stderr) != 1 || stderr[0] != "[NON-JSON] NOT JSON" {
		t.Errorf("expected NON-JSON passthrough, got %v", stderr)
	}
}

func TestProcessRunner_Cancel(t *testing.T) {
	mock := writeMockCLI(t, "sleep")
	r := NewProcessRunner(t.TempDir(), "unused")
	r.SetCmdFactory(mockFactory(mock))

	done := make(chan error, 1)
	go func() {
		done <- r.Run([]string{}, func(ev Event) {}, nil)
	}()

	// 等待进程启动并开始输出
	time.Sleep(500 * time.Millisecond)
	if !r.IsRunning() {
		t.Fatal("expected runner running before cancel")
	}

	r.Cancel()

	select {
	case err := <-done:
		if err != nil {
			t.Errorf("cancel should return nil error, got %v", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("Run did not return after cancel")
	}
	if r.IsRunning() {
		t.Error("runner should not be running after cancel")
	}
}

func TestProcessRunner_RejectConcurrentRun(t *testing.T) {
	mock := writeMockCLI(t, "sleep")
	r := NewProcessRunner(t.TempDir(), "unused")
	r.SetCmdFactory(mockFactory(mock))

	done := make(chan error, 1)
	go func() {
		done <- r.Run([]string{}, func(ev Event) {}, nil)
	}()
	time.Sleep(300 * time.Millisecond)

	if err := r.Run([]string{}, func(ev Event) {}, nil); err == nil {
		t.Error("expected error on concurrent Run")
	}

	r.Cancel()
	<-done
}

func TestArgs(t *testing.T) {
	if got := ScanArgs("/m"); len(got) != 3 || got[0] != "scan" {
		t.Errorf("ScanArgs = %v", got)
	}
	pa := ProcessArgs("/m", 2)
	if pa[2] != "--main-mode" || pa[3] != "2" {
		t.Errorf("ProcessArgs = %v", pa)
	}
	found := false
	for _, a := range pa {
		if a == "--json-output" {
			found = true
		}
	}
	if !found {
		t.Error("ProcessArgs should include --json-output")
	}
}
