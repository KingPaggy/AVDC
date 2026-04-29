#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import json
import os
import re
import shutil
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import requests
from PIL import Image

from core.file_utils import check_pic
from core.config_io import get_proxy_config
from core.networking import get_proxies


@dataclass
class RemoteCallbacks:
    log: Callable[[str], None]
    move_failed: Callable[[str, str], None]


class RemoteService:
    """Own HTTP downloads and Emby interactions."""

    def download_file_with_filename(
        self,
        url: str,
        filename: str,
        path: str,
        filepath: str,
        failed_folder: str,
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> None:
        proxy_type = ""
        retry_count = 0
        proxy = ""
        timeout = 0
        try:
            proxy_type, proxy, timeout, retry_count = get_proxy_config()
        except Exception as error_info:
            print("[-]Error in DownloadFileWithFilename! " + str(error_info))
            log("[-]Error in DownloadFileWithFilename! Proxy config error! Please check the config.")
        proxies = get_proxies(proxy_type, proxy)
        i = 0
        while i < retry_count:
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
                }
                result = requests.get(
                    str(url), headers=headers, timeout=timeout, proxies=proxies
                )
                with open(str(path) + "/" + filename, "wb") as code:
                    code.write(result.content)
                return
            except Exception as error_info:
                i += 1
                print("[-]Error in DownloadFileWithFilename! " + str(error_info))
                print("[-]Image Download :   Connect retry " + str(i) + "/" + str(retry_count))
        log("[-]Connect Failed! Please check your Proxy or Network!")
        move_failed(filepath, failed_folder)

    def thumb_download(
        self,
        json_data: dict,
        path: str,
        naming_rule: str,
        config,
        filepath: str,
        failed_folder: str,
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> None:
        thumb_name = naming_rule + "-thumb.jpg"
        if os.path.exists(path + "/" + thumb_name):
            log("[+]Thumb Existed!     " + thumb_name)
            return
        i = 1
        while i <= int(config["proxy"]["retry"]):
            self.download_file_with_filename(
                json_data["cover"], thumb_name, path, filepath, failed_folder, log, move_failed
            )
            if not check_pic(path + "/" + thumb_name):
                print("[!]Image Download Failed! Trying again. " + str(i) + "/" + config["proxy"]["retry"])
                i = i + 1
            else:
                break
        if check_pic(path + "/" + thumb_name):
            log("[+]Thumb Downloaded!  " + thumb_name)
        else:
            os.remove(path + "/" + thumb_name)
            raise Exception("The Size of Thumb is Error! Deleted " + thumb_name + "!")

    def small_cover_download(
        self,
        path: str,
        naming_rule: str,
        json_data: dict,
        config,
        filepath: str,
        failed_folder: str,
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> str:
        if json_data["imagecut"] == 3:
            if json_data["cover_small"] == "":
                return "small_cover_error"
            is_pic_open = 0
            poster_name = naming_rule + "-poster.jpg"
            if os.path.exists(path + "/" + poster_name):
                log("[+]Poster Existed!    " + poster_name)
                return ""
            self.download_file_with_filename(
                json_data["cover_small"],
                "cover_small.jpg",
                path,
                filepath,
                failed_folder,
                log,
                move_failed,
            )
            try:
                if not check_pic(path + "/cover_small.jpg"):
                    raise Exception("The Size of smallcover is Error! Deleted cover_small.jpg!")
                fp = open(path + "/cover_small.jpg", "rb")
                is_pic_open = 1
                img = Image.open(fp)
                w = img.width
                h = img.height
                if not (1.4 <= h / w <= 1.6):
                    log("[-]The size of cover_small.jpg is unfit, Try to cut thumb!")
                    fp.close()
                    os.remove(path + "/cover_small.jpg")
                    return "small_cover_error"
                img.save(path + "/" + poster_name)
                log("[+]Poster Downloaded! " + poster_name)
                fp.close()
                os.remove(path + "/cover_small.jpg")
            except Exception as error_info:
                log("[-]Error in smallCoverDownload: " + str(error_info))
                if is_pic_open:
                    fp.close()
                os.remove(path + "/cover_small.jpg")
                log("[+]Try to cut cover!")
                return "small_cover_error"
        return ""

    def extrafanart_download(
        self,
        json_data: dict,
        path: str,
        config,
        filepath: str,
        failed_folder: str,
        extrafanart_folder: str,
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> None:
        if len(json_data["extrafanart"]) == 0:
            json_data["extrafanart"] = ""
        if str(json_data["extrafanart"]) != "":
            log("[+]ExtraFanart Downloading!")
            if extrafanart_folder == "":
                extrafanart_folder = "extrafanart"
            extrafanart_path = path + "/" + extrafanart_folder
            extrafanart_list = json_data["extrafanart"]
            if not os.path.exists(extrafanart_path):
                os.makedirs(extrafanart_path)
            extrafanart_count = 0
            for extrafanart_url in extrafanart_list:
                extrafanart_count += 1
                if not os.path.exists(extrafanart_path + "/fanart" + str(extrafanart_count) + ".jpg"):
                    i = 1
                    while i <= int(config["proxy"]["retry"]):
                        self.download_file_with_filename(
                            extrafanart_url,
                            "fanart" + str(extrafanart_count) + ".jpg",
                            extrafanart_path,
                            filepath,
                            failed_folder,
                            log,
                            move_failed,
                        )
                        if not check_pic(extrafanart_path + "/fanart" + str(extrafanart_count) + ".jpg"):
                            print("[!]Image Download Failed! Trying again. " + str(i) + "/" + config["proxy"]["retry"])
                            i = i + 1
                        else:
                            break

    def get_emby_actor_list(self, emby_url: str, api_key: str, log: Callable[[str], None]) -> dict:
        emby_url = emby_url.replace("：", ":")
        url = "http://" + emby_url + "/emby/Persons?api_key=" + api_key
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36"
        }
        actor_list = {}
        try:
            getweb = requests.get(str(url), headers=headers, timeout=10)
            getweb.encoding = "utf-8"
            actor_list = json.loads(getweb.text)
        except Exception:
            log("[-]Error! Check your emby_url or api_key!")
            actor_list["TotalRecordCount"] = 0
        return actor_list

    def show_actor_lines(self, actor_list: dict, mode: int) -> List[str]:
        lines: List[str] = []
        if actor_list.get("TotalRecordCount", 0) == 0:
            return lines
        count = 1
        actor_list_temp = ""
        for actor in actor_list["Items"]:
            if mode == 3:
                actor_list_temp += str(count) + "." + actor["Name"] + ","
                count += 1
            elif mode == 2 and actor["ImageTags"] != {}:
                actor_list_temp += str(count) + "." + actor["Name"] + ","
                count += 1
            elif mode == 1 and actor["ImageTags"] == {}:
                actor_list_temp += str(count) + "." + actor["Name"] + ","
                count += 1
            if (count - 1) % 5 == 0 and actor_list_temp != "":
                lines.append("[+]" + actor_list_temp)
                actor_list_temp = ""
        if actor_list_temp != "":
            lines.append("[+]" + actor_list_temp)
        return lines

    def choose_picture_name(self, actor_name: str, profile_pictures: List[str]) -> Tuple[int, str]:
        if actor_name + ".jpg" in profile_pictures:
            return 1, actor_name + ".jpg"
        if actor_name + ".png" in profile_pictures:
            return 1, actor_name + ".png"
        byname_list = re.split("[,，()（）]", actor_name)
        for byname in byname_list:
            if byname + ".jpg" in profile_pictures:
                return 1, byname + ".jpg"
            if byname + ".png" in profile_pictures:
                return 1, byname + ".png"
        return 0, ""

    def upload_profile_picture(
        self, emby_url: str, api_key: str, count: int, actor: dict, pic_path: str, log: Callable[[str], None]
    ) -> None:
        emby_url = emby_url.replace("：", ":")
        try:
            f = open(pic_path, "rb")
            b6_pic = base64.b64encode(f.read())
            f.close()
            url = "http://" + emby_url + "/emby/Items/" + actor["Id"] + "/Images/Primary?api_key=" + api_key
            if pic_path.endswith("jpg"):
                header = {"Content-Type": "image/png"}
            else:
                header = {"Content-Type": "image/jpeg"}
            requests.post(url=url, data=b6_pic, headers=header)
            log(
                "[+]"
                + "%4s" % str(count)
                + ".Success upload profile picture for "
                + actor["Name"]
                + "!"
            )
        except Exception as error_info:
            log("[-]Error in upload_profile_picture! " + str(error_info))

    def find_profile_pictures(
        self,
        mode: int,
        actor_list: dict,
        profile_pictures: List[str],
        path_success: str,
        emby_url: str,
        api_key: str,
        log: Callable[[str], None],
        upload_enabled: bool,
    ) -> List[str]:
        lines: List[str] = []
        count = 1
        for actor in actor_list.get("Items", []):
            flag, pic_name = self.choose_picture_name(actor["Name"], profile_pictures)
            if flag == 1 and (
                actor["ImageTags"] == {} or not os.path.exists(path_success + "/" + pic_name)
            ):
                if upload_enabled and mode == 1:
                    try:
                        self.upload_profile_picture(
                            emby_url,
                            api_key,
                            count,
                            actor,
                            path_success.replace("/Success", "") + "/" + pic_name,
                            log,
                        )
                        shutil.copy(
                            path_success.replace("/Success", "") + "/" + pic_name,
                            path_success + "/" + pic_name,
                        )
                    except Exception as error_info:
                        log("[-]Error in found_profile_picture! " + str(error_info))
                else:
                    lines.append(
                        "[+]" + "%4s" % str(count) + ".Actor name: " + actor["Name"] + "  Pic name: " + pic_name
                    )
                count += 1
        if count == 1:
            lines.append("[-]NO profile picture can be uploaded!")
        return lines

