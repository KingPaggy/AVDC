// Package components 提供可复用的 UI 组件。
package components

// ListViewModel 管理列表数据与选中索引，是列表的单一数据源。
// 渲染从 Items() 读取，导航通过 Select/Move 修改选中状态，
// cursor 位置由上层同步（仅作视觉呈现）。
type ListViewModel[T any] struct {
	items  []T
	selIdx int
}

// NewListViewModel 创建一个空列表模型。
func NewListViewModel[T any]() *ListViewModel[T] {
	return &ListViewModel[T]{selIdx: -1}
}

// SetItems 替换列表数据，并重置选中到第一个元素（空列表为 -1）。
func (m *ListViewModel[T]) SetItems(items []T) {
	m.items = items
	if len(items) > 0 {
		m.selIdx = 0
	} else {
		m.selIdx = -1
	}
}

// Items 返回当前列表数据（只读使用）。
func (m *ListViewModel[T]) Items() []T {
	return m.items
}

// Len 返回元素个数。
func (m *ListViewModel[T]) Len() int {
	return len(m.items)
}

// SelectedIndex 返回当前选中索引；空列表为 -1。
func (m *ListViewModel[T]) SelectedIndex() int {
	return m.selIdx
}

// Selected 返回当前选中元素；空列表返回 ok=false。
func (m *ListViewModel[T]) Selected() (T, bool) {
	var zero T
	if m.selIdx < 0 || m.selIdx >= len(m.items) {
		return zero, false
	}
	return m.items[m.selIdx], true
}

// Select 将选中移动到 idx（越界则拒绝）。返回是否成功。
func (m *ListViewModel[T]) Select(idx int) bool {
	if idx < 0 || idx >= len(m.items) {
		return false
	}
	m.selIdx = idx
	return true
}

// Move 将选中移动 delta 步，夹在 [0, Len-1] 区间。
// 返回选中索引是否发生变化。
func (m *ListViewModel[T]) Move(delta int) bool {
	if m.selIdx < 0 || len(m.items) == 0 {
		return false
	}
	next := m.selIdx + delta
	if next < 0 {
		next = 0
	}
	if next >= len(m.items) {
		next = len(m.items) - 1
	}
	if next == m.selIdx {
		return false
	}
	m.selIdx = next
	return true
}

// ResetSelection 将选中重置到第一个元素。
func (m *ListViewModel[T]) ResetSelection() {
	if len(m.items) > 0 {
		m.selIdx = 0
	} else {
		m.selIdx = -1
	}
}
