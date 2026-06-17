# AVDC QML UI 设计手册

> 基于 UI/UX Pro Max 设计智能（67 种风格 / 96 种配色 / 99 条 UX 准则）生成，针对 AVDC PySide6 QML 桌面应用定制。

## 1. 设计系统总览

| 维度 | 选择 | 说明 |
|------|------|------|
| **风格** | Dark Mode (OLED) | 深色主题，低白光发射，高对比度，WCAG AAA 级可访问性 |
| **色彩体系** | Catppuccin Mocha | 社区成熟暗色调色板，与设置页现有设计一致 |
| **字体策略** | 系统默认字体族 | QML 桌面应用优先使用系统原生字体 |
| **布局模式** | 底部 Tab 导航 + SwipeView | 适合桌面端水平导航，5 个页面 |
| **信息密度** | 中等 | 12-16px padding，14px 正文，可读不拥挤 |

### 1.1 设计原则

1. **功能优先** — 桌面工具类应用，信息清晰 > 视觉装饰
2. **一致性** — 全部页面复用同一套组件和配色
3. **低干扰** — 暗色背景 + 有限强调色，减少视觉噪音
4. **可访问性** — 文字对比度 ≥ 4.5:1，焦点状态可见

---

## 2. 配色系统

### 2.1 Catppuccin Mocha 色板

| 角色 | 名称 | 色值 | 用途 |
|------|------|------|------|
| **背景** | Base | `#181825` | ApplicationWindow 底色 |
| **表面** | Mantle | `#1e1e2e` | 卡片、面板、TabBar 背景 |
| **覆盖层0** | Surface0 | `#313244` | 输入框、选择器背景 |
| **覆盖层1** | Surface1 | `#45475a` | 非聚焦边框、分割线 |
| **覆盖层2** | Surface2 | `#585b70` | 次级分割线、禁用态 |
| **强调** | Blue | `#89b4fa` | 聚焦边框、滑块值、链接、激活态 |
| **主文字** | Text | `#cdd6f4` | 标题、正文 |
| **次要文字** | Subtext1 | `#bac2de` | 标签、描述 |
| **弱文字** | Overlay2 | `#6c7086` | 占位符、未激活态 |
| **成功** | Green | `#a6e3a1` | 成功提示、正向状态 |
| **警告** | Yellow | `#f9e2af` | 警告状态、注意提示 |
| **错误** | Red | `#f38ba8` | 错误提示、失败状态 |
| **信息** | Sky | `#89dceb` | 信息提示 |
| **高亮按钮** | Lavender | `#b4befe` | 主操作按钮（保存、确认） |
| **紫色强调** | Mauve | `#cba6f7` | 可选强调色 |
| **桃色** | Peach | `#fab387` | 可选强调色 |
| **品红** | Maroon | `#eba0ac` | 可选强调色 |
| **茶色** | Teal | `#94e2d5` | 可选强调色 |

### 2.2 语义化使用规则

| 场景 | 前景色 | 背景色 | 对比度 |
|------|--------|--------|--------|
| 正文 | `#cdd6f4` (Text) | `#1e1e2e` (Mantle) | ~14:1 ✓ |
| 标签 | `#bac2de` (Subtext1) | `#1e1e2e` (Mantle) | ~9.5:1 ✓ |
| 占位符 | `#6c7086` (Overlay2) | `#313244` (Surface0) | ~3.5:1 ⚠ (非交互文本可接受) |
| 按钮文字 | `#1e1e2e` (Mantle) | `#b4befe` (Lavender) | ~11:1 ✓ |
| 成功提示 | `#1e1e2e` (Mantle) | `#a6e3a1` (Green) | ~12:1 ✓ |
| 错误提示 | `#1e1e2e` (Mantle) | `#f38ba8` (Red) | ~8:1 ✓ |

### 2.3 状态色对照表

```
正常态  → 表面色: Surface0 (#313244), 文字: Text (#cdd6f4)
聚焦态  → 边框: Blue (#89b4fa), 文字: Text (#cdd6f4)
悬停态  → 边框: Surface2 (#585b70), 或颜色加深
禁用态  → 文字: Overlay2 (#6c7086), 不透明度降低
成功态  → 背景: Green (#a6e3a1), 文字: Base (#181825)
错误态  → 背景: Red (#f38ba8), 文字: Base (#181825)
警告态  → 背景: Yellow (#f9e2af), 文字: Base (#181825)
```

---

## 3. 字体与排版

### 3.1 字号层级

| 层级 | 字号 | 用途 |
|------|------|------|
| H1 | 24px bold | 页面主标题（About 页标题） |
| H2 | 16px bold | 区块标题（SectionCard 标题） |
| Body | 14px normal | 正文、标签、按钮文字 |
| Small | 13px normal | 次要文字、辅助说明 |
| Caption | 12px normal | 数值标签、状态标签 |

### 3.2 字体使用规范

QML 桌面应用使用系统默认字体族，不加载外部字体文件。

```qml
// 标题
font.pixelSize: 24
font.bold: true

// 区块标题
font.pixelSize: 16
font.bold: true

// 正文 / 标签
font.pixelSize: 14

// 小字
font.pixelSize: 13

// 数值标签
font.pixelSize: 12
font.bold: true
```

### 3.3 行高与间距

- 正文行高：1.5（QML 默认即可）
- 区块内间距：12px（SectionCard 内部）
- 页面级间距：16px（页面顶部 margin）
- 按钮间距：16px（按钮之间）

---

## 4. 组件库

### 4.1 已有组件

#### SectionCard
- **位置**：`qml/components/SectionCard.qml`
- **用途**：分组容器，带标题和分割线
- **属性**：`sectionTitle` (string)
- **背景**：`#1e1e2e`，圆角 8px
- **内边距**：16px

#### ConfigInput
- **位置**：`qml/components/ConfigInput.qml`
- **用途**：标签 + 文本输入框
- **属性**：`labelText`, `textValue`
- **双向绑定**：`onTextValueChanged` ↔ 外部同步

#### ConfigSwitch
- **位置**：`qml/components/ConfigSwitch.qml`
- **用途**：标签 + 开关
- **属性**：`labelText`, `checked` (bool)

#### ConfigRadioGroup
- **位置**：`qml/components/ConfigRadioGroup.qml`
- **用途**：标签 + 水平单选按钮组
- **属性**：`labelText`, `options` (array), `selectedValue`

#### ConfigSlider
- **位置**：`qml/components/ConfigSlider.qml`
- **用途**：标签 + 滑块 + 数值显示
- **属性**：`labelText`, `sliderValue`, `fromValue`, `toValue`

#### ConfigCheckbox
- **位置**：`qml/components/ConfigCheckbox.qml`
- **用途**：复选框 + 标签
- **属性**：`labelText`, `checked` (bool)

#### ConfigFilePicker
- **位置**：`qml/components/ConfigFilePicker.qml`
- **用途**：标签 + 文本框 + 浏览按钮（目录选择）
- **属性**：`labelText`, `textValue`
- **信号**：`folderSelected(path)`

### 4.2 需新增组件

#### ProgressBar
- **用途**：刮削/整理进度显示
- **属性**：`progressValue` (0-1), `statusText`, `showPercentage` (bool)
- **颜色**：进度条 `#89b4fa`，背景 `#313244`
- **圆角**：6px

#### LogViewer
- **用途**：带滚动和颜色过滤的日志显示
- **属性**：`logEntries` (listModel), `filterLevel` (string: "all"|"error"|"warn"|"info")
- **日志颜色**：ERROR → `#f38ba8`, WARN → `#f9e2af`, INFO → `#cdd6f4`, DEBUG → `#6c7086`

#### ToolCard
- **用途**：工具卡片，展示单个工具
- **属性**：`iconName` (string), `title`, `description`, `actionLabel`
- **交互**：点击触发 `clicked` 信号
- **悬停**：边框 `#585b70` → `#89b4fa`，轻微背景色变

#### StatusBadge
- **用途**：状态徽章
- **属性**：`status` (string: "success"|"error"|"warning"|"info"), `text`
- **颜色**：success → Green, error → Red, warning → Yellow, info → Sky

---

## 5. 页面结构

### 5.1 全局布局

```
ApplicationWindow (960 x 700, min 800 x 600)
├── Toast (floating, z: 100, 顶部居中)
│   ├── 绿色成功: #a6e3a1
│   ├── 红色错误: #f38ba8
│   └── 自动消失: 2s, slide 动画 300ms
│
├── ColumnLayout
│   ├── SwipeView (fill parent minus TabBar)
│   │   ├── HomePage          (index 0)
│   │   ├── LogPage           (index 1)
│   │   ├── ToolsPage         (index 2)
│   │   ├── SettingsPage      (index 3) ← 已实现
│   │   └── AboutPage         (index 4)
│   │
│   └── TabBar (bottom, 高度自适应)
│       ├── TabButton "主页"
│       ├── TabButton "日志"
│       ├── TabButton "工具"
│       ├── TabButton "设置"
│       └── TabButton "关于"
│
└── Connections { target: settings }
    ├── onConfigSaved() → toast.show("配置已保存")
    ├── onConfigLoaded() → toast.show("配置已加载")
    └── onErrorOccurred(msg) → toast.show(msg, color: #f38ba8)
```

### 5.2 页面规格

#### HomePage（主页 / 工作台）

```
ScrollView
└── ColumnLayout (width: 680, centered)
    ├── 文件选择区
    │   ├── ConfigFilePicker (label: "输入目录")
    │   └── ConfigInput (label: "排除文件夹")
    │
    ├── 模式选择
    │   └── ConfigRadioGroup (刮削模式 / 整理模式)
    │
    ├── 操作按钮区
    │   ├── Button "开始处理" (highlighted, primary action)
    │   └── Button "停止"
    │
    └── 进度显示区
        ├── ProgressBar (实时进度)
        ├── 状态文字 ("正在处理: xxx.mp4")
        └── 统计信息 (成功: N, 失败: N, 跳过: N)
```

**交互要点**：
- "开始处理" 按钮触发 Python CoreEngine 的 `process_batch()`
- 进度通过 Python Signal/Slot 实时更新 QML ProgressBar
- 统计数字用 StatusBadge 显示

#### LogPage（日志）

```
ColumnLayout (fills parent)
├── RowLayout (filter bar, height: 40)
│   ├── ConfigRadioGroup inline (全部 / 错误 / 警告 / 信息)
│   └── Spacer
│   ├── Button "清空"
│   └── Button "导出"
│
└── ScrollView (fills remaining)
    └── ListView / Repeater (log entries)
        ├── 每行: [时间] [级别色块] [日志文字]
        └── 自动滚动到底部
```

**交互要点**：
- 日志条目通过 Python 侧 EventBus 实时推送
- 日志级别着色：ERROR=#f38ba8, WARN=#f9e2af, INFO=#cdd6f4, DEBUG=#6c7086
- 时间戳格式：`HH:mm:ss`，颜色 `#6c7086`

#### ToolsPage（工具）

```
ScrollView
└── ColumnLayout (width: 680, centered)
    ├── SectionCard (sectionTitle: "文件工具")
    │   └── GridLayout (columns: 2)
    │       ├── ToolCard (批量重命名)
    │       ├── ToolCard (封面裁剪)
    │       ├── ToolCard (水印处理)
    │       └── ToolCard (格式转换)
    │
    └── SectionCard (sectionTitle: "媒体库工具")
        └── GridLayout (columns: 2)
            ├── ToolCard (Emby 同步)
            ├── ToolCard (NFO 生成器)
            ├── ToolCard (元数据编辑)
            └── ToolCard (重复检测)
```

#### SettingsPage（设置）

> 已完整实现，参考 `qml/SettingsPage.qml`。

#### AboutPage（关于）

```
Item
└── ColumnLayout (centered in parent)
    ├── Text ("AVDC", 24px, bold, #cdd6f4)
    ├── Text ("PySide6 + QML 版", 14px, #6c7086)
    ├── Text ("版本: x.x.x", 13px, #bac2de)
    ├── Text ("Python 3.13", 13px, #6c7086)
    ├── Rectangle (divider)
    └── Text ("开源协议 & 依赖信息", 13px, #bac2de)
```

---

## 6. 交互规范

### 6.1 动画与过渡

| 场景 | 时长 | 缓动 |
|------|------|------|
| Toast 滑入 | 300ms | OutCubic |
| 输入框聚焦 | 150ms | 默认线性 |
| 按钮悬停 | 150ms | 默认线性 |
| 页面切换 | SwipeView 默认 | 内置滑动 |
| 滑块拖动 | 实时 | 无延迟 |

**原则**：桌面应用微交互不超过 300ms，避免拖沓感。

### 6.2 按钮状态

```
默认态 → 系统默认背景 + 文字色 #cdd6f4
悬停态 → 背景变亮 10% + 光标 pointerHand: true
按下态 → 背景变暗 5%
聚焦态 → 边框 #89b4fa (1px)
禁用态 → 不透明度 0.5 + 不可交互
Primary → highlighted: true + 背景 #b4befe + 文字 #1e1e2e
```

### 6.3 输入框状态

```
默认态 → 背景 #313244, 边框 #45475a
聚焦态 → 边框 #89b4fa (1px), 背景不变
错误态 → 边框 #f38ba8 (1px) + 错误提示文字
禁用态 → 不透明度 0.5
```

### 6.4 Toast 使用规范

| 类型 | 背景色 | 文字色 | 时长 |
|------|--------|--------|------|
| 成功 | `#a6e3a1` | `#1e1e2e` | 2s |
| 错误 | `#f38ba8` | `#1e1e2e` | 3s（手动可关闭） |
| 信息 | `#89b4fa` | `#1e1e2e` | 2s |

### 6.5 加载状态

- 短操作（< 2s）：按钮禁用 + 文字变为 "处理中..."
- 长操作（> 2s）：ProgressBar 显示进度百分比
- 不确定时长：进度条使用循环动画（indeterminate 模式）

---

## 7. Python-QML 数据流

### 7.1 数据绑定模式

```
Python SettingsModel                    QML Components
┌─────────────────┐                     ┌────────────────────┐
│   Property      │ ◄── Signal ───────  │   onXxxChanged      │
│   (getter/setter)│                     │   (双向绑定)         │
│                 │ ── notify signal ─► │   自动更新 UI        │
│   @Slot 方法    │ ◄── QML 调用 ────── │   settings.save()   │
│   Signal 事件   │ ── emit ─────────►  │   Connections { }   │
└─────────────────┘                     └────────────────────┘
```

### 7.2 命名约定

| Python (snake_case) | QML (camelCase) |
|---------------------|-----------------|
| `main_mode` | `mainMode` |
| `success_output_folder` | `successOutputFolder` |
| `poster_mark` | `posterMark` |
| `baidu_app_id` | `baiduAppId` |

### 7.3 新增属性步骤

1. 在 `settings_model.py` 添加 Signal：`newFieldChanged = Signal(str)`
2. 使用 `_make_prop` 创建 getter/setter：
   ```python
   _get_nf, _set_nf = _make_prop("new_field", "newFieldChanged")
   newField = Property(str, _get_nf, _set_nf, notify=newFieldChanged)
   ```
3. 在 `_load_defaults()` 添加默认值
4. 在 `load()` 的字段映射中添加
5. 在 `_signal_map()` 中添加映射
6. QML 侧绑定：`textValue: settings.newField`

---

## 8. 编码规范

### 8.1 QML 文件规范

- **文件名**：PascalCase，如 `SettingsPage.qml`、`ConfigInput.qml`
- **类型名**：与文件名一致（`Item { id: settingsPage }`）
- **导入顺序**：QtQuick → QtQuick.Controls → QtQuick.Layouts → 本地模块
- **属性声明**：放在组件顶部，`id` 之后
- **注释**：`// 中文说明`，分组用 `// ===== 区块名 =====`

### 8.2 属性命名

```qml
// 对外暴露的 property
property string labelText: ""
property int sliderValue: 0
property var options: []

// 内部 id 命名
id: root          // 根元素
id: input         // 输入框
id: toggle        // 开关
id: slider        // 滑块
id: column        // 布局容器
```

### 8.3 双向绑定防循环

```qml
// ConfigInput 中的做法：
onTextValueChanged: {
    // 只有当内部值与外部值不同时才更新，避免无限循环
    if (input.text !== textValue) input.text = textValue
}

TextField {
    onTextChanged: {
        if (root.textValue !== text) root.textValue = text
    }
}
```

### 8.4 颜色使用规范

```qml
// ❌ 不要：硬编码颜色散落在各处
color: "#1e1e2e"

// ✅ 推荐：注释标注颜色名称，保持一致
color: "#1e1e2e"  // Catppuccin Mantle
```

项目已有配色应全项目统一，不要在新页面中使用未在色板中的颜色。

---

## 9. 可访问性

| 检查项 | 要求 | 状态 |
|--------|------|------|
| 文字对比度 | ≥ 4.5:1 (WCAG AA) | ✅ Catppuccin Mocha 已满足 |
| 焦点可见 | 聚焦元素有视觉反馈 | ✅ 蓝色边框 `#89b4fa` |
| 键盘导航 | Tab 键可达所有交互元素 | ✅ QML 默认支持 |
| 错误不依赖颜色 | 错误有文字 + 图标 | ⚠ 需确保实现 |
| 最小字号 | 正文 ≥ 14px | ✅ 已满足 |

---

## 10. 开发工作流

### 10.1 添加新页面

1. 在 `qml/` 下创建 `XxxPage.qml`
2. 在 `main.qml` 的 SwipeView 中添加页面
3. 在 `main.qml` 的 TabBar 中添加 TabButton（顺序对应）
4. 需要新组件 → 在 `qml/components/` 下创建
5. 需要新数据 → 在 `settings_model.py` 添加 Property
6. 运行 `pyside6-qmllint` 检查语法

### 10.2 调试命令

```bash
# QML 语法检查
.venv/bin/pyside6-qmllint pyside6_gui/qml/

# 忽略 unqualified 警告（Python 注入的 context property）
.venv/bin/pyside6-qmllint --ignore unqualified pyside6_gui/qml/

# 运行应用
uv run python pyside6_gui/main.py
```

### 10.3 目录结构

```
pyside6_gui/
├── main.py                  # 入口：QGuiApplication + QQmlApplicationEngine
├── settings_model.py        # Python 数据模型
├── pyproject.toml           # 依赖声明
└── qml/
    ├── main.qml             # 主窗口
    ├── SettingsPage.qml     # 设置页（已实现）
    ├── HomePage.qml         # 主页（待实现）
    ├── LogPage.qml          # 日志页（待实现）
    ├── ToolsPage.qml        # 工具页（待实现）
    ├── AboutPage.qml        # 关于页（待实现）
    └── components/
        ├── SectionCard.qml
        ├── ConfigInput.qml
        ├── ConfigSwitch.qml
        ├── ConfigRadioGroup.qml
        ├── ConfigSlider.qml
        ├── ConfigCheckbox.qml
        ├── ConfigFilePicker.qml
        ├── ProgressBar.qml      # 待新增
        ├── LogViewer.qml        # 待新增
        ├── ToolCard.qml         # 待新增
        └── StatusBadge.qml      # 待新增
```
