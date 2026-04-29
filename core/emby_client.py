"""
Emby API client for AVDC — actor list, profile picture upload.

All functions accept emby_url and api_key as parameters (no Qt references).
Logging via core.logger.
"""
from __future__ import annotations

import base64
import os
import re
import shutil
from typing import Optional

import requests

from core.logger import logger

_EMBA_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36"
)


def _normalize_url(emby_url: str) -> str:
    """Replace full-width colon with normal one."""
    return emby_url.replace("：", ":")


# ========================================================================
# 演员列表
# ========================================================================


def get_actor_list(emby_url: str, api_key: str, timeout: int = 10) -> dict:
    """Fetch the actor/person list from Emby."""
    url = f"http://{_normalize_url(emby_url)}/emby/Persons?api_key={api_key}"
    try:
        resp = requests.get(url, headers={"User-Agent": _EMBA_UA}, timeout=timeout)
        resp.encoding = "utf-8"
        return resp.json()
    except Exception:
        logger.info("[-]Error! Check your emby_url or api_key!")
        return {"TotalRecordCount": 0, "Items": []}


def list_actors(
    emby_url: str,
    api_key: str,
    mode: int = 3,
) -> list[str]:
    """List actors by mode: 1=without avatar, 2=with avatar, 3=all.

    Returns a list of formatted actor name strings.
    """
    actor_list = get_actor_list(emby_url, api_key)
    if actor_list.get("TotalRecordCount", 0) == 0:
        return []

    result = []
    count = 1
    for actor in actor_list["Items"]:
        name = actor["Name"]
        has_avatar = actor.get("ImageTags", {}) != {}

        if mode == 1 and has_avatar:
            continue
        if mode == 2 and not has_avatar:
            continue

        result.append(f"{count}. {name}")
        count += 1
    return result


# ========================================================================
# 头像匹配与上传
# ========================================================================


def find_and_upload_pictures(
    emby_url: str,
    api_key: str,
    actor_dir: str = "Actor",
    mode: int = 1,
) -> None:
    """Scan Actor/ directory for profile pictures and optionally upload them.

    *mode=1*: upload profile pictures for actors missing avatars.
    *mode=2*: log actors that could have profile pictures uploaded.
    """
    if mode == 1:
        logger.info("[+]Start upload profile pictures!")
    elif mode == 2:
        logger.info("[+]可添加头像的女优!")

    if not os.path.exists(actor_dir):
        logger.info("[+]Actor folder not exist!")
        logger.info("[*]======================================================")
        return

    success_dir = os.path.join(actor_dir, "Success")
    os.makedirs(success_dir, exist_ok=True)

    profile_pictures = set(os.listdir(actor_dir))
    actor_list = get_actor_list(emby_url, api_key)

    if actor_list.get("TotalRecordCount", 0) == 0:
        logger.info("[*]======================================================")
        return

    count = 1
    for actor in actor_list["Items"]:
        flag = 0
        pic_name = ""

        # Try exact match first
        for ext in (".jpg", ".png"):
            candidate = actor["Name"] + ext
            if candidate in profile_pictures:
                flag = 1
                pic_name = candidate
                break

        # Try alias match
        if flag == 0:
            byname_list = re.split("[,，()（）]", actor["Name"])
            for byname in byname_list:
                for ext in (".jpg", ".png"):
                    candidate = byname + ext
                    if candidate in profile_pictures:
                        pic_name = candidate
                        flag = 1
                        break
                if flag:
                    break

        has_avatar = actor.get("ImageTags", {}) != {}
        already_success = os.path.exists(os.path.join(success_dir, pic_name))

        if flag == 1 and (not has_avatar or not already_success):
            if mode == 1:
                try:
                    upload_actor_photo(
                        emby_url, api_key, actor,
                        os.path.join(actor_dir, pic_name),
                    )
                    shutil.copy(
                        os.path.join(actor_dir, pic_name),
                        os.path.join(success_dir, pic_name),
                    )
                except Exception as exc:
                    logger.info(f"[-]Error in find_and_upload_pictures! {exc}")
            else:
                logger.info(
                    f"[+]{count:4d}.Actor name: {actor['Name']}  Pic name: {pic_name}"
                )
            count += 1

    if count == 1:
        logger.info("[-]NO profile picture can be uploaded!")
    logger.info("[*]======================================================")


def upload_actor_photo(
    emby_url: str,
    api_key: str,
    actor: dict,
    pic_path: str,
) -> None:
    """Upload a profile picture for an Emby actor/person."""
    url = (
        f"http://{_normalize_url(emby_url)}/emby/Items/"
        f"{actor['Id']}/Images/Primary?api_key={api_key}"
    )

    with open(pic_path, "rb") as f:
        b6_pic = base64.b64encode(f.read())

    # Note: original code has content-type swapped (jpg→png, else→jpeg)
    # Keep the original behavior for compatibility
    content_type = "image/png" if pic_path.endswith("jpg") else "image/jpeg"

    requests.post(
        url=url, data=b6_pic,
        headers={"Content-Type": content_type},
    )
    logger.info(
        f"[+]Success upload profile picture for {actor['Name']}!"
    )
