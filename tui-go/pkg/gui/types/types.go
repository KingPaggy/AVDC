// Package types 定义 TUI 共享类型与枚举。
package types

// WindowName 标识逻辑屏幕区域（布局编排单位）。
type WindowName string

const (
	WindowFiles WindowName = "files" // 侧栏：文件列表
	WindowMain  WindowName = "main"  // 主区域：log/result 共享
)

// ContextKind 标识 context 的类型，决定其布局与焦点行为。
type ContextKind int

const (
	ContextSide      ContextKind = iota // 侧栏/常驻面板
	ContextMain                         // 主区域面板
	ContextTemporary                    // 临时弹窗（menu/confirm/...）
)

// VideoFile 表示扫描到的视频文件。
type VideoFile struct {
	Path   string // 完整路径（/ 分隔）
	Name   string // 无扩展名文件名
	Number string // 提取的番号（可为空）
	Dir    bool   // 是否为目录项
}

// ScrapeStats 刮削进度与统计。
type ScrapeStats struct {
	Total   int
	Success int
	Failed  int
	Current int
}
