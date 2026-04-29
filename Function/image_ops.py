"""
Image operations for AVDC — watermark, cropping (Baidu AI face detection), size fixing.

All functions accept typed parameters (no Qt / self.Ui references).
Logging via Function.logger.

Baidu AI credentials come from AppConfig (baidu_app_id/api_key/secret_key).
"""
from __future__ import annotations

import os

from PIL import Image, ImageFilter
from aip import AipBodyAnalysis

from Function.config_provider import AppConfig
from Function.logger import logger

# ========================================================================
# 封面裁剪（百度 AI 人脸/人体检测）
# ========================================================================


def crop_by_face_detection(
    path: str,
    file_name: str,
    mode: int = 1,
    app_id: str = "",
    api_key: str = "",
    secret_key: str = "",
) -> None:
    """Crop a thumb to poster using Baidu body analysis for positioning.

    *mode=2* signals caller to update UI (handled by UI layer).
    """
    png_name = file_name.replace("-thumb.jpg", "-poster.jpg")
    file_path = os.path.join(path, file_name)
    png_path = os.path.join(path, png_name)

    try:
        if os.path.exists(png_path):
            os.remove(png_path)
    except Exception as exc:
        logger.info(f"[-]Error in crop_by_face_detection: {exc}")
        return

    client = AipBodyAnalysis(app_id, api_key, secret_key)

    with Image.open(file_path) as im:
        width, height = im.size

    with open(file_path, "rb") as fp:
        image_bytes = fp.read()

    ex, ey, ew, eh = 0, 0, 0, 0

    if height / width <= 1.5:
        # Too wide — use body analysis to find nose position
        result = client.bodyAnalysis(image_bytes)
        ewidth = int(height / 1.5)
        ex = int(result["person_info"][0]["body_parts"]["nose"]["x"])
        if width - ex < ewidth / 2:
            ex = width - ewidth
        else:
            ex -= int(ewidth / 2)
        if ex < 0:
            ex = 0
        ey = 0
        eh = height
        ew = min(ewidth, width)
    else:
        # Too tall — crop top portion
        ex = 0
        ey = 0
        ew = int(width)
        eh = ew * 1.5

    with Image.open(file_path) as img:
        img_new_png = img.crop((ex, ey, ew + ex, eh + ey))
        img_new_png.save(png_path)

    logger.info(f"[+]Poster Cut         {png_name} from {file_name}!")


# ========================================================================
# 封面裁剪（无码片 — 右侧裁剪）
# ========================================================================


def cut_poster(
    imagecut: int,
    path: str,
    naming_rule: str,
    baidu_credentials: dict | None = None,
) -> None:
    """Cut or download poster based on imagecut flag.

    imagecut == 0: face detection crop (uses Baidu AI)
    imagecut == 1: crop right half of thumb
    imagecut == 3: already handled by small_cover_download
    """
    if imagecut == 3:
        return
    if imagecut != 3:
        thumb_name = naming_rule + "-thumb.jpg"
        poster_name = naming_rule + "-poster.jpg"
        thumb_path = os.path.join(path, thumb_name)
        poster_path = os.path.join(path, poster_name)

        if os.path.exists(poster_path):
            logger.info(f"[+]Poster Existed!    {poster_name}")
            return

        if imagecut == 0:
            # Face detection crop
            if baidu_credentials:
                crop_by_face_detection(
                    path, thumb_name, mode=1,
                    app_id=baidu_credentials.get("app_id", ""),
                    api_key=baidu_credentials.get("api_key", ""),
                    secret_key=baidu_credentials.get("secret_key", ""),
                )
            else:
                logger.info("[-]Baidu credentials missing for face crop")
        else:
            # Crop right half (imagecut == 1 or 2)
            try:
                img = Image.open(thumb_path)
                w, h = img.size
                img2 = img.crop((w / 1.9, 0, w, h))
                img2.save(poster_path)
                logger.info(f"[+]Poster Cut!        {poster_name}")
            except Exception:
                logger.info("[-]Thumb cut failed!")


# ========================================================================
# 封面尺寸修正
# ========================================================================


def fix_image_size(path: str, naming_rule: str) -> None:
    """Fix poster aspect ratio by padding with Gaussian blur background."""
    poster_path = os.path.join(path, naming_rule + "-poster.jpg")
    try:
        pic = Image.open(poster_path)
        width, height = pic.size
        if not (2 / 3 - 0.05 <= width / height <= 2 / 3 + 0.05):
            fixed_pic = pic.resize((int(width), int(3 / 2 * width)))
            fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))
            fixed_pic.paste(pic, (0, int((3 / 2 * width - height) / 2)))
            fixed_pic.save(poster_path)
    except Exception as exc:
        logger.info(f"[-]Error in fix_image_size: {exc}")


# ========================================================================
# 水印
# ========================================================================

# Watermark overlay file paths (relative to project root)
_WATERMARK_PATHS = {
    1: "Img/SUB.png",       # 字幕
    2: "Img/LEAK.png",      # 流出
    3: "Img/UNCENSORED.png", # 无码
}


def apply_marks(
    pic_path: str,
    cn_sub: int,
    leak: int,
    uncensored: int,
    mark_config: dict,
) -> None:
    """Apply watermark marks to an image.

    mark_config keys:
        mark_size: int (1-5, larger = smaller watermark)
        mark_pos: str ("top_left", "top_right", "bottom_left", "bottom_right")
        poster_mark: int (0/1)
        thumb_mark: int (0/1)
    """
    mark_type = ""
    if cn_sub:
        mark_type += ",字幕"
    if leak:
        mark_type += ",流出"
    if uncensored:
        mark_type += ",无码"

    if mark_type == "":
        return

    mark_size = mark_config.get("mark_size", 10)
    mark_pos = mark_config.get("mark_pos", "top_left")
    pos_map = {
        "top_left": 0,
        "top_right": 1,
        "bottom_right": 2,
        "bottom_left": 3,
    }
    count = pos_map.get(mark_pos, 0)

    img_pic = Image.open(pic_path)

    if cn_sub == 1:
        _add_watermark(pic_path, img_pic, mark_size, count, 1)
        count = (count + 1) % 4
    if leak == 1:
        _add_watermark(pic_path, img_pic, mark_size, count, 2)
        count = (count + 1) % 4
    if uncensored == 1:
        _add_watermark(pic_path, img_pic, mark_size, count, 3)

    img_pic.close()


def _add_watermark(
    pic_path: str,
    img_pic: Image.Image,
    size: int,
    count: int,
    mode: int,
) -> None:
    """Add a single watermark overlay to the image."""
    mark_path = _WATERMARK_PATHS.get(mode, "")
    if not mark_path or not os.path.exists(mark_path):
        logger.info(f"[-]Watermark image not found: {mark_path}")
        return

    img_subt = Image.open(mark_path)
    scroll_high = int(img_pic.height / size)
    scroll_wide = int(scroll_high * img_subt.width / img_subt.height)
    img_subt = img_subt.resize((scroll_wide, scroll_high), Image.Resampling.LANCZOS)
    r, g, b, a = img_subt.split()

    pos = [
        {"x": 0, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": img_pic.height - scroll_high},
        {"x": 0, "y": img_pic.height - scroll_high},
    ]

    img_pic.paste(img_subt, (pos[count]["x"], pos[count]["y"]), mask=a)
    img_pic.save(pic_path, quality=95)
