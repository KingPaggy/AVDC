package config

// DefaultKeybindings 默认键位表（action → key string）。
// 用户配置按相同 action 名覆盖。
//
// 分组说明：
//   - global.*：所有非临时 context 生效
//   - log.*：log 面板滚动
//   - files.*：文件列表面板
//   - result.*：结果面板
//   - list.*：列表导航（files/result/menu 共享）
var DefaultKeybindings = map[string]string{
	// 全局
	"global.quit":      "q",
	"global.escape":    "esc",
	"global.focusNext": "l",
	"global.focusPrev": "h",
	"global.help":      "?",
	"global.config":    "c",
	// log 滚动
	"log.scrollDown": "j",
	"log.scrollUp":   "k",
	"log.top":        "g",
	"log.bottom":     "G",
	// files 面板
	"files.refresh":  "r",
	"files.search":   "/",
	"files.mark":     "space",
	"files.markAll":  "a",
	"files.cancel":   "x",
	"files.scrape":   "s",
	"files.organize": "o",
	// result 面板
	"result.filter": "t",
	// 列表导航（vim 键可配置；方向键固定不配置）
	"list.down":     "j",
	"list.up":       "k",
	"list.home":     "g",
	"list.end":      "G",
	"list.pageUp":   ",",
	"list.pageDown": ".",
}

// Registry 键位注册表：默认值 + 用户覆盖合并。
// 未知 action 的覆盖会被忽略（保持默认）。
type Registry struct {
	actions map[string]string
}

// NewRegistry 创建注册表（默认 + 覆盖合并）。
func NewRegistry(overrides KeybindingConfig) *Registry {
	actions := make(map[string]string, len(DefaultKeybindings))
	for k, v := range DefaultKeybindings {
		actions[k] = v
	}
	for k, v := range overrides {
		if v == "" {
			continue
		}
		if _, ok := actions[k]; ok {
			actions[k] = v
		}
	}
	return &Registry{actions: actions}
}

// Key 返回 action 的 gocui key（rune 或 gocui.Key）。
// 解析失败时回退默认键位；仍失败返回 nil（调用方跳过）。
func (r *Registry) Key(action string) any {
	key, err := ParseKey(r.actions[action])
	if err != nil {
		if def, ok := DefaultKeybindings[action]; ok {
			key, err = ParseKey(def)
		}
	}
	if err != nil {
		return nil
	}
	return key
}

// String 返回 action 的原始键位字符串（调试用）。
func (r *Registry) String(action string) string {
	return r.actions[action]
}
