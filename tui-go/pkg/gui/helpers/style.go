package helpers

import "fmt"

// style 提供文本样式标签辅助（gocui 的 [color]...[-] 语法）。
// 状态语义映射到固定颜色：成功绿 / 失败红 / 警告黄 /
// 强调青 / 弱化 dim，避免散落的裸标签。

// Info 返回绿色成功/信息文本标签。
func Info(s string) string { return fmt.Sprintf("[green]%s[-]", s) }

// Error 返回红色错误/失败文本标签。
func Error(s string) string { return fmt.Sprintf("[red]%s[-]", s) }

// Warning 返回黄色警告文本标签。
func Warning(s string) string { return fmt.Sprintf("[yellow]%s[-]", s) }

// Accent 返回青色强调文本标签。
func Accent(s string) string { return fmt.Sprintf("[cyan]%s[-]", s) }

// Dim 返回弱化文本标签（次要说明）。
func Dim(s string) string { return fmt.Sprintf("[dim]%s[-]", s) }
