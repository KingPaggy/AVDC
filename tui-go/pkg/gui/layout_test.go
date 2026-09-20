package gui

import "testing"

// 宽窗口（100 列）下三栏按 1:2:1 分配。
func TestFlexPanels_WideWindow(t *testing.T) {
	l := &Layout{}
	panels := l.flexPanels(100, 1, 20, true)

	// files: 0..24
	if panels[0] != [4]int{0, 1, 24, 20} {
		t.Errorf("files = %v, want [0 1 24 20]", panels[0])
	}
	// log: 26..75
	if panels[1] != [4]int{26, 1, 75, 20} {
		t.Errorf("log = %v, want [26 1 75 20]", panels[1])
	}
	// result: 76..98
	if panels[2] != [4]int{76, 1, 98, 20} {
		t.Errorf("result = %v, want [76 1 98 20]", panels[2])
	}
	// files→log 间留 1 空隙列（内部间隔 2）
	if panels[0][2]+2 != panels[1][0] {
		t.Errorf("gap files->log: got %d, want 2",
			panels[1][0]-panels[0][2])
	}
	// log→result 相邻（内部间隔 1，边框外扩后轻微重叠，
	// 由 SupportOverlaps 处理——与原布局行为一致）
	if panels[1][2]+1 != panels[2][0] {
		t.Errorf("gap log->result: got %d, want 1",
			panels[2][0]-panels[1][2])
	}
}

// 窄窗口（<60 列）降级：result 隐藏，log 占满剩余宽度。
func TestFlexPanels_NarrowWindow(t *testing.T) {
	l := &Layout{}
	panels := l.flexPanels(50, 1, 20, false)

	// files: 0..11
	if panels[0] != [4]int{0, 1, 11, 20} {
		t.Errorf("files = %v, want [0 1 11 20]", panels[0])
	}
	// log 占满剩余：13..48
	if panels[1] != [4]int{13, 1, 48, 20} {
		t.Errorf("log = %v, want [13 1 48 20]", panels[1])
	}
	// result 坐标越界（x0 > x1），配合 Visible=false 不渲染
	if panels[2][0] <= panels[2][2] {
		t.Errorf("result x0=%d should exceed x1=%d (hidden)",
			panels[2][0], panels[2][2])
	}
}

// 极窄窗口不应产生负宽度。
func TestFlexPanels_VeryNarrow(t *testing.T) {
	l := &Layout{}
	panels := l.flexPanels(20, 1, 20, false)
	if panels[0][2] < panels[0][0] {
		t.Errorf("files width negative: %v", panels[0])
	}
	if panels[1][2] < panels[1][0] {
		t.Errorf("log width negative: %v", panels[1])
	}
}
