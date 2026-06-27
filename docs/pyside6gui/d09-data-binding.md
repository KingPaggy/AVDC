# Python ↔ QML 数据绑定详解

> Property 注册机制、Signal 通知链、双向绑定防循环、调试技巧。

## 1. 绑定机制总览

### 绑定链路

```
Python Property (getter/setter)
    ↓ notify Signal
Qt Meta-Object System
    ↓ setContextProperty()
QML Context Property
    ↓ property binding
QML UI Element
```

### 核心概念

| 概念 | Python 侧 | QML 侧 |
|------|-----------|--------|
| 属性定义 | `Property(type, getter, setter, notify=Signal)` | `property int value: 0` |
| 属性访问 | `obj.attr` | `obj.attr` |
| 属性变更通知 | `notifySignal.emit()` | 自动重新评估 binding |
| 双向绑定 | setter 被调用 | `onXxxChanged: obj.xxx = newValue` |

## 2. Property 注册流程

### 两种注册方式

| 方式 | 语法 | 适用场景 |
|------|------|----------|
| 装饰器 | `@Property(type, notify=Signal)` | 静态属性，数量少 |
| 类工厂 | `namespace[key] = Property(...)` | 动态属性，数量多 |

### 装饰器方式（ProcessingModel）

```python
# processing_model.py
class ProcessingModel(QObject):
    progressValueChanged = Signal(float)

    @Property(float, notify=progressValueChanged)
    def progressValue(self):
        return self._progress_value

    @progressValue.setter
    def progressValue(self, value: float):
        if self._progress_value != value:
            self._progress_value = value
            self.progressValueChanged.emit(value)
```

### 类工厂方式（SettingsModel）

```python
# settings_model.py — 38 个属性动态生成
def _create_settings_model_class() -> type:
    namespace = {'__module__': __name__, ...}

    for config_key, (type_, default, qml_name) in SCHEMA.items():
        signal_name = f"{qml_name}Changed"
        namespace[signal_name] = Signal(type_)

        getter = make_getter(config_key)   # 闭包捕获 key
        setter = make_setter(config_key, signal_name)
        namespace[qml_name] = Property(type_, getter, setter, notify=namespace[signal_name])

    return type('SettingsModel', (QObject,), namespace)
```

### 为什么不能在类外 setattr？

PySide6 的 Property 必须在类创建时注册到 Qt meta-object 系统。类创建后再 setattr，QML 访问返回 `undefined`。详见 [t01-dynamic-property.md](t01-dynamic-property.md)。

## 3. Signal 通知链

### Python → QML 的变更传播

当 Python 侧 Property 值变化时，必须发射 notify Signal，QML 才能感知：

```
Python setter 修改内部值
    ↓ emit(signal)
Qt Meta-Object 分发
    ↓
QML binding 重新计算
    ↓
UI 刷新显示
```

### 实际示例

```python
# Python 侧
@Property(float, notify=progressValueChanged)
def progressValue(self):
    return self._progress_value

def _emit_progress(self, value: float):
    self._progress_value = value
    self.progressValueChanged.emit(value)  # ← 必须发射
```

```qml
// QML 侧 — 自动响应
ProgressBar {
    progressValue: processing.progressValue  // binding 自动重算
}
```

### 多 Signal 场景

ProcessingModel 有两个 Signal 同时关联 `progressValue`：

```python
progressChanged = Signal(float)          # 纯信号，QML Connections 接收
progressValueChanged = Signal(float)     # Property notify，触发 binding 重算

def _emit_progress(self, value: float):
    self._progress_value = value
    self.progressValueChanged.emit(value)  # 触发 binding
    self.progressChanged.emit(value)       # 触发 Connections
```

QML 两种接收方式：

```qml
// 方式 1：binding（推荐，自动响应）
ProgressBar { progressValue: processing.progressValue }

// 方式 2：Connections（手动处理）
Connections {
    target: processing
    function onProgressChanged(value) { console.log(value) }
}
```

## 4. 双向绑定防循环

### 问题场景

当 QML UI 和 Python Property 互相绑定同一值时，可能形成死循环：

```
UI 变更 → onTextChanged → Python setter → notify → binding → UI 变更 → ...
```

### _suppressUpdate 模式

项目中所有 Config* 组件使用 `_suppressUpdate` 标志打破循环：

```qml
// ConfigInput.qml
property string textValue: ""
property bool _suppressUpdate: false

TextField {
    id: input
    // Python → QML：外部更新时抑制回写
    onTextChanged: {
        if (!root._suppressUpdate && root.textValue !== text) {
            root.textValue = text
        }
    }
}

// QML → Python：值变化时更新 UI
onTextValueChanged: {
    if (!_suppressUpdate && input.text !== textValue) {
        _suppressUpdate = true
        input.text = textValue
        _suppressUpdate = false
    }
}
```

### 流程分析

```
场景 A：用户输入
  TextField.onTextChanged → textValue 更新 → Python setter → notify →
  onTextValueChanged 触发 → input.text === textValue（已同步）→ 不操作 ✅

场景 B：外部重置
  Python resetToDefaults() → notify → onTextValueChanged 触发 →
  _suppressUpdate = true → input.text = textValue →
  _suppressUpdate = false → TextField.onTextChanged 触发 →
  _suppressUpdate = false 但 textValue === text → 不操作 ✅
```

## 5. 常见陷阱与解法

### 陷阱 1：类外 setattr 注册 Property

❌ 错误：
```python
class MyModel(QObject):
    pass

setattr(MyModel, 'myProp', Property(str, getter, setter, notify=sig))
# QML 访问返回 undefined
```

✅ 正确：使用类工厂模式（见 [t01-dynamic-property.md](t01-dynamic-property.md)）。

### 陷阱 2：忘记发射 notify Signal

```python
def set_value(self, v):
    self._value = v
    # ❌ 忘记 self.valueChanged.emit(v)
    # QML 不会刷新
```

**规则**：setter 修改内部状态后，必须发射对应的 notify Signal。

### 陷阱 3：跨线程直接修改 Property

❌ 错误：
```python
# Worker 线程中直接修改
self._progress = 0.5
self.progressChanged.emit(0.5)  # 非主线程发射 Signal → 崩溃
```

✅ 正确：
```python
# Worker 线程通过 QueuedConnection 回到主线程
QMetaObject.invokeMethod(self, "_finishProcessing", Qt.QueuedConnection)
```

### 陷阱 4：Context Property 注册顺序

`main.py` 中注册顺序有依赖关系（详见 d01）：

```
1. Theme        ← 所有组件依赖
2. settings     ← HomePage/SettingsPage 依赖
3. logModel     ← EventBus → LogBridge → LogFilterModel
4. processing   ← 依赖 settings
5. windowController ← 必须在 engine.load() 之前
```

## 6. 调试技巧

### 查看 Property 是否注册

```python
# 验证 Property 是否在 meta-object 中
obj = SettingsModel()
meta = obj.metaObject()
for i in range(meta.propertyCount()):
    p = meta.property(i)
    print(p.name(), p.typeName())
```

### QML 侧打印绑定值

```qml
// 方法 1：直接 console.log
Text {
    text: settings.proxy
    Component.onCompleted: console.log("proxy:", settings.proxy)
}

// 方法 2：绑定变化时打印
Binding {
    target: someObject
    property: "value"
    value: settings.timeout
    onValueChanged: console.log("timeout changed:", value)
}
```

### 验证 Signal 是否发射

```python
# Python 侧手动连接测试
model = SettingsModel()
model.timeoutChanged.connect(lambda v: print(f"timeout -> {v}"))
model.timeout = 15  # 应输出: timeout -> 15
```

### 使用 QSignalSpy 单元测试

```python
from PySide6.QtTest import QSignalSpy

spy = QSignalSpy(model.timeoutChanged)
model.timeout = 20
assert spy.count() == 1
assert spy.at(0)[0] == 20
```

### 调试 Context Property 注入

```python
# 确认 Context Property 已设置
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("settings", settings)

# 验证
prop = engine.rootContext().contextProperty("settings")
print(type(prop))  # 应输出 <class 'SettingsModel'>
```
