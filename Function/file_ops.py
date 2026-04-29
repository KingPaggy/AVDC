"""
File operations for AVDC — downloads, NFO generation, file moves, naming.

All functions accept typed parameters (no Qt / self.Ui references).
Logging via Function.logger.
"""
from __future__ import annotations

import os
import re
import shutil
import xml.etree.ElementTree as ET
from configparser import ConfigParser
from typing import Optional

import requests
from PIL import Image

from Function.config_provider import AppConfig
from Function.logger import logger
from core.file_utils import check_pic, escapePath
from core.metadata import get_info

# ========================================================================
# 下载
# ========================================================================

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
)


def download_file(
    url: str,
    filename: str,
    path: str,
    config: AppConfig,
    filepath: str = "",
    failed_folder: str = "",
) -> bool:
    """Download *url* to *path/filename*, retrying per config. Returns True on success."""
    proxies = config.get_proxies_dict()
    timeout = config.timeout
    retry_count = config.retry

    for i in range(retry_count):
        try:
            os.makedirs(path, exist_ok=True)
            resp = requests.get(str(url), headers={"User-Agent": _UA},
                                timeout=timeout, proxies=proxies)
            with open(os.path.join(path, filename), "wb") as f:
                f.write(resp.content)
            return True
        except Exception as exc:
            logger.info(f"[-]Image Download retry {i+1}/{retry_count}: {exc}")

    logger.info("[-]Connect Failed! Please check your Proxy or Network!")
    if filepath and failed_folder:
        move_to_failed(filepath, failed_folder, config)
    return False


def download_thumb(
    json_data: dict,
    path: str,
    naming_rule: str,
    config: AppConfig,
    filepath: str = "",
    failed_folder: str = "",
) -> None:
    """Download the main cover as thumb.jpg, validating with check_pic."""
    thumb_name = naming_rule + "-thumb.jpg"
    thumb_path = os.path.join(path, thumb_name)
    if os.path.exists(thumb_path):
        logger.info(f"[+]Thumb Existed!     {thumb_name}")
        return

    for i in range(config.retry):
        download_file(json_data["cover"], thumb_name, path, config, filepath, failed_folder)
        if check_pic(thumb_path):
            logger.info(f"[+]Thumb Downloaded!  {thumb_name}")
            return
        logger.info(f"[!]Thumb retry {i+1}/{config.retry}")

    # All retries failed — remove bad file
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
    raise Exception(f"Thumb download failed, deleted {thumb_name}")


def download_small_cover(
    path: str,
    naming_rule: str,
    json_data: dict,
    config: AppConfig,
    filepath: str = "",
    failed_folder: str = "",
) -> Optional[str]:
    """Download the small cover for uncensored titles. Returns None on success, 'small_cover_error' on failure."""
    if json_data.get("imagecut") != 3:
        return None
    if not json_data.get("cover_small"):
        return "small_cover_error"

    poster_name = naming_rule + "-poster.jpg"
    poster_path = os.path.join(path, poster_name)
    if os.path.exists(poster_path):
        logger.info(f"[+]Poster Existed!    {poster_name}")
        return None

    download_file(json_data["cover_small"], "cover_small.jpg", path, config, filepath, failed_folder)
    small_path = os.path.join(path, "cover_small.jpg")

    try:
        if not check_pic(small_path):
            raise Exception("cover_small.jpg is corrupt")
        with open(small_path, "rb") as fp:
            img = Image.open(fp)
            w, h = img.size
            if not (1.4 <= h / w <= 1.6):
                logger.info("[-]cover_small.jpg size unfit, try to cut thumb!")
                fp.close()
                os.remove(small_path)
                return "small_cover_error"
            img.save(poster_path)
        logger.info(f"[+]Poster Downloaded! {poster_name}")
        os.remove(small_path)
    except Exception as exc:
        logger.info(f"[-]Error in smallCoverDownload: {exc}")
        if os.path.exists(small_path):
            os.remove(small_path)
        logger.info("[+]Try to cut cover!")
        return "small_cover_error"

    return None


def download_extrafanart(
    json_data: dict,
    path: str,
    config: AppConfig,
    filepath: str = "",
    failed_folder: str = "",
) -> None:
    """Download extra fanart images into a subfolder."""
    fanart_list = json_data.get("extrafanart", [])
    if not fanart_list:
        return
    if not config.extrafanart_download:
        return

    logger.info("[+]ExtraFanart Downloading!")
    folder = config.extrafanart_folder or "extrafanart"
    fanart_dir = os.path.join(path, folder)
    os.makedirs(fanart_dir, exist_ok=True)

    for idx, url in enumerate(fanart_list, 1):
        fname = f"fanart{idx}.jpg"
        fpath = os.path.join(fanart_dir, fname)
        if os.path.exists(fpath):
            continue
        for attempt in range(config.retry):
            download_file(url, fname, fanart_dir, config, filepath, failed_folder)
            if check_pic(fpath):
                break
            logger.info(f"[!]ExtraFanart retry {attempt+1}/{config.retry}")


# ========================================================================
# NFO 生成
# ========================================================================

def write_nfo(
    path: str,
    name_file: str,
    cn_sub: int,
    leak: int,
    json_data: dict,
    filepath: str = "",
    failed_folder: str = "",
    config: Optional[AppConfig] = None,
) -> None:
    """Generate an NFO XML file using ElementTree (replaces PrintFiles)."""
    # Resolve naming media title
    (title, studio, publisher, year, outline, runtime,
     director, actor_photo, actor, release, tag,
     number, cover, website, series) = get_info(json_data)

    naming_media = (
        json_data.get("naming_media", "")
        .replace("title", title)
        .replace("studio", studio)
        .replace("year", year)
        .replace("runtime", runtime)
        .replace("director", director)
        .replace("actor", actor)
        .replace("release", release)
        .replace("number", number)
        .replace("series", series)
        .replace("publisher", publisher)
    )

    nfo_path = os.path.join(path, name_file + ".nfo")
    if os.path.exists(nfo_path):
        logger.info(f"[+]Nfo Existed!       {name_file}.nfo")
        return

    os.makedirs(path, exist_ok=True)

    root = ET.Element("movie")

    ET.SubElement(root, "title").text = naming_media
    ET.SubElement(root, "set")

    # Rating
    try:
        score = json_data.get("score", "")
        if score and score != "unknown" and float(score) != 0.0:
            ET.SubElement(root, "rating").text = str(score)
    except (ValueError, TypeError):
        pass

    if studio != "unknown":
        ET.SubElement(root, "studio").text = studio
    if year != "unknown":
        ET.SubElement(root, "year").text = year
    if outline != "unknown":
        ET.SubElement(root, "outline").text = outline
        ET.SubElement(root, "plot").text = outline
    if runtime != "unknown":
        ET.SubElement(root, "runtime").text = str(runtime).replace(" ", "")
    if director != "unknown":
        ET.SubElement(root, "director").text = director

    ET.SubElement(root, "poster").text = name_file + "-poster.jpg"
    ET.SubElement(root, "thumb").text = name_file + "-thumb.jpg"
    ET.SubElement(root, "fanart").text = name_file + "-fanart.jpg"

    # Actors
    try:
        for name, thumb_url in actor_photo.items():
            if str(name) not in ("unknown", ""):
                actor_el = ET.SubElement(root, "actor")
                ET.SubElement(actor_el, "name").text = name
                if thumb_url:
                    ET.SubElement(actor_el, "thumb").text = thumb_url
    except Exception as exc:
        logger.info(f"[-]Error in actor_photo: {exc}")

    if studio != "unknown":
        ET.SubElement(root, "maker").text = studio
    if publisher != "unknown":
        ET.SubElement(root, "maker").text = publisher
    ET.SubElement(root, "label")

    # Tags & genres
    _add_tags(root, "tag", tag, json_data, cn_sub, leak, studio, publisher, series)
    _add_tags(root, "genre", tag, json_data, cn_sub, leak, studio, publisher, series)

    ET.SubElement(root, "num").text = number
    if release != "unknown":
        ET.SubElement(root, "premiered").text = release
        ET.SubElement(root, "release").text = release
    ET.SubElement(root, "cover").text = cover
    ET.SubElement(root, "website").text = website

    try:
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(nfo_path, encoding="unicode", xml_declaration=True)
        logger.info(f"[+]Nfo Wrote!         {name_file}.nfo")
    except Exception as exc:
        logger.info(f"[-]Write Failed!")
        logger.info(f"[-]Error in write_nfo: {exc}")
        if config and filepath and failed_folder:
            move_to_failed(filepath, failed_folder, config)


def _add_tags(root, element_name, tag_list, json_data, cn_sub, leak, studio, publisher, series):
    """Add tag/genre elements to the NFO root."""
    try:
        for t in tag_list:
            if t != "unknown":
                ET.SubElement(root, element_name).text = t
    except Exception:
        pass
    if json_data.get("imagecut") == 3:
        ET.SubElement(root, element_name).text = "無碼"
    if leak == 1:
        ET.SubElement(root, element_name).text = "流出"
    if cn_sub == 1:
        ET.SubElement(root, element_name).text = "中文字幕"
    if series != "unknown":
        ET.SubElement(root, element_name).text = "系列:" + series
    if studio != "unknown":
        ET.SubElement(root, element_name).text = "製作:" + studio
    if publisher != "unknown":
        ET.SubElement(root, element_name).text = "發行:" + publisher


# ========================================================================
# 文件移动 / 整理 / 命名
# ========================================================================

def move_to_failed(filepath: str, failed_folder: str, config: AppConfig) -> None:
    """Move a file to the failed folder (if config says so)."""
    if not config.failed_file_move:
        return
    try:
        shutil.move(filepath, failed_folder + "/")
        logger.info(f"[-]Move {os.path.split(filepath)[1]} to Failed output folder Success!")
    except Exception as exc:
        logger.info(f"[-]Error in move_to_failed! {exc}")


def paste_file_to_folder(
    filepath: str,
    path: str,
    naming_rule: str,
    failed_folder: str,
    config: AppConfig,
) -> bool:
    """Move or symlink the video + subtitle files. Returns True if subtitle was moved."""
    ext = os.path.splitext(filepath)[1]
    target = os.path.join(path, naming_rule + ext)
    try:
        if os.path.exists(target):
            raise FileExistsError
        if config.soft_link:
            os.symlink(filepath, target)
            logger.info(f"[+]Movie Linked!     {naming_rule}{ext}")
        else:
            shutil.move(filepath, target)
            logger.info(f"[+]Movie Moved!       {naming_rule}{ext}")

        # Move matching subtitle files
        path_old = os.path.dirname(filepath) + "/"
        filename = os.path.splitext(os.path.basename(filepath))[0]
        sub_types = config.sub_type.split("|")
        for sub in sub_types:
            sub_src = path_old + filename + sub
            if os.path.exists(sub_src):
                shutil.move(sub_src, os.path.join(path, naming_rule + sub))
                logger.info(f"[+]Sub moved!         {naming_rule}{sub}")
                return True
    except FileExistsError:
        logger.info(f"[+]Movie Existed!     {naming_rule}{ext}")
        if os.path.split(filepath)[0] != path:
            move_to_failed(filepath, failed_folder, config)
    except PermissionError:
        logger.info("[-]PermissionError! Please run as Administrator!")
    except Exception as exc:
        logger.info(f"[-]Error in paste_file_to_folder: {exc}")
    return False


def copy_as_fanart(path: str, naming_rule: str) -> None:
    """Copy thumb.jpg as fanart.jpg."""
    src = os.path.join(path, naming_rule + "-thumb.jpg")
    dst = os.path.join(path, naming_rule + "-fanart.jpg")
    try:
        if not os.path.exists(dst):
            shutil.copy(src, dst)
            logger.info(f"[+]Fanart Copied!     {naming_rule}-fanart.jpg")
        else:
            logger.info(f"[+]Fanart Existed!    {naming_rule}-fanart.jpg")
    except Exception as exc:
        logger.info(f"[-]Error in copy_as_fanart: {exc}")


def delete_thumb(path: str, naming_rule: str, keep_thumb: bool) -> None:
    """Delete the thumb file if the user unchecked thumb download."""
    if keep_thumb:
        return
    thumb_path = os.path.join(path, naming_rule + "-thumb.jpg")
    try:
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            logger.info(f"[+]Thumb Delete!      {naming_rule}-thumb.jpg")
    except Exception as exc:
        logger.info(f"[-]Error in delete_thumb: {exc}")


def get_disc_part(filepath: str) -> str:
    """Extract -CDn / -cdn disc part from filepath."""
    try:
        m = re.search(r"-CD\d+", filepath) or re.search(r"-cd\d+", filepath)
        if m:
            return m.group()
    except Exception:
        pass
    return ""


def create_output_folder(success_folder: str, json_data: dict, config: AppConfig) -> str:
    """Create the output folder based on naming rules. Returns the folder path."""
    (title, studio, publisher, year, outline, runtime,
     director, actor_photo, actor, release, tag,
     number, cover, website, series) = get_info(json_data)

    # Truncate long actor lists
    if len(actor.split(",")) >= 10:
        parts = actor.split(",")
        actor = parts[0] + "," + parts[1] + "," + parts[2] + "等演员"

    folder_name = json_data.get("folder_name", "number")
    path = (
        folder_name
        .replace("title", title)
        .replace("studio", studio)
        .replace("year", year)
        .replace("runtime", runtime)
        .replace("director", director)
        .replace("actor", actor)
        .replace("release", release)
        .replace("number", number)
        .replace("series", series)
        .replace("publisher", publisher)
    )
    path = path.replace("--", "-").strip("-")
    if len(path) > 100:
        logger.info("[-]Error in Length of Path! Cut title!")
        path = path.replace(title, title[:70])
    path = success_folder + "/" + path
    path = path.replace("--", "-").strip("-")

    if not os.path.exists(path):
        path = escapePath(path, _make_config_parser(config))
        os.makedirs(path)
    return path


def resolve_naming_rule(json_data: dict) -> str:
    """Resolve the file naming rule from json_data fields."""
    (title, studio, publisher, year, outline, runtime,
     director, actor_photo, actor, release, tag,
     number, cover, website, series) = get_info(json_data)

    if len(actor.split(",")) >= 10:
        parts = actor.split(",")
        actor = parts[0] + "," + parts[1] + "," + parts[2] + "等演员"

    name_file = (
        json_data.get("naming_file", "number")
        .replace("title", title)
        .replace("studio", studio)
        .replace("year", year)
        .replace("runtime", runtime)
        .replace("director", director)
        .replace("actor", actor)
        .replace("release", release)
        .replace("number", number)
        .replace("series", series)
        .replace("publisher", publisher)
    )
    name_file = name_file.replace("//", "/").replace("--", "-").strip("-")
    if len(name_file) > 100:
        logger.info("[-]Error in Length of Path! Cut title!")
        name_file = name_file.replace(title, title[:70])
    return name_file


def ensure_failed_folder(failed_folder: str, config: AppConfig) -> None:
    """Create the failed output folder if configured."""
    if config.failed_file_move and not os.path.exists(failed_folder):
        try:
            os.makedirs(failed_folder + "/")
            logger.info(f"[+]Created folder named {failed_folder}!")
        except Exception as exc:
            logger.info(f"[-]Error in ensure_failed_folder: {exc}")


def clean_empty_dirs(path: str) -> None:
    """Remove empty directories recursively."""
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path):
        for d in dirs:
            try:
                os.removedirs(os.path.join(root, d))
                logger.info(f"[+]Deleting empty folder {os.path.join(root, d)}")
            except OSError:
                pass


# ========================================================================
# 内部工具
# ========================================================================

def _make_config_parser(config: AppConfig) -> ConfigParser:
    """Build a ConfigParser from AppConfig for compatibility with escapePath()."""
    cfg = ConfigParser()
    cfg["escape"] = {
        "literals": config.literals,
        "folders": config.folders,
        "string": config.string,
    }
    return cfg
