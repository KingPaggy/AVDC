package components

import (
	"avdc-tui/pkg/gui/helpers"
)

// Toast 在状态栏显示一条通知消息。
// 不自动消失（状态栏随后会被状态更新覆盖），避免在
// gocui 单线程中使用计时器/goroutine 的风险。
// 轻提示用途：配置保存成功、任务完成、操作被取消等。
func Toast(gui GuiLike, msg string, isError bool) {
	g := gui.GetGui()
	v, err := g.View("status")
	if err != nil {
		return
	}
	v.Clear()
	if isError {
		v.WriteString(helpers.Error(msg))
	} else {
		v.WriteString(helpers.Info(msg))
	}
}
