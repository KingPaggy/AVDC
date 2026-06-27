# 调试指南

> QML 控制台错误、Python 模型调试、日志系统、性能分析工具。

## 1. QML 调试

### 控制台输出

```qml
// 基础打印
console.log("当前值:", settings.timeout)

// 带上下文
console.log("[SettingsPage] 保存配置:", JSON.stringify(settings))

// 错误级别
console.warn("警告：值为空")
console.error("错误：绑定失败")
```

### 常见 QML 错误

| 错误信息 | 原因 | 解决 |
|----------|------|------|
| `Unable to assign [undefined]` | Property 未注册 | 检查类工厂是否包含该属性 |
| `ReferenceError: xxx is not defined` | Context Property 未注入 | 检查 main.py 注册顺序 |
| `Cannot assign to read-only property` | Property 无 setter | 添加 setter 或使用只读绑定 |
| `Component is not ready` | QML 文件语法错误 | 运行 qmllint 检查 |

### QML Lint

```bash
# 检查语法错误
.venv/bin/pyside6-qmllint pyside6_gui/qml/main.qml

# 输出示例
# Warning: main.qml:42:5: Unused import
#   import QtQuick.Controls 2.15
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

## 2. Python 模型调试

### 验证 Property 注册

```python
# 列出所有注册的 Property
obj = SettingsModel()
meta = obj.metaObject()
print(f"共 {meta.propertyCount()} 个属性:")
for i in range(meta.propertyCount()):
    p = meta.property(i)
    print(f"  {p.name()}: {p.typeName()}")
```

### 验证 Signal 连接

```python
# 检查 Signal 是否有订阅者
model = SettingsModel()
print(f"timeoutChanged 订阅者: {model.timeoutChanged.receivers()}")
# 输出: 0（无订阅）或 >0（QML 已绑定）
```

### 验证 Context Property

```python
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("settings", settings)

# 检查是否成功注入
prop = engine.rootContext().contextProperty("settings")
print(f"settings 类型: {type(prop)}")
# 应输出: <class 'SettingsModel'>
```

### 日志输出

```python
import logging

logger = logging.getLogger(__name__)

def save(self):
    logger.debug(f"保存配置到: {self._config_path}")
    try:
        # ...
        logger.info("配置保存成功")
    except Exception as e:
        logger.error(f"保存失败: {e}", exc_info=True)
```

## 3. 日志系统调试

### 日志链路追踪

```
EventBus.emit(LOG_INFO, message="开始处理")
    ↓
LogBridge._on_log_info(event)
    ↓ logReceived.emit("INFO", "开始处理")
LogFilterModel.addEntry("INFO", "开始处理")
    ↓ _source_model.append(entry)
LogListModel.beginInsertRows() → endInsertRows()
    ↓ countChanged.emit()
LogViewer.ListView 更新显示
```

### 检查日志是否到达

```python
# 在 LogBridge 中添加调试
class LogBridge(QObject):
    def _on_log_info(self, event):
        message = getattr(event, "message", "")
        print(f"[DEBUG] LogBridge 收到: {message}")  # ← 调试
        self.logReceived.emit("INFO", message)
```

### 检查过滤是否生效

```python
# 验证过滤模型
log_model = LogFilterModel(max_entries=100)
log_model.addEntry("INFO", "测试日志")
print(f"过滤级别: {log_model.filterLevel}")
print(f"源模型条数: {log_model._source_model.count}")
print(f"过滤模型条数: {log_model._filtered_model.count}")
```

## 4. 性能分析

### Qt Creator QML Profiler

```bash
# 启动性能分析
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pyside6_gui.main

# 在 Qt Creator 中：
# Analyze → QML Profiler → Attach to Running Application
```

### 常见性能问题

| 问题 | 症状 | 解决 |
|------|------|------|
| ListView 卡顿 | 滚动时帧率低 | 使用 QAbstractListModel 虚拟化 |
| 频繁 binding 重算 | CPU 占用高 | 检查循环依赖，优化 Signal 发射 |
| 内存泄漏 | 内存持续增长 | 检查 QObject 父子关系，及时 deleteLater |

### 日志系统优化

```python
# LogListModel 已实现：
# 1. 虚拟化：ListView 只渲染可见行
# 2. 限制条数：max_entries=1000，自动删除旧日志
# 3. 批量删除：excess > 0 时一次性删除多条

# 如果仍有性能问题：
# - 降低 max_entries（如 500）
# - 在 filterLevel="error" 时跳过 INFO 日志
```

## 5. 截图调试

### 页面截图

```python
from PySide6.QtGui import QImage

def screenshot_qquickitem(item, path):
    """截图 QQuickItem（含超出 viewport 的内容）"""
    result = item.grabToImage()
    if result.ready:
        result.image().save(path)
        print(f"截图已保存: {path}")
    else:
        result.wait(3000)
        if result.ready:
            result.image().save(path)
        else:
            print("截图失败（offscreen 模式限制）")
```

### 对比基准截图

```python
from PIL import Image
import numpy as np

def compare_images(baseline_path, current_path):
    """像素级对比，输出差异比例"""
    baseline = np.array(Image.open(baseline_path))
    current = np.array(Image.open(current_path))
    
    diff = np.abs(baseline - current)
    significant = (diff > 10).sum()
    ratio = significant / baseline.size
    
    print(f"差异比例: {ratio:.2%}")
    return ratio < 0.01  # 1% 以下视为通过
```

## 6. 常用调试工具

### Python 调试

| 工具 | 用途 | 命令 |
|------|------|------|
| `pdb` | 交互式调试 | `python -m pdb script.py` |
| `breakpoint()` | 断点 | Python 3.7+ 内置 |
| `logging` | 日志输出 | `logger.debug/info/error` |
| `traceback` | 异常堆栈 | `traceback.print_exc()` |

### QML 调试

| 工具 | 用途 | 命令 |
|------|------|------|
| `console.log()` | 打印 | QML 内置 |
| `qmllint` | 语法检查 | `pyside6-qmllint file.qml` |
| Qt Creator | 可视化调试 | GUI 工具 |
| QML Profiler | 性能分析 | Qt Creator 内置 |

### Qt 环境变量

```bash
# 启用详细日志
QT_LOGGING_RULES="qt.qpa.*=true"

# 禁用硬件加速（调试渲染问题）
QT_QUICK_BACKEND=software

# 启用 QML 调试
QML_DEBUG_PORT=3768
```

## 7. 调试 Checklist

### QML 加载失败

- [ ] 检查 QML 文件路径是否正确
- [ ] 运行 `qmllint` 检查语法
- [ ] 检查 import 路径是否添加
- [ ] 查看控制台错误信息

### Property 返回 undefined

- [ ] 检查 Property 是否在类工厂 namespace 中
- [ ] 验证 `metaObject().propertyCount()` 包含该属性
- [ ] 检查 Context Property 注入顺序
- [ ] 确认 getter 返回值类型正确

### Signal 未触发

- [ ] 检查 `emit()` 是否被调用
- [ ] 验证 QML 侧是否正确连接（`Connections` 或 binding）
- [ ] 使用 `QSignalSpy` 单元测试验证
- [ ] 检查跨线程问题（需 QueuedConnection）

### 日志不显示

- [ ] 检查 EventBus 是否发射事件
- [ ] 验证 LogBridge.connect() 已调用
- [ ] 检查 filterLevel 是否过滤掉该级别
- [ ] 验证 LogListModel.append() 被调用
