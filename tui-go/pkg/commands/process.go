// Package commands 封装对 cli.py 的子进程调用：
// 统一命令构造、JSONL 流式解析、取消与错误包装。
package commands

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
)

// Event 表示 cli.py --json-output 的一行 JSONL 事件。
type Event struct {
	Type    string `json:"type"`
	Msg     string `json:"msg,omitempty"`
	File    string `json:"file,omitempty"`
	Suffix  string `json:"suffix,omitempty"`
	Reason  string `json:"reason,omitempty"`
	Error   string `json:"error,omitempty"`
	Current int    `json:"current,omitempty"`
	Total   int    `json:"total,omitempty"`
	Success int    `json:"success,omitempty"`
	Failed  int    `json:"failed,omitempty"`
	Result  string `json:"result,omitempty"`
}

// CmdFactory 构造子进程命令（测试注入 mock 用）。
type CmdFactory func(cliPath string, args []string) *exec.Cmd

// DefaultCmdFactory 用 uv 启动 cli.py（与 mac-gui 一致，
// 绝对路径 /opt/homebrew/bin/uv 不依赖 PATH）。
func DefaultCmdFactory(cliPath string, args []string) *exec.Cmd {
	cmdArgs := append([]string{"run", "python", cliPath}, args...)
	return exec.Command("/opt/homebrew/bin/uv", cmdArgs...)
}

// ProcessRunner 运行 cli.py 子进程并流式解析 JSONL 事件。
type ProcessRunner struct {
	projectRoot string
	cliPath     string
	factory     CmdFactory
	cmd         *exec.Cmd
	mu          sync.Mutex
	running     bool
	cancelled   bool
}

// NewProcessRunner 创建命令运行器。
// cliPath 为 cli/cli.py 路径；projectRoot 作为子进程工作目录。
func NewProcessRunner(projectRoot, cliPath string) *ProcessRunner {
	return &ProcessRunner{
		projectRoot: projectRoot,
		cliPath:     cliPath,
		factory:     DefaultCmdFactory,
	}
}

// SetCmdFactory 替换命令构造器（测试注入 mock 脚本）。
func (r *ProcessRunner) SetCmdFactory(f CmdFactory) {
	r.factory = f
}

// IsRunning 是否正在运行。
func (r *ProcessRunner) IsRunning() bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.running
}

// Run 启动子进程，逐行解析 stdout 的 JSONL 并回调 onEvent；
// stderr 的非 JSON 输出通过 onStderr 透传（不丢失）。
// 返回进程错误（取消时返回 nil 表示被取消）。
func (r *ProcessRunner) Run(args []string,
	onEvent func(Event), onStderr func(string)) error {
	r.mu.Lock()
	if r.running {
		r.mu.Unlock()
		return fmt.Errorf("process already running")
	}
	r.running = true
	r.cancelled = false
	r.mu.Unlock()
	defer func() {
		r.mu.Lock()
		r.running = false
		r.mu.Unlock()
	}()

	cmd := r.factory(r.cliPath, args)
	cmd.Dir = r.projectRoot
	r.mu.Lock()
	r.cmd = cmd
	r.mu.Unlock()

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("stdout pipe: %w", err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("start: %w", err)
	}

	// stdout：JSONL 事件流
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		var ev Event
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			if onStderr != nil {
				onStderr("[NON-JSON] " + line)
			}
			continue
		}
		onEvent(ev)
	}

	// stderr：非 JSON 输出透传
	errScanner := bufio.NewScanner(stderr)
	for errScanner.Scan() {
		line := errScanner.Text()
		if strings.TrimSpace(line) != "" && onStderr != nil {
			onStderr(line)
		}
	}

	err = cmd.Wait()
	r.mu.Lock()
	wasCancel := r.cancelled
	r.mu.Unlock()
	if err != nil {
		if wasCancel {
			return nil // 被取消：非错误
		}
		return fmt.Errorf("process exited: %w", err)
	}
	return nil
}

// Cancel 取消当前子进程（kill 整个进程组，避免残留）。
// 未运行时无操作。
func (r *ProcessRunner) Cancel() {
	r.mu.Lock()
	r.cancelled = true
	cmd := r.cmd
	r.mu.Unlock()
	if cmd != nil && cmd.Process != nil {
		// 负 PID 表示进程组，确保子进程一并终止
		_ = exec.Command("kill", "-TERM",
			fmt.Sprintf("-%d", cmd.Process.Pid)).Run()
		_ = cmd.Process.Kill()
	}
}

// cliPath 由 NewProcessRunner 注入；此辅助供测试构造。
func cliPathOf(root string) string {
	return filepath.Join(root, "cli", "cli.py")
}
