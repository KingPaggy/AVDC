package commands

import (
	"fmt"
	"strings"
)

// ScanArgs 构造 `scan` 命令参数（同步一次性扫描）。
func ScanArgs(dir string) []string {
	return []string{"scan", "--path", dir}
}

// ProcessArgs 构造刮削/整理命令参数（--json-output 流式）。
// mode: 1=scrape（刮削元数据） 2=organize（重命名整理）。
func ProcessArgs(dir string, mode int) []string {
	return []string{
		"--path", dir,
		"--main-mode", fmt.Sprint(mode),
		"--json-output",
	}
}

// argsString 供日志/调试输出。
func argsString(args []string) string {
	return strings.Join(args, " ")
}
