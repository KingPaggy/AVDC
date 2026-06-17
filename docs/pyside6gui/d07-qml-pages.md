# QML 页面详解

> 5 个页面（Home / Settings / Log / Tools / About）的内部结构、数据绑定、交互流程。

## 1. 页面通用布局模式

所有页面遵循统一布局模板，确保视觉一致性：

```qml
Item {
    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: width                    // 禁止水平滚动

        Column {                               // 非 Layout 父元素 → 用 implicitHeight
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(
                parent.width - Theme.spacingXL * 2,
                Theme.maxContentWidth          // ← 各页面用不同常量
            )
            spacing: Theme.spacingLG

            Item { implicitHeight: Theme.spacingXL }   // 顶部留白
            SectionCard { ... }
            SectionCard { ... }
            Item { implicitHeight: Theme.spacingXL }   // 底部留白
        }
    }
}
```

### 三种宽度变体

| 页面 | 宽度常量 | 值 | 原因 |
|------|---------|-----|------|
| HomePage / AboutPage | `maxContentWidth` | 680 | 标准内容宽度 |
| SettingsPage | `maxFormContentWidth` | 760 | 表单较长，加宽减少滚动 |
| ToolsPage | `maxToolContentWidth` | 840 | 2 列网格需要更多横向空间 |

---

## 2. HomePage — 工作台

**文件**：`qml/HomePage.qml`

### 结构

4 个 SectionCard：
- **输入**：ConfigFilePicker（输入目录）+ ConfigInput（排除文件夹）
- **处理模式**：ConfigRadioGroup（刮削/整理）
- **操作**：[开始处理] [停止] 按钮
- **进度**：ProgressBar + 3 个 StatusBadge（成功/失败/跳过）

### 数据绑定

```qml
ConfigFilePicker { textValue: settings.successOutputFolder }
ConfigRadioGroup { selectedValue: settings.mainMode }
```

### 按钮互斥

```qml
Button {
    text: "开始处理"
    enabled: !processing.isProcessing
    onClicked: processing.startBatch(settings.successOutputFolder, settings.escapeFolders, settings.mainMode)
}
Button {
    text: "停止"
    enabled: processing.isProcessing
    onClicked: processing.stop()
}
```

### 进度展示

```qml
ProgressBar { progressValue: processing.progressValue; statusText: processing.statusText }
StatusBadge { status: "success"; text: "成功: " + processing.successCount }
StatusBadge { status: "error"; text: "失败: " + processing.failCount }
StatusBadge { status: "info"; text: "跳过: " + processing.skipCount }
```

### 完整交互流程

```
用户点击 [开始处理]
    ↓
processing.startBatch(path, escape, mode)
    │ SettingsModel.to_app_config() → AppConfig
    │ threading.Thread(target=_worker)
    ↓ Worker 线程
CoreEngine.process_batch()
    │ 每文件: on_progress() → progressValue 更新 → ProgressBar 刷新
    │ 成功: on_success() → successCount++ → movieProcessed.emit(true)
    │ 失败: on_failure() → failCount++ → movieProcessed.emit(false)
    │ 完成: QMetaObject.invokeMethod("_finishProcessing") → 回到主线程
    ↓
UI 更新: isProcessing=false, progressValue=1.0, 按钮恢复
```

---

## 3. SettingsPage — 配置表单

**文件**：`qml/SettingsPage.qml`

### 10 个分组

| # | SectionCard | 主要字段 |
|---|-------------|----------|
| 1 | **通用** | mainMode, softLink, switchDebug, updateCheck, saveLog, failedFileMove, successOutputFolder, failedOutputFolder |
| 2 | **代理** | proxyType, proxy, timeout, retry |
| 3 | **命名规则** | folderName, namingMedia, namingFile |
| 4 | **媒体** | mediaType, subType, mediaPath |
| 5 | **排除** | escapeFolders, escapeString, literals |
| 6 | **水印** | posterMark, thumbMark, markSize, markType(SUB/LEAK/UNCENSORED), markPos |
| 7 | **无码** | uncensoredPoster, uncensoredPrefix |
| 8 | **下载** | nfoDownload, posterDownload, fanartDownload, thumbDownload, extrafanartDownload, extrafanartFolder |
| 9 | **Emby** | embyUrl, apiKey |
| 10 | **百度 AI** | baiduAppId, baiduApiKey, baiduSecretKey |

### 水印类型 — 多 Checkbox 联动

3 个 ConfigCheckbox 共同写入逗号分隔字符串 `markType`：

```qml
ConfigCheckbox {
    id: markSubCheckbox
    checked: settings.markType.indexOf("SUB") >= 0   // 读取：字符串包含
    onCheckedChanged: _updateMarkType()
}

function _updateMarkType() {
    var parts = []
    if (markSubCheckbox.checked) parts.push("SUB")
    if (markLeakCheckbox.checked) parts.push("LEAK")
    if (markUncensoredCheckbox.checked) parts.push("UNCENSORED")
    settings.markType = parts.join(",")   // 写入："SUB,LEAK" 或 ""
}
```

### 底部操作按钮

```qml
Button { text: "恢复默认"; onClicked: settings.resetToDefaults() }
Button { text: "保存配置"; highlighted: true; onClicked: settings.save() }
```

保存后触发 `settings.configSaved` 信号 → Toast 通知。

---

## 4. LogPage — 日志

**文件**：`qml/LogPage.qml`

### 结构

```
┌─ ColumnLayout (fill parent) ─────────────┐
│  ┌─ Rectangle: 过滤栏 ──────────────────┐│
│  │  过滤: [全部] [错误] [警告] [信息] [调试]│
│  │                    1234 条  [清空] [导出]│
│  └──────────────────────────────────────┘│
│  ┌─ LogViewer (fill remaining) ─────────┐│
│  │  12:34:56 INFO  开始批量处理           ││
│  │  12:34:57 INFO  [1/100] SSIS-487.mp4  ││
│  │  12:34:58 ERROR 失败: timeout          ││
│  │  ...                                  ││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### 过滤栏 — Repeater 模式

用 `Repeater` 动态生成 5 个过滤按钮，避免手写重复代码：

```qml
Repeater {
    model: [
        {value: "all",   text: "全部"},
        {value: "error", text: "错误"},
        {value: "warn",  text: "警告"},
        {value: "info",  text: "信息"},
        {value: "debug", text: "调试"}
    ]

    Button {
        text: modelData.text
        flat: true
        // 选中态：accentColor；未选中：tertiaryText
        palette.buttonText: logModel.filterLevel === modelData.value
            ? Theme.accentColor
            : Theme.tertiaryText

        onClicked: logModel.filterLevel = modelData.value
    }
}
```

### 与 LogFilterModel 的绑定

- `logModel.totalCount` → 总日志数
- `logModel.filterLevel = "error"` → Python 侧重建过滤列表
- `logModel.clearAll()` → 清空日志
- `logModel.filteredModel` → QAbstractListModel，ListView 直接绑定

过滤在 **Python 侧** 完成，比 QML delegate `visible: false` 更高效。

---

## 5. ToolsPage — 工具

**文件**：`qml/ToolsPage.qml`

### 结构

```
┌─ SectionCard: 文件工具 ──────────────────┐
│  ┌─ GridLayout (2 列) ─────────────────┐│
│  │  [批量重命名]    [封面裁剪]           ││
│  │  [水印处理]      [格式转换]           ││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
┌─ SectionCard: 媒体库工具 ────────────────┐
│  ┌─ GridLayout (2 列) ─────────────────┐│
│  │  [Emby 同步]     [NFO 生成器]        ││
│  │  [元数据编辑]    [重复检测]           ││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### GridLayout 用法

```qml
GridLayout {
    columns: 2
    columnSpacing: Theme.spacingMD
    rowSpacing: Theme.spacingMD
    ToolCard {
        title: "批量重命名"
        description: "按命名规则批量重命名影片文件"
        Layout.fillWidth: true
        onClicked: toast.show("批量重命名（待实现）")
    }
}
```

**当前状态**：所有 ToolCard 点击显示 Toast 占位，功能待实现。

---

## 6. AboutPage — 关于

**文件**：`qml/AboutPage.qml`

### 结构

```qml
Rectangle {
    anchors.centerIn: parent
    width: Theme.aboutCardWidth      // 400
    height: Theme.aboutCardHeight    // 320
    radius: Theme.radiusXL
    ColumnLayout {
        Text { text: "AVDC"; font.pixelSize: Theme.fontLargeTitle }
        Text { text: "版本 0.1.0" }
        Rectangle { height: 1; width: Theme.aboutDividerWidth }
        Text { text: "PySide6\nlxml\nBeautifulSoup4\n..." }
    }
}
```

无 ScrollView，无数据绑定，纯静态展示。

---

## 7. 页面与 Python 模型的交互总结

| 页面 | 读取 settings.* | 写入 settings.* | 调用 settings 方法 | 使用 processing.* |
|------|----------------|----------------|-------------------|------------------|
| HomePage | successOutputFolder, escapeFolders, mainMode | ✅ 双向绑定 | — | startBatch(), stop(), isProcessing, progressValue, successCount, failCount, skipCount, statusText |
| SettingsPage | 全部 38 个字段 | ✅ 双向绑定 | save(), resetToDefaults() | — |
| LogPage | — | — | — | — |
| ToolsPage | — | — | — | — |
| AboutPage | — | — | — | — |

### 页面间共享设置

HomePage 和 SettingsPage 共享相同的 settings 字段（如 `successOutputFolder`、`mainMode`）。在任一页面修改会立即反映到另一页面（Qt Property 的 notify 信号触发 QML 重新绑定）。
