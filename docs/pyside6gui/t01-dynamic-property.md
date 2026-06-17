# PySide6 动态 Property 陷阱

> 记录一个在 AVDC QML 项目中遇到的 PySide6 Property 注册问题及解决方案。

## 问题描述

使用 `setattr` 在类定义**之后**动态添加 `Property`，QML 访问时返回 `undefined`。

### 错误代码示例

```python
class SettingsModel(QObject):
    configLoaded = Signal()
    # ... 其他静态属性 ...

# ❌ 错误做法：类定义后通过 setattr 添加 Property
for config_key, (type_, default, qml_name) in SCHEMA.items():
    signal_name = f"{qml_name}Changed"
    signal = Signal(type_)
    setattr(SettingsModel, signal_name, signal)  # ❌ 不会注册到 meta-object
    
    getter = make_getter(config_key)
    setter = make_setter(config_key, signal_name)
    prop = Property(type_, getter, setter, notify=signal)
    setattr(SettingsModel, qml_name, prop)  # ❌ QML 访问返回 undefined
```

### 现象

```qml
// QML 中访问
Text { text: settings.successOutputFolder }
// 运行时警告：Unable to assign [undefined] to QString
```

## 原因分析

PySide6 的 `Property` 和 `Signal` 需要在 **类创建时** 注册到 Qt 的 meta-object 系统。Qt 的 meta-object 编译器（MOC）在类首次被处理时构建属性表，之后通过 `setattr` 添加的属性不会被识别。

QML 通过 meta-object 系统访问 Python 对象属性，如果属性不在 meta-object 中，返回 `undefined`。

## 解决方案

使用 **类工厂模式**，在 `type()` 创建类时就把所有 Property 和 Signal 放入 namespace：

```python
def _create_settings_model_class() -> type:
    """Build the SettingsModel class with all Properties in the namespace."""

    # 1. 基础 namespace
    namespace: dict = {
        '__module__': __name__,
        '__qualname__': 'SettingsModel',
        'configLoaded': Signal(),
        'configSaved': Signal(),
        'errorOccurred': Signal(str),
    }

    # 2. 动态生成 Signal + Property，加入 namespace
    for config_key, (type_, default, qml_name) in SCHEMA.items():
        signal_name = f"{qml_name}Changed"
        namespace[signal_name] = Signal(type_)  # ✅ 在类创建前加入
        
        getter = make_getter(config_key)
        setter = make_setter(config_key, signal_name)
        prop = Property(type_, getter, setter, notify=namespace[signal_name])
        namespace[qml_name] = prop  # ✅ 在类创建前加入

    # 3. 添加实例方法
    namespace['__init__'] = __init__
    namespace['load'] = load
    namespace['save'] = save
    # ...

    # 4. 创建类（此时所有 Property 已在 namespace 中）
    return type('SettingsModel', (QObject,), namespace)

SettingsModel = _create_settings_model_class()  # ✅ QML 可正常访问
```

## 验证

```python
# 验证 Property 是否正确注册
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtCore import QCoreApplication
from PySide6.QtQML import QQmlApplicationEngine

app = QCoreApplication([])
engine = QQmlApplicationEngine()

from pyside6_gui.settings_model import SettingsModel
s = SettingsModel()
engine.rootContext().setContextProperty('settings', s)

engine.loadData(b'''
import QtQuick 2.15
Item {
    Component.onCompleted: {
        console.log('successOutputFolder:', settings.successOutputFolder)
        console.log('mainMode:', settings.mainMode)
        Qt.quit()
    }
}
''', '')

# 正确输出：
# qml: successOutputFolder: JAV_output
# qml: mainMode: 1
```

## 适用场景

当需要动态生成多个相似 Property 时（如配置绑定、表单字段），使用类工厂模式而非 `setattr` 后绑定。

## 相关资源

- [PySide6 Property Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/Property.html)
- [Qt Meta-Object System](https://doc.qt.io/qt-6/metaobjects.html)
- `pyside6_gui/settings_model.py` — 完整实现示例
