# PySide6 GUI 测试策略

> 测试架构、8 个测试文件的组织、Mock 策略、QML 截图回归、运行方法。

## 1. 测试架构

### 测试文件索引

| 文件 | 类别 | 测试目标 |
|------|------|----------|
| `test_settings_model.py` | 单元 | SCHEMA 默认值、Property 变更信号、save/load/reset、错误处理 |
| `test_processing_model.py` | 单元 | 信号骨架、状态切换、stop 标志 |
| `test_processing_model_engine.py` | 单元+集成 | `start_batch`/`start_single` 完整生命周期（mock CoreEngine） |
| `test_log_bridge.py` | 单元 | EventBus → Qt Signal 桥接、3 种日志级别转发 |
| `test_integration.py` | 集成 | ProcessingModel + CoreEngine + EventBus 协同 |
| `test_qml_loading.py` | 集成 | QML 文件解析、Context Property 注入 |
| `test_theme.py` | 单元 | Theme 常量合法性（颜色格式、间距网格、字号层级） |
| `test_page_display.py` | 视觉回归 | 页面结构验证 + 截图基准对比 |

### 运行命令

```bash
# 运行全部 GUI 测试
uv run pytest pyside6_gui/test/ -v

# 运行单个文件
uv run pytest pyside6_gui/test/test_settings_model.py -v

# 更新截图基准
uv run pytest pyside6_gui/test/test_page_display.py -v --update-baseline
```

## 2. 关键约束

### QT_QPA_PLATFORM=offscreen

```python
# conftest.py 顶部 — 必须在任何 Qt import 之前设置
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
```

### 共享 Fixtures

| Fixture | 职责 |
|---------|------|
| `qt_app` | `QGuiApplication` 单例，跨测试共享 |
| `tmp_config_ini` | 临时 config.ini（含完整 section） |
| `settings` | 连接到临时 config 的 `SettingsModel` |
| `qml_engine` | 已注入 `Theme` + `settings` Context Property 的 `QQmlApplicationEngine` |

## 3. Mock 策略

### MockEventBus

用于隔离测试 LogBridge，避免依赖真实 EventBus：

```python
class MockEventBus:
    def on(self, event_type, handler): ...
    def off(self, event_type, handler): ...
    def emit(self, event_type, **kwargs): ...
```

### Mock CoreEngine

`test_processing_model_engine.py` 使用 `unittest.mock.patch` 拦截 CoreEngine 构造：

```python
with patch.object(core._services.orchestrator, "CoreEngine") as MockEngine:
    mock_engine = MagicMock()
    mock_engine.process_batch.return_value = {"total": 1, "success": 1, "failed": 0}
    MockEngine.return_value = mock_engine
    # ... 验证信号发射
```

### QSignalSpy

所有 Qt Signal 测试均使用 `QSignalSpy` 验证发射次数和参数：

```python
spy = QSignalSpy(model.isProcessingChanged)
model.isProcessing = True
assert spy.count() == 1
assert spy.at(0)[0] is True
```

## 4. 截图回归测试

`test_page_display.py` 实现了完整的视觉回归流水线：

```
加载 main.qml → 切换到目标页 → grabToImage() → PIL RGBA 对比 → 差异图生成
```

### 工具函数

| 函数 | 作用 |
|------|------|
| `find_qquickitem_by_name(root, name)` | 递归查找 objectName 对应的 QQuickItem |
| `grab_item_image(item)` | 全量截图（不受 viewport 裁剪） |
| `qimage_to_pil(image)` | QImage → PIL RGBA 转换 |
| `compare_images(baseline, current)` | 像素级对比，返回差异比例 + 差异图 |

### 差异判定

```python
significant = (diff_arr > 10).sum()   # 容差 10/255
diff_ratio = significant / b_arr.size
match = diff_ratio < 0.01              # 1% 以下视为通过
```

### 输出文件

| 文件 | 说明 |
|------|------|
| `baseline/xxx_page.png` | 基准截图 |
| `diff_xxx_page.png` | 差异热力图 |
| `current_xxx_page.png` | 当前截图 |

> ⚠️ offscreen 模式下 `grabToImage()` 返回空图像，截图测试自动跳过。需真实显示器运行。

## 5. 测试分类详解

### SettingsModel 测试

| 类 | 覆盖范围 |
|----|----------|
| `TestSettingsModelDefaults` | 8 个默认值断言 |
| `TestSettingsModelModelPropertyChanges` | 信号发射（mainModeChanged, proxyTypeChanged 等） |
| `TestSettingsModelSaveLoad` | save/load 持久化 + 信号 |
| `TestSettingsModelReset` | resetToDefaults 恢复 + 信号 |
| `TestSettingsModelErrorHandling` | 不存在文件、新目录保存 |

### ProcessingModel 测试

| 类 | 覆盖范围 |
|----|----------|
| `TestProcessingModelSkeleton` | 信号/Slot 存在性、状态切换 |
| `TestProcessingModelBatch` | start_batch 生命周期（mock CoreEngine） |
| `TestProcessingModelSingle` | start_single 生命周期（mock CoreEngine） |
| `TestProcessingModelStop` | stop() 标志设置与重置 |

### Theme 测试

| 类 | 覆盖范围 |
|----|----------|
| `TestThemeColors` | 合法 hex、无纯黑/纯白 |
| `TestThemeSpacing` | 正值、4pt 网格、递增、精确值 |
| `TestThemeRadii` | 正值、递增 |
| `TestThemeTypography` | 字号层级完整性 |
| `TestThemeSidebar` | Min < Ideal < Max，IconOnly < Min |
| `TestThemeWindow` | Default > Min |
| `TestThemeAnimation` | 递增、合理范围 |
| `TestThemeCompleteness` | 必要 key 全存在 |
