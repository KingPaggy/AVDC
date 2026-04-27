"""Image processing services for AVDC.

Contains reusable image operations: AI-based poster cropping, center cropping,
and watermark compositing. All functions are pure — no UI dependencies.
"""
import os
from PIL import Image
from core.errors import ImageError
import os
from PIL import Image

# Watermark mark image paths
MARK_PATHS = {
    "SUB": "Img/SUB.png",
    "LEAK": "Img/LEAK.png",
    "UNCENSORED": "Img/UNCENSORED.png",
}

# Watermark corner positions: top-left, top-right, bottom-right, bottom-left
MARK_POSITIONS = [
    {"x": 0, "y": 0},
    {"x": 0, "y": 0},  # computed from image size at apply time
    {"x": 0, "y": 0},
    {"x": 0, "y": 0},
]

# Baidu AI credentials — read from environment variables
# Set BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY in your environment
BAIDU_APP_ID = os.environ.get("BAIDU_APP_ID", "")
BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "")


def cut_poster_ai(thumb_path: str, poster_path: str) -> str | None:
    """Crop poster from thumb using Baidu AI body analysis.

    Returns poster_path on success, None on failure.
    """
    if not BAIDU_APP_ID or not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        return None

    try:
        from aip import AipBodyAnalysis
    except ImportError:
        return None

    if os.path.exists(poster_path):
        os.remove(poster_path)

    client = AipBodyAnalysis(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)

    with Image.open(thumb_path) as im:
        width, height = im.size

    with open(thumb_path, "rb") as fp:
        image = fp.read()

    ex, ey, ew, eh = 0, 0, 0, 0

    if height / width <= 1.5:
        result = client.bodyAnalysis(image)
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
        ew = ewidth if ewidth <= width else width
    else:
        ex = 0
        ey = 0
        ew = width
        eh = ew * 1.5

    with Image.open(thumb_path) as img:
        img_new = img.crop((ex, ey, ew + ex, eh + ey))
        img_new.save(poster_path)

    return poster_path


def cut_poster_center(thumb_path: str, poster_path: str) -> bool:
    """Crop poster from thumb using a simple center-right crop (imagecut=1).

    Returns True on success, False on failure.
    """
    try:
        img = Image.open(thumb_path)
        w, h = img.size
        img2 = img.crop((w / 1.9, 0, w, h))
        img2.save(poster_path)
        img.close()
        return True
    except Exception as e:
        raise ImageError(f"Center crop failed for {thumb_path}: {e}") from e


def cut_poster(thumb_path: str, poster_path: str, imagecut: int = 0) -> bool:
    """High-level poster crop dispatcher.

    imagecut:
        0 — AI-based body analysis crop
        1 — center-right crop
        3 — skip (poster already exists or not needed)
    """
    if imagecut == 0:
        return cut_poster_ai(thumb_path, poster_path) is not None
    elif imagecut == 1:
        return cut_poster_center(thumb_path, poster_path)
    return True  # imagecut == 3, nothing to do


# ---------------------------------------------------------------------------
# Watermark compositing
# ---------------------------------------------------------------------------

# Position index mapping: top_left=0, top_right=1, bottom_right=2, bottom_left=3
MARK_POS_INDEX = {
    "top_left": 0,
    "top_right": 1,
    "bottom_right": 2,
    "bottom_left": 3,
}

# Mark type key → config flag name
MARK_TYPES = [
    ("SUB", "cn_sub"),
    ("LEAK", "leak"),
    ("UNCENSORED", "uncensored"),
]


def add_watermark(
    pic_path: str,
    mark_size: int = 3,
    mark_pos: str = "top_left",
    marks: dict | None = None,
) -> None:
    """Add watermark marks (SUB/LEAK/UNCENSORED) to an image.

    Args:
        pic_path: path to the image to watermark (modified in place)
        mark_size: size factor (1-5, larger = smaller watermark)
        mark_pos: one of top_left, top_right, bottom_right, bottom_left
        marks: dict like {"cn_sub": True, "leak": False, "uncensored": True}
    """
    if marks is None:
        marks = {}

    start_count = MARK_POS_INDEX.get(mark_pos, 0)
    count = start_count

    img_pic = Image.open(pic_path)
    size = 14 - mark_size

    for mark_key, flag_name in MARK_TYPES:
        if not marks.get(flag_name, False):
            continue
        mark_img_path = MARK_PATHS[mark_key]
        if not os.path.exists(mark_img_path):
            continue
        _apply_single_mark(pic_path, img_pic, size, count % 4, mark_img_path)
        count = (count + 1) % 4

    img_pic.close()


def _apply_single_mark(
    pic_path: str,
    img_pic: Image.Image,
    size: int,
    pos_index: int,
    mark_path: str,
) -> None:
    """Composite a single watermark onto the image at the given corner position."""
    img_subt = Image.open(mark_path)
    scroll_high = int(img_pic.height / size)
    scroll_wide = int(scroll_high * img_subt.width / img_subt.height)
    img_subt = img_subt.resize((scroll_wide, scroll_high), Image.LANCZOS)

    r, g, b, a = img_subt.split()

    pos = [
        {"x": 0, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": img_pic.height - scroll_high},
        {"x": 0, "y": img_pic.height - scroll_high},
    ]

    img_pic.paste(img_subt, (pos[pos_index]["x"], pos[pos_index]["y"]), mask=a)
    img_pic.save(pic_path, quality=95)
