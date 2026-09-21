package gui

import (
	"github.com/go-errors/errors"
	"github.com/jesseduffield/gocui"

	"avdc-tui/pkg/gui/helpers"
)

// Layout 处理 view 定位与重排。
//
// 布局采用 flex 比例分配：顶栏 options（1 行）、中间三栏
// files:log:result = 1:2:1、底栏 status（1 行）。
// 窄窗口（<60 列）降级：隐藏 result，log 占满剩余宽度。
type Layout struct {
	gui *Gui
}

// 面板间隔（列）。
const panelGap = 1

// layout 每次屏幕重绘时调用（含 resize）。
func (l *Layout) layout(g *gocui.Gui) error {
	width, height := g.Size()

	topLines := 1
	bottomLines := 1
	midY0 := topLines
	midY1 := height - bottomLines - 1

	// 窄窗口降级：隐藏 result 栏
	resultVisible := width >= 60

	panels := l.flexPanels(width, midY0, midY1, resultVisible)

	if err := l.setView(g, "options", 0, 0, width, topLines); err != nil {
		return err
	}
	if err := l.setView(g, "files", panels[0][0], panels[0][1],
		panels[0][2], panels[0][3]); err != nil {
		return err
	}
	if err := l.setView(g, "log", panels[1][0], panels[1][1],
		panels[1][2], panels[1][3]); err != nil {
		return err
	}
	if err := l.setView(g, "result", panels[2][0], panels[2][1],
		panels[2][2], panels[2][3]); err != nil {
		return err
	}
	if err := l.setView(g, "status", 0, height-bottomLines,
		width, height-1); err != nil {
		return err
	}

	// 窄窗口时隐藏 result view（恢复时自动显示）
	if v, err := g.View("result"); err == nil {
		v.Visible = resultVisible
	}

	l.renderOptions()
	l.renderStatus()
	return nil
}

// flexPanels 按权重 1:2:1 计算三栏坐标（与原布局坐标一致：
// files→log 间留 1 空隙列，log→result 相邻，边框外扩后
// 由 SupportOverlaps 允许轻微重叠）。
// 返回 [files, log, result] 三元组，每项为 [x0,y0,x1,y1]。
func (l *Layout) flexPanels(width, y0, y1 int, showResult bool) [][4]int {
	filesW := width / 4
	logW := width / 2
	if !showResult {
		// result 隐藏：log 占满剩余
		logW = width - filesW - 2*panelGap
	}

	filesX1 := filesW - 1
	logX0 := filesW + panelGap
	logX1 := filesW + logW
	resultX0 := logX1 + panelGap
	resultX1 := width - 2

	return [][4]int{
		{0, y0, filesX1, y1},         // files
		{logX0, y0, logX1, y1},       // log
		{resultX0, y0, resultX1, y1}, // result
	}
}

// setView 定位 view（frameOffset=1 边框外扩 1 字符）。
func (l *Layout) setView(g *gocui.Gui, name string, x0, y0, x1, y1 int) error {
	const frameOffset = 1
	_, err := g.SetView(name,
		x0-frameOffset, y0-frameOffset,
		x1+frameOffset, y1+frameOffset, 0)
	if err != nil && !errors.Is(err, gocui.ErrUnknownView) {
		return err
	}
	return nil
}

// optionsHints 各 context 的顶栏键位提示（随焦点切换）。
var optionsHints = map[string]string{
	"files": "j/k: Nav  |  Enter: Menu  |  s: Scrape  |  " +
		"o: Organize  |  space: Mark  |  /: Search  |  " +
		"r: Refresh  |  c: Config  |  ?: Help  |  q: Quit",
	"log": "j/k: Scroll  |  g/G: Top/Bottom  |  x: Cancel  |  " +
		"h/l: Panel  |  ?: Help",
	"result": "j/k: Nav  |  Enter: Detail  |  t: Filter  |  " +
		"x: Cancel  |  h/l: Panel  |  ?: Help",
	"menu":    "j/k: Move  |  Enter: Confirm  |  Esc: Cancel",
	"confirm": "y: Yes  |  n: No  |  Esc: Cancel",
	"prompt":  "Enter: Confirm  |  Ctrl+U: Clear  |  Esc: Cancel",
	"help":    "Tab: Category  |  Esc/q: Close",
	"config":  "j/k: Field  |  Enter: Edit  |  s: Save  |  Esc: Close",
}

// renderOptions 绘制顶部选项栏（当前 context 的键位提示）。
func (l *Layout) renderOptions() {
	v, err := l.gui.getView("options")
	if err != nil {
		return
	}
	text := optionsHints[l.gui.contexts.Current().Name]
	if text == "" {
		text = "?: Help  |  q: Quit"
	}
	v.Clear()
	v.FgColor = helpers.Theme.OptionsBarFg
	v.WriteString(text)
}

// renderStatus 绘制底部状态栏（从 Gui 状态渲染，不覆盖
// 已设置的状态文本）。
func (l *Layout) renderStatus() {
	v, err := l.gui.getView("status")
	if err != nil {
		return
	}
	text := l.gui.StatusText()
	if text == "" {
		text = "Ready  |  Select a directory to begin  |  AVDC TUI v" +
			l.gui.version
	}
	v.Clear()
	v.FgColor = helpers.Theme.StatusBarFg
	v.WriteString(text)
}
