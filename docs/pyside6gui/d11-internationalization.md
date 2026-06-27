# 国际化指南

> Qt 国际化机制、qsTr() 翻译函数、.ts/.qm 文件、翻译工作流。

## 1. 国际化基础

### 为什么需要国际化

- 支持多语言界面（中文/英文/日文）
- 适应不同地区习惯（日期、数字格式）
- 扩大用户群体

### Qt 国际化架构

```
QML/Python 源码
    ↓ qsTr() 标记
lupdate 提取
    ↓
.ts 翻译文件（XML）
    ↓ linguist 编辑
.qm 编译文件（二进制）
    ↓ 运行时加载
Qt Linguist System
```

## 2. QML 翻译标记

### qsTr() 函数

```qml
// 基础用法
Text {
    text: qsTr("保存配置")
}

// 带上下文
Text {
    text: qsTr("SettingsPage", "保存")
}

// 带参数
Text {
    text: qsTr("共 %1 个文件").arg(fileCount)
}
```

### 注意事项

```qml
// ❌ 错误：动态拼接字符串
Text {
    text: qsTr("成功") + ": " + count
}

// ✅ 正确：使用 %1 占位符
Text {
    text: qsTr("成功: %1").arg(count)
}

// ❌ 错误：未标记的硬编码
Text {
    text: "开始处理"  // 无法翻译
}

// ✅ 正确：使用 qsTr()
Text {
    text: qsTr("开始处理")
}
```

## 3. Python 翻译标记

### tr() 函数（QObject 子类）

```python
# settings_model.py
class SettingsModel(QObject):
    @Slot()
    def save(self):
        try:
            # ...
            self.configSaved.emit()
        except Exception as e:
            self.errorOccurred.emit(self.tr("保存配置失败: %1").arg(str(e)))
```

### QT_TRANSLATE_NOOP（非 QObject）

```python
# 用于模块级常量
ERROR_MESSAGES = {
    "config_load": QT_TRANSLATE_NOOP("Errors", "加载配置失败"),
    "config_save": QT_TRANSLATE_NOOP("Errors", "保存配置失败"),
}
```

## 4. 翻译工作流

### 步骤 1：提取翻译字符串

```bash
# 提取 QML + Python 中的 qsTr/tr
.venv/bin/pyside6-lupdate pyside6_gui/qml/*.qml \
                          pyside6_gui/qml/components/*.qml \
                          pyside6_gui/*.py \
                          -ts translations/zh_CN.ts
```

### 步骤 2：编辑翻译文件

```bash
# 使用 Qt Linguist GUI
.venv/bin/pyside6-linguist translations/zh_CN.ts
```

### 步骤 3：编译翻译文件

```bash
.venv/bin/pyside6-lrelease translations/zh_CN.ts -qm translations/zh_CN.qm
```

### 步骤 4：加载翻译

```python
# main.py
from PySide6.QtCore import QTranslator, QLocale

translator = QTranslator()
translator.load(QLocale("zh_CN"), "translations/", ".qm")
app.installTranslator(translator)
```

## 5. 日期/数字本地化

### QLocale 格式化

```python
from PySide6.QtCore import QLocale

locale = QLocale(QLocale.Chinese, QLocale.China)

# 日期
date_str = locale.toString(QDate.currentDate(), QLocale.ShortFormat)
# 输出: 2024/6/27

# 数字
num_str = locale.toString(1234567.89, 'f', 2)
# 输出: 1,234,567.89
```

### QML 中使用

```qml
import Qt.labs.platform 1.1

Text {
    // 使用系统本地化格式
    text: Qt.formatDate(new Date(), Locale.ShortFormat)
}
```

## 6. 项目现状与待办

### 当前状态

- 所有界面文字硬编码为中文
- 未使用 qsTr()/tr() 标记
- 无 .ts/.qm 翻译文件

### 实施计划

1. **标记阶段**：全局搜索替换硬编码文字为 qsTr()
2. **提取阶段**：运行 lupdate 生成 .ts 文件
3. **翻译阶段**：使用 Linguist 完成英文翻译
4. **集成阶段**：main.py 加载 .qm，添加语言切换 UI

### 预估工作量

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| 标记 | 2-3 小时 | 约 200 处文字需标记 |
| 提取 | 5 分钟 | 自动化脚本 |
| 翻译 | 4-6 小时 | 需专业翻译 |
| 集成 | 1 小时 | 代码改动小 |

## 7. 测试方法

### 伪翻译测试

```bash
# 使用伪翻译工具生成测试 .qm
# 特征：所有文字替换为 [!!! 原始文字 !!!]
.venv/bin/pyside6-lrelease pseudotranslation.ts -qm pseudo.qm
```

### 验证翻译覆盖

```bash
# 统计未翻译条目
grep -c '<translation type="unfinished">' translations/zh_CN.ts
# 输出: 0（全部已翻译）
```
