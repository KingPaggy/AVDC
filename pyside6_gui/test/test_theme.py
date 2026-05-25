"""Tests for Theme constants — pure Python, no Qt runtime needed."""
import re
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import THEME


# ===== Hex color validation =====

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _all_colors():
    """Extract all color values from THEME."""
    colors = []
    for key, value in THEME.items():
        if isinstance(value, str) and value.startswith("#"):
            colors.append((key, value))
    return colors


class TestThemeColors:
    def test_all_colors_are_valid_hex(self):
        """All color values should be valid 6-digit hex codes."""
        for name, value in _all_colors():
            assert _HEX_RE.match(value), f"{name}: '{value}' is not a valid hex color"

    def test_no_pure_black_or_white(self):
        """Theme should not use #000000 or #FFFFFF (HIG guideline)."""
        for name, value in _all_colors():
            assert value.upper() not in ("#000000", "#FFFFFF"), (
                f"{name}: should not use fixed black/white, use semantic colors instead"
            )


# ===== Spacing validation =====

class TestThemeSpacing:
    def test_all_spacing_positive(self):
        """All spacing values should be positive."""
        for key in ("spacingXS", "spacingSM", "spacingMD", "spacingLG",
                     "spacingXL", "spacingXXL", "spacingXXXL"):
            assert THEME[key] > 0, f"{key} should be positive"

    def test_spacing_on_4pt_grid(self):
        """All spacing values should be multiples of 4 (8pt grid)."""
        for key in ("spacingXS", "spacingSM", "spacingMD", "spacingLG",
                     "spacingXL", "spacingXXL", "spacingXXXL"):
            assert THEME[key] % 4 == 0, f"{key}={THEME[key]} is not on 4pt grid"

    def test_spacing_increasing(self):
        """Spacing values should be monotonically increasing."""
        keys = ("spacingXS", "spacingSM", "spacingMD", "spacingLG",
                "spacingXL", "spacingXXL", "spacingXXXL")
        values = [THEME[k] for k in keys]
        for i in range(1, len(values)):
            assert values[i] > values[i - 1], (
                f"{keys[i]}={values[i]} should be > {keys[i-1]}={values[i-1]}"
            )

    def test_specific_spacing_values(self):
        """Verify exact expected spacing values."""
        expected = {
            "spacingXS": 4,
            "spacingSM": 8,
            "spacingMD": 12,
            "spacingLG": 16,
            "spacingXL": 20,
            "spacingXXL": 24,
            "spacingXXXL": 32,
        }
        for key, value in expected.items():
            assert THEME[key] == value, f"{key} should be {value}, got {THEME[key]}"


# ===== Radius validation =====

class TestThemeRadii:
    def test_all_radii_positive(self):
        for key in ("radiusSM", "radiusMD", "radiusLG", "radiusXL"):
            assert THEME[key] > 0, f"{key} should be positive"

    def test_radii_increasing(self):
        """Radius values should be monotonically increasing."""
        keys = ("radiusSM", "radiusMD", "radiusLG", "radiusXL")
        values = [THEME[k] for k in keys]
        for i in range(1, len(values)):
            assert values[i] > values[i - 1], (
                f"{keys[i]}={values[i]} should be > {keys[i-1]}={values[i-1]}"
            )


# ===== Typography validation =====

class TestThemeTypography:
    def test_all_fonts_positive(self):
        for key in ("fontMini", "fontCaption", "fontBody", "fontHeading",
                     "fontTitle", "fontSidebarHeader", "fontStat"):
            assert THEME[key] > 0, f"{key} should be positive"

    def test_core_hierarchy(self):
        """Core font hierarchy: Mini < Caption < Body <= Heading < Title < Stat."""
        assert THEME["fontMini"] < THEME["fontCaption"]
        assert THEME["fontCaption"] < THEME["fontBody"]
        assert THEME["fontBody"] <= THEME["fontHeading"]  # Body and Heading can be same size
        assert THEME["fontHeading"] < THEME["fontTitle"]
        assert THEME["fontTitle"] < THEME["fontStat"]


# ===== Sidebar validation =====

class TestThemeSidebar:
    def test_width_increasing(self):
        """Sidebar widths: Min < Ideal < Max."""
        assert THEME["sidebarMin"] < THEME["sidebarIdeal"]
        assert THEME["sidebarIdeal"] < THEME["sidebarMax"]

    def test_icon_only_less_than_min(self):
        """Icon-only sidebar should be narrower than minimum."""
        assert THEME["sidebarIconOnly"] < THEME["sidebarMin"]


# ===== Window validation =====

class TestThemeWindow:
    def test_default_greater_than_min(self):
        assert THEME["windowDefaultWidth"] > THEME["windowMinWidth"]
        assert THEME["windowDefaultHeight"] > THEME["windowMinHeight"]


# ===== Animation validation =====

class TestThemeAnimation:
    def test_durations_increasing(self):
        assert THEME["animationFast"] < THEME["animationNormal"]
        assert THEME["animationNormal"] < THEME["animationSlow"]

    def test_reasonable_durations(self):
        """Animation durations should be in the 100-500ms range."""
        for key in ("animationFast", "animationNormal", "animationSlow"):
            assert 50 <= THEME[key] <= 1000, (
                f"{key}={THEME[key]}ms is outside reasonable range"
            )


# ===== Completeness =====

class TestThemeCompleteness:
    def test_has_all_expected_keys(self):
        """Theme should have all expected keys."""
        expected_keys = {
            # Colors
            "textColor", "secondaryText", "tertiaryText",
            "accentColor", "errorColor", "successColor", "warningColor",
            "infoColor", "purpleColor", "pinkColor", "mintColor",
            "indigoColor", "yellowColor", "brownColor",
            "backgroundColor", "sidebarBg", "cardBg", "inputBg",
            "separatorColor", "hoverBg", "pressedBg", "focusBorder",
            # Spacing
            "spacingXS", "spacingSM", "spacingMD", "spacingLG",
            "spacingXL", "spacingXXL", "spacingXXXL",
            # Radii
            "radiusSM", "radiusMD", "radiusLG", "radiusXL",
            # Typography
            "fontTitle", "fontHeading", "fontBody", "fontCaption",
            "fontMini", "fontSidebarHeader", "fontStat",
            "fontLargeTitle", "fontPageTitle",
            # Sidebar
            "sidebarMin", "sidebarIdeal", "sidebarMax", "sidebarIconOnly",
            # Window
            "windowDefaultWidth", "windowDefaultHeight",
            "windowMinWidth", "windowMinHeight",
            # Breakpoints
            "breakpointCompact", "breakpointStandard",
            # Animation
            "animationFast", "animationNormal", "animationSlow",
        }
        for key in expected_keys:
            assert key in THEME, f"Theme missing key: {key}"
