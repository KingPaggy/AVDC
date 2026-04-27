#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import shutil
from dataclasses import dataclass
from typing import Any, Callable

from PIL import Image, ImageFilter

from core.file_utils import escapePath
from core.metadata import get_info


@dataclass
class FileSystemCallbacks:
    log: Callable[[str], None]
    move_failed: Callable[[str, str], None]
    image_cut: Callable[[str, str], None]
    mark_image: Callable[[str, int, int, int], None]


class FileSystemService:
    """Encapsulate local filesystem side effects used by AVDC."""

    def move_failed_folder(self, filepath: str, failed_folder: str, enabled: bool) -> None:
        if not enabled:
            return
        try:
            shutil.move(filepath, failed_folder + "/")
        except Exception:
            raise

    def cleanup_empty_dirs(self, path: str, log: Callable[[str], None]) -> None:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir_name in dirs:
                    try:
                        os.removedirs(root.replace("\\", "/") + "/" + dir_name)
                        log("[+]Deleting empty folder " + root.replace("\\", "/") + "/" + dir_name)
                    except Exception:
                        pass

    def get_part(self, filepath: str) -> str:
        try:
            if re.search(r"-CD\d+", filepath):
                return re.findall(r"-CD\d+", filepath)[0]
            if re.search(r"-cd\d+", filepath):
                return re.findall(r"-cd\d+", filepath)[0]
        except Exception:
            return ""
        return ""

    def create_folder(self, success_folder: str, json_data: dict, config: Any) -> str:
        (
            title,
            studio,
            publisher,
            year,
            outline,
            runtime,
            director,
            actor_photo,
            actor,
            release,
            tag,
            number,
            cover,
            website,
            series,
        ) = get_info(json_data)
        folder_name = json_data["folder_name"]
        path = (
            folder_name.replace("title", title)
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
            path = path.replace(title, title[0:70])
        path = success_folder + "/" + path
        path = path.replace("--", "-").strip("-")
        if not os.path.exists(path):
            path = escapePath(path, config)
            os.makedirs(path)
        return path

    def delete_thumb(self, path: str, naming_rule: str, keep_thumb: bool, log: Callable[[str], None]) -> None:
        try:
            thumb_path = path + "/" + naming_rule + "-thumb.jpg"
            if (not keep_thumb) and os.path.exists(thumb_path):
                os.remove(thumb_path)
                log("[+]Thumb Delete!      " + naming_rule + "-thumb.jpg")
        except Exception as error_info:
            log("[-]Error in deletethumb: " + str(error_info))

    def copy_fanart(self, path: str, naming_rule: str, log: Callable[[str], None]) -> None:
        try:
            if not os.path.exists(path + "/" + naming_rule + "-fanart.jpg"):
                shutil.copy(
                    path + "/" + naming_rule + "-thumb.jpg",
                    path + "/" + naming_rule + "-fanart.jpg",
                )
                log("[+]Fanart Copied!     " + naming_rule + "-fanart.jpg")
            else:
                log("[+]Fanart Existed!    " + naming_rule + "-fanart.jpg")
        except Exception as error_info:
            log("[-]Error in copyRenameJpgToFanart: " + str(error_info))

    def paste_file_to_folder(
        self,
        filepath: str,
        path: str,
        naming_rule: str,
        failed_folder: str,
        keep_failed_move: bool,
        use_symlink: bool,
        subtitle_types: list[str],
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> bool:
        file_ext = str(os.path.splitext(filepath)[1])
        try:
            if os.path.exists(path + "/" + naming_rule + file_ext):
                raise FileExistsError
            if use_symlink:
                os.symlink(filepath, path + "/" + naming_rule + file_ext)
                log("[+]Movie Linked!     " + naming_rule + file_ext)
            else:
                shutil.move(filepath, path + "/" + naming_rule + file_ext)
                log("[+]Movie Moved!       " + naming_rule + file_ext)
            path_old = filepath.replace(filepath.split("/")[-1], "")
            filename = filepath.split("/")[-1].split(".")[0]
            for sub in subtitle_types:
                if os.path.exists(path_old + "/" + filename + sub):
                    shutil.move(path_old + "/" + filename + sub, path + "/" + naming_rule + sub)
                    log("[+]Sub moved!         " + naming_rule + sub)
                    return True
        except FileExistsError:
            log("[+]Movie Existed!     " + naming_rule + file_ext)
            if os.path.split(filepath)[0] != path and keep_failed_move:
                move_failed(filepath, failed_folder)
        except PermissionError:
            log("[-]PermissionError! Please run as Administrator!")
        except Exception as error_info:
            log("[-]Error in pasteFileToFolder: " + str(error_info))
        return False

    def write_nfo(
        self,
        path: str,
        name_file: str,
        cn_sub: int,
        leak: int,
        json_data: dict,
        filepath: str,
        failed_folder: str,
        keep_failed_move: bool,
        log: Callable[[str], None],
        move_failed: Callable[[str, str], None],
    ) -> None:
        (
            title,
            studio,
            publisher,
            year,
            outline,
            runtime,
            director,
            actor_photo,
            actor,
            release,
            tag,
            number,
            cover,
            website,
            series,
        ) = get_info(json_data)
        name_media = (
            json_data["naming_media"]
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
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            if os.path.exists(path + "/" + name_file + ".nfo"):
                log("[+]Nfo Existed!       " + name_file + ".nfo")
                return
            with open(path + "/" + name_file + ".nfo", "wt", encoding="UTF-8") as code:
                print("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", file=code)
                print("<movie>", file=code)
                print("  <title>" + title + "</title>", file=code)
                print("  <originaltitle>" + title + "</originaltitle>", file=code)
                print("  <sorttitle>" + title + "</sorttitle>", file=code)
                print("  <set>" + series + "</set>", file=code)
                print("  <studio>" + studio + "</studio>", file=code)
                print("  <publisher>" + publisher + "</publisher>", file=code)
                print("  <director>" + director + "</director>", file=code)
                print("  <premiered>" + release + "</premiered>", file=code)
                print("  <release>" + release + "</release>", file=code)
                print("  <plot>" + outline + "</plot>", file=code)
                print("  <runtime>" + str(runtime) + "</runtime>", file=code)
                print("  <number>" + number + "</number>", file=code)
                print("  <cover>" + cover + "</cover>", file=code)
                print("  <website>" + website + "</website>", file=code)
                print("</movie>", file=code)
                log("[+]Nfo Wrote!         " + name_file + ".nfo")
        except Exception as error_info:
            log("[-]Write Failed!")
            log("[-]Error in PrintFiles: " + str(error_info))
            if keep_failed_move:
                move_failed(filepath, failed_folder)

    def fix_size(self, path: str, naming_rule: str, log: Callable[[str], None]) -> None:
        try:
            poster_path = path + "/" + naming_rule + "-poster.jpg"
            pic = Image.open(poster_path)
            (width, height) = pic.size
            if not 2 / 3 - 0.05 <= width / height <= 2 / 3 + 0.05:
                fixed_pic = pic.resize((int(width), int(3 / 2 * width)))
                fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))
                fixed_pic.paste(pic, (0, int((3 / 2 * width - height) / 2)))
                fixed_pic.save(poster_path)
        except Exception as error_info:
            log("[-]Error in fix_size: " + str(error_info))

    def move_movie_files(
        self,
        movie_list: list[str],
        dest_path: str,
        subtitle_types: list[str],
        log: Callable[[str], None],
    ) -> None:
        """Move video files and their subtitles to a target directory."""
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            log("[+]Created folder Movie_moved!")
        log("[+]Move Movies Start!")
        for movie in movie_list:
            if dest_path in movie:
                continue
            try:
                filename = movie.split("/")[-1]
                shutil.move(movie, dest_path + "/" + filename)
                log("   [+]Move " + filename + " to Movie_moved Success!")
                # Move subtitle files alongside
                base_name = filename.split(".")[0]
                path_old = movie.replace(filename, "")
                for sub in subtitle_types:
                    sub_src = path_old + "/" + base_name + sub
                    if os.path.exists(sub_src):
                        shutil.move(sub_src, dest_path + "/" + base_name + sub)
                        log("   [+]Sub moved! " + base_name + sub)
            except Exception as error_info:
                log("[-]Error in move_movie_files: " + str(error_info))
        log("[+]Move Movies All Finished!!!")

