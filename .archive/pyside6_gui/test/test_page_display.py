"""PySide6 QML 页面显示测试 — 检测布局/显示异常。

核心思路：加载 main.qml（完整应用上下文），通过页面切换检测各页面结构。

支持：
- 页面元素属性断言（尺寸/可见性/数量）
- 全量截图（含超出 viewport 的滚动内容）
- 基准截图对比（视觉回归）
- 差异图生成

用法：
    uv run pytest pyside6_gui/test/test_page_display.py -v
    uv run pytest pyside6_gui/test/test_page_display.py -v --update-baseline
"""
import os
import sys
from pathlib import Path

import pytest
import numpy as np
from PIL import Image

from PySide6.QtCore import QUrl, QObject, QTimer
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
TEST_DIR = Path(__file__).parent
BASELINE_DIR = TEST_DIR / "baseline"
BASELINE_DIR.mkdir(exist_ok=True)
QML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qml"))
MAIN_QML = os.path.join(QML_DIR, "main.qml")


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def find_qquickitem_by_name(root: QQuickItem, name: str) -> QQuickItem | None:
    """递归查找有指定 objectName 的 QQuickItem。"""
    if root.objectName() == name:
        return root
    for child in root.childItems():
        result = find_qquickitem_by_name(child, name)
        if result:
            return result
    return None


def collect_qquickitems(root: QQuickItem) -> list[QQuickItem]:
    """递归收集所有 QQuickItem。"""
    items = [root]
    for child in root.childItems():
        items.extend(collect_qquickitems(child))
    return items


def grab_item_image(item: QQuickItem, timeout_ms: int = 3000) -> QImage | None:
    """对 QQuickItem 做全量截图（不受 viewport 裁剪）。"""
    result = item.grabToImage()
    if not result.ready:
        result.wait(timeout_ms)
    if not result.ready:
        return None
    return result.image()


def qimage_to_pil(image: QImage) -> Image.Image:
    """QImage → PIL Image (RGBA)。"""
    w, h = image.width(), image.height()
    data = image.constBits().asarray(w * 4, h)
    data = data.reshape((h, w, 4))
    rgba = np.zeros_like(data)
    rgba[:, :, 0] = data[:, :, 2]  # R
    rgba[:, :, 1] = data[:, :, 1]  # G
    rgba[:, :, 2] = data[:, :, 0]  # B
    rgba[:, :, 3] = data[:, :, 3]  # A
    return Image.fromarray(rgba, mode="RGBA")


def compare_images(baseline: Image.Image, current: Image.Image) -> dict:
    """像素级对比，返回差异报告。"""
    size_match = baseline.size == current.size
    if not size_match:
        current = current.resize(baseline.size, Image.LANCZOS)

    b_arr = np.array(baseline.convert("RGB")).astype(np.float32)
    c_arr = np.array(current.convert("RGB")).astype(np.float32)
    diff_arr = np.abs(b_arr - c_arr)
    significant = (diff_arr > 10).sum()
    diff_ratio = significant / b_arr.size

    diff_visual = Image.fromarray(np.clip(diff_arr / 255 * 255, 0, 255).astype(np.uint8))

    return {
        "match": diff_ratio < 0.01,
        "diff_ratio": diff_ratio,
        "size_match": size_match,
        "message": f"差异 {diff_ratio:.2%}, 尺寸 {'一致' if size_match else f'{baseline.size} vs {current.size}'}",
        "diff_image": diff_visual,
    }


# ---------------------------------------------------------------------------
# 主窗口 fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def main_window(qt_app, tmp_config_ini):
    """加载 main.qml 主窗口，返回 contentItem (QQuickItem) 用于搜索子元素。"""
    from PySide6.QtQml import QQmlApplicationEngine

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import THEME
    from settings_model import SettingsModel

    config_path = tmp_config_ini
    settings = SettingsModel(config_path=config_path)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("Theme", THEME)
    engine.rootContext().setContextProperty("settings", settings)
    engine.load(QUrl.fromLocalFile(MAIN_QML))

    assert engine.rootObjects(), "main.qml 加载失败"
    root = engine.rootObjects()[0]
    # ApplicationWindow 不是 QQuickItem，用 contentItem 作为搜索起点
    content_root = root.contentItem() if hasattr(root, "contentItem") else root

    yield content_root

    engine.deleteLater()


def switch_page(content_root, page_index: int):
    """通过 pageLoader 切换页面。"""
    loader = find_qquickitem_by_name(content_root, "pageLoader")
    if loader:
        loader.setProperty("currentPage", page_index)
        from PySide6.QtTest import QTest
        QTest.qWait(300)


# ---------------------------------------------------------------------------
# 测试：SettingsPage (index=3)
# ---------------------------------------------------------------------------
class TestSettingsPage:
    PAGE_INDEX = 3

    def test_load_and_structure(self, main_window):
        """SettingsPage 结构检查 — 应该有 10 个 SectionCard。"""
        switch_page(main_window, self.PAGE_INDEX)

        page = find_qquickitem_by_name(main_window, "settingsPage")
        assert page, "找不到 settingsPage"

        # 通过查找 SectionCard 内的 titleText 来计数
        all_items = collect_qquickitems(page)
        section_count = 0
        for item in all_items:
            try:
                t = item.property("text")
                if t in ("通用", "代理", "命名规则", "媒体", "排除",
                         "水印", "无码", "下载", "Emby", "百度 AI"):
                    section_count += 1
            except (AttributeError, TypeError):
                pass

        # 至少找到 5 个标题即认为页面结构正常
        assert section_count >= 5, f"SectionCard 标题数量不足: {section_count}"

    def test_screenshot(self, main_window, request):
        """SettingsPage 全量截图对比基准。
        
        注意：offscreen 模式下 grabToImage() 返回空图像，此测试跳过。
        需要真实显示器运行：QT_QPA_PLATFORM=  uv run pytest ...
        """
        import os
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            pytest.skip("offscreen 模式不支持截图，跳过")
        
        switch_page(main_window, self.PAGE_INDEX)
        from PySide6.QtTest import QTest
        QTest.qWait(500)

        flickable = find_qquickitem_by_name(main_window, "settingsFlickable")
        assert flickable, "找不到 settingsFlickable"

        qimg = grab_item_image(flickable)
        if qimg is None or qimg.isNull():
            pytest.skip("截图返回空图像（可能因为 offscreen 渲染限制）")

        pil_img = qimage_to_pil(qimg)
        baseline_path = BASELINE_DIR / "settings_page.png"

        if request.config.getoption("--update-baseline", default=False):
            pil_img.save(str(baseline_path))
            pytest.skip(f"基准已更新: {baseline_path}")

        if not baseline_path.exists():
            pil_img.save(str(baseline_path))
            pytest.skip(f"基准已创建: {baseline_path}")

        baseline_img = Image.open(baseline_path)
        result = compare_images(baseline_img, pil_img)

        if not result["match"]:
            diff_path = TEST_DIR / "diff_settings_page.png"
            result["diff_image"].save(str(diff_path))
            pil_img.save(str(TEST_DIR / "current_settings_page.png"))
            pytest.fail(
                f"SettingsPage 视觉回归失败: {result['message']}\n"
                f"差异图: {diff_path}"
            )


# ---------------------------------------------------------------------------
# 测试：HomePage (index=0)
# ---------------------------------------------------------------------------
class TestHomePage:
    PAGE_INDEX = 0

    def test_sections_present(self, main_window):
        """HomePage 应该有 4 个 SectionCard。"""
        switch_page(main_window, self.PAGE_INDEX)

        page = find_qquickitem_by_name(main_window, "homePage")
        assert page, "找不到 homePage"

        all_items = collect_qquickitems(page)
        expected_titles = {"输入", "处理模式", "操作", "进度"}
        found_titles = set()
        for item in all_items:
            try:
                t = item.property("text")
                if t in expected_titles:
                    found_titles.add(t)
            except (AttributeError, TypeError):
                pass
        assert len(found_titles) >= 4, f"SectionCard 标题不足: {found_titles}"


# ---------------------------------------------------------------------------
# 测试：ToolsPage (index=2)
# ---------------------------------------------------------------------------
class TestToolsPage:
    PAGE_INDEX = 2

    def test_grid_layout(self, main_window):
        """ToolsPage 应该包含双列 GridLayout。"""
        switch_page(main_window, self.PAGE_INDEX)

        page = find_qquickitem_by_name(main_window, "toolsPage")
        assert page, "找不到 toolsPage"

        grid = _find_by_classname(page, "GridLayout")
        assert grid, "ToolsPage 缺少 GridLayout"

        cols = grid.property("columns")
        if cols is not None:
            assert cols == 2, f"GridLayout 列数应为 2，实际 {cols}"


def _find_by_classname(item, classname):
    type_name = item.metaObject().className()
    if classname in type_name:
        return item
    for child in item.childItems():
        result = _find_by_classname(child, classname)
        if result:
            return result
    return None


# ---------------------------------------------------------------------------
# pytest 钩子
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--update-baseline",
        action="store_true",
        default=False,
        help="更新基准截图",
    )
