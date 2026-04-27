#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import json
import logging
import logging.handlers
import traceback
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QTextCursor, QIcon, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QApplication, QShortcut
from PyQt5.QtCore import pyqtSignal, QT_VERSION_STR
import sys
import time
import os.path
import shutil
import re
import os
from configparser import ConfigParser
from Ui.AVDC_new import Ui_MainWindow
from core.config_io import save_config
from core.file_utils import movie_lists, escapePath, getNumber
from core.scrape_pipeline import getDataFromJSON
from core.image_processing import add_watermark, cut_poster, cut_poster_ai
from core.naming_service import resolve_name
from application.batch_service import BatchCallbacks, BatchWorkflowService
from application.file_processing_service import FileProcessDependencies, FileProcessingService
from application.file_system_service import FileSystemService
from application.remote_service import RemoteService


# ======================================================================== 自定义日志处理器
class UIHandler(logging.Handler):
    """将日志输出到UI界面的处理器"""
    def __init__(self, text_browser):
        super().__init__()
        self.text_browser = text_browser

    def emit(self, record):
        try:
            msg = self.format(record)
            # 使用 Qt 的信号机制安全地更新 UI
            from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(self.text_browser, "append",
                                  Qt.QueuedConnection,
                                  Q_ARG(str, msg))
        except Exception:
            self.handleError(record)


class ToggleableFileHandler(logging.FileHandler):
    """支持动态开关的文件处理器"""
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self.enabled = True
        self._file_handle = None

    def emit(self, record):
        if not self.enabled:
            return
        return super().emit(record)

    def set_enabled(self, enabled):
        """启用或禁用文件输出"""
        if self.enabled == enabled:
            return
        self.enabled = enabled
        if enabled and self.stream is None:
            self.stream = self._open()


class AVDC_Main_UI(QMainWindow):
    progressBarValue = pyqtSignal(int)  # 进度条信号量

    def __init__(self):
        super().__init__()
        # 初始化UI
        self.Ui = Ui_MainWindow()
        self.Ui.setupUi(self)

        # 初始化需要的变量
        self.version = "3.964"
        self.m_drag = False
        self.m_DragPosition = 0
        self.count_claw = 0  # 批量刮削次数
        self.select_file_path = ""
        self.json_array = {}

        # 初始化日志系统（需在 Init_Ui 之前完成）
        self.setup_logger()

        self.Init_Ui()
        self.Init()
        self.Load_Config()
        self.show_version()
        self.show()
        self.batch_service = BatchWorkflowService()
        self.file_service = FileProcessingService()
        self.fs_service = FileSystemService()
        self.remote_service = RemoteService()

    def Init_Ui(self):
        # 替换 listView_result 为 QTreeWidget
        self.Ui.gridLayout.removeWidget(self.Ui.listView_result)
        self.Ui.listView_result.deleteLater()
        self.Ui.treeWidget_number = QtWidgets.QTreeWidget(self.Ui.tab_main)
        self.Ui.treeWidget_number.setHeaderLabel("刮削结果")
        self.Ui.gridLayout.addWidget(self.Ui.treeWidget_number, 0, 0, 8, 1)

        # 添加开始按钮和进度条
        self.Ui.pushButton_start_cap = QtWidgets.QPushButton(
            "开始刮削", self.Ui.tab_main
        )
        self.Ui.pushButton_start_cap.setMinimumHeight(40)
        self.Ui.gridLayout.addWidget(self.Ui.pushButton_start_cap, 8, 0, 1, 1)

        self.Ui.progressBar_avdc = QtWidgets.QProgressBar(self.Ui.tab_main)
        self.Ui.progressBar_avdc.setMinimumHeight(40)
        self.Ui.gridLayout.addWidget(self.Ui.progressBar_avdc, 8, 1, 1, 2)

        self.Ui.label_percent = QtWidgets.QLabel("", self.Ui.tab_main)

        # 初始化 treeWidget Items
        self.item_succ = QTreeWidgetItem(self.Ui.treeWidget_number)
        self.item_succ.setText(0, "成功")
        self.item_fail = QTreeWidgetItem(self.Ui.treeWidget_number)
        self.item_fail.setText(0, "失败")
        self.Ui.treeWidget_number.expandAll()

        # 填充 ComboBox
        self.Ui.comboBox_2.addItems(
            [
                "All websites",
                "mgstage",
                "javbus",
                "jav321",
                "javdb",
                "avsox",
                "xcity",
                "dmm",
            ]
        )
        self.Ui.comboBox.addItems(["可添加头像的女优", "有头像的女优", "所有女优"])
        self.Ui.comboBox_ScrapWeb_2.addItems(
            ["javbus", "javdb", "avsox", "dmm", "mgstage", "jav321", "xcity", "fc2"]
        )

        ico_path = ""
        if os.path.exists("AVDC-ico.png"):
            ico_path = "AVDC-ico.png"
        elif os.path.exists("Img/AVDC-ico.png"):
            ico_path = "Img/AVDC-ico.png"
        if ico_path:
            self.setWindowIcon(QIcon(ico_path))  # 设置窗口图标

        self.Ui.progressBar_avdc.setValue(0)  # 进度条清0
        self.progressBarValue.connect(self.set_processbar)
        self.Ui.progressBar_avdc.setTextVisible(True)

        # 设置快捷键：Ctrl+1,2,3,4,5 切换主标签页
        self.shortcut_cmd1 = QtWidgets.QShortcut(QKeySequence("Ctrl+1"), self)
        self.shortcut_cmd1.activated.connect(lambda: self.Ui.tabWidget.setCurrentIndex(0))  # 主页

        self.shortcut_cmd2 = QtWidgets.QShortcut(QKeySequence("Ctrl+2"), self)
        self.shortcut_cmd2.activated.connect(lambda: self.Ui.tabWidget.setCurrentIndex(1))  # 日志

        self.shortcut_cmd3 = QtWidgets.QShortcut(QKeySequence("Ctrl+3"), self)
        self.shortcut_cmd3.activated.connect(lambda: self.Ui.tabWidget.setCurrentIndex(2))  # 工具

        self.shortcut_cmd4 = QtWidgets.QShortcut(QKeySequence("Ctrl+4"), self)
        self.shortcut_cmd4.activated.connect(lambda: self.Ui.tabWidget.setCurrentIndex(3))  # 设置

        self.shortcut_cmd5 = QtWidgets.QShortcut(QKeySequence("Ctrl+5"), self)
        self.shortcut_cmd5.activated.connect(lambda: self.Ui.tabWidget.setCurrentIndex(4))  # 关于

    def cleanup_old_logs(self, max_keep=100):
        """清理旧日志文件，仅保留最新的 max_keep 个"""
        log_dir = "Log"
        if not os.path.exists(log_dir):
            return

        try:
            # 获取所有日志文件
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.startswith("app_") and filename.endswith(".log"):
                    filepath = os.path.join(log_dir, filename)
                    # 获取文件修改时间
                    mtime = os.path.getmtime(filepath)
                    log_files.append((filepath, mtime))

            # 按修改时间排序（最新的在前面）
            log_files.sort(key=lambda x: x[1], reverse=True)

            # 删除超出限制的旧日志文件
            if len(log_files) > max_keep:
                files_to_delete = log_files[max_keep:]
                deleted_count = 0
                for filepath, _ in files_to_delete:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        print(f"删除日志文件失败: {filepath}, 错误: {str(e)}")

                if deleted_count > 0:
                    print(f"已清理 {deleted_count} 个旧日志文件")

        except Exception as e:
            print(f"清理旧日志文件失败: {str(e)}")

    def setup_logger(self):
        """设置统一的日志系统"""
        try:
            # 创建日志目录
            if not os.path.exists("Log"):
                os.makedirs("Log")

            # 清理旧日志文件，仅保留最新的100个
            self.cleanup_old_logs(max_keep=100)

            # 创建 logger
            self.logger = logging.getLogger('AVDC')
            self.logger.setLevel(logging.DEBUG)
            self.logger.handlers.clear()  # 清除可能存在的旧处理器

            # 设置日志格式
            formatter = logging.Formatter('%(message)s')

            # 1. 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 2. UI 界面处理器（输出到 textBrowser_log）
            ui_handler = UIHandler(self.Ui.textBrowser_log)
            ui_handler.setLevel(logging.INFO)
            ui_handler.setFormatter(formatter)
            self.logger.addHandler(ui_handler)

            # 3. 文件处理器（可动态开关）
            log_filename = f"Log/app_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}.log"
            self.log_file_handler = ToggleableFileHandler(log_filename, encoding='utf-8')
            self.log_file_handler.setLevel(logging.DEBUG)
            self.log_file_handler.setFormatter(formatter)

            # 根据配置启用/禁用文件日志
            file_log_enabled = self.Ui.radioButton_9.isChecked()
            self.log_file_handler.set_enabled(file_log_enabled)

            self.logger.addHandler(self.log_file_handler)

            self.logger.info("[*]======================== AVDC ========================")
            self.logger.info(f"[*]日志系统初始化完成")
            self.logger.info(f"[*]工作目录: {os.getcwd()}")
            self.logger.info(f"[*]日志文件: {log_filename}")
            self.logger.info(f"[*]文件日志: {'启用' if file_log_enabled else '禁用'}")
            self.logger.info(f"[*]Python版本: {sys.version.split()[0]}")
            self.logger.info(f"[*]PyQt版本: {QT_VERSION_STR}")
            self.logger.info("[*]======================================================")

        except Exception as e:
            print(f"初始化日志系统失败: {str(e)}")
            # 创建备用 logger
            self.logger = logging.getLogger('AVDC_Fallback')
            self.logger.setLevel(logging.ERROR)
            self.logger.addHandler(logging.StreamHandler())
            self.logger.error(f"日志系统初始化失败: {str(e)}")

    def toggle_file_logging(self, enabled):
        """切换文件日志开关"""
        if hasattr(self, 'log_file_handler'):
            self.log_file_handler.set_enabled(enabled)
            status = '启用' if enabled else '禁用'
            self.logger.info(f"[*]文件日志已{status}")

    def log_error(self, error, context=""):
        """记录错误日志"""
        error_msg = f"[-]Error{': ' + context if context else ': '} {str(error)}"
        self.logger.error(error_msg)

    def log_info(self, message):
        """记录信息日志"""
        self.logger.info(message)

    # ========================================================================按钮点击事件
    def Init(self):
        self.Ui.treeWidget_number.clicked.connect(self.treeWidget_number_clicked)
        self.Ui.pushButton_ChooseFile.clicked.connect(
            self.pushButton_select_file_clicked
        )
        self.Ui.pushButton_start_cap.clicked.connect(self.pushButton_start_cap_clicked)
        self.Ui.pushButton.clicked.connect(self.pushButton_save_config_clicked)
        self.Ui.pushButton_2.clicked.connect(self.pushButton_init_config_clicked)
        self.Ui.pushButton_StartMove.clicked.connect(self.move_file)
        self.Ui.pushButton_AddAvatar.clicked.connect(
            self.pushButton_add_actor_pic_clicked
        )
        self.Ui.pushButton_Check.clicked.connect(self.pushButton_show_pic_actor_clicked)
        self.Ui.pushButton_6.clicked.connect(self.pushButton_select_thumb_clicked)
        self.Ui.pushButton_StartScrap.clicked.connect(
            self.pushButton_start_single_file_clicked
        )
        self.Ui.horizontalSlider_2.valueChanged.connect(self.lcdNumber_timeout_change)
        self.Ui.horizontalSlider_3.valueChanged.connect(self.lcdNumber_retry_change)
        self.Ui.horizontalSlider.valueChanged.connect(self.lcdNumber_mark_size_change)

    # ========================================================================显示版本号
    def show_version(self):
        self.logger.info("[*]======================== AVDC ========================")
        self.logger.info(f"[*]                     Version {self.version}")
        self.logger.info("[*]======================================================")

    def lcdNumber_timeout_change(self):
        timeout = self.Ui.horizontalSlider_2.value()
        self.Ui.lcdNumber.display(timeout)

    def lcdNumber_retry_change(self):
        retry = self.Ui.horizontalSlider_3.value()
        self.Ui.lcdNumber_2.display(retry)

    def lcdNumber_mark_size_change(self):
        mark_size = self.Ui.horizontalSlider.value()
        self.Ui.label_12.setText(str(mark_size))  # changed to setText

    def treeWidget_number_clicked(self, qmodeLindex):
        item = self.Ui.treeWidget_number.currentItem()
        if item.text(0) != "成功" and item.text(0) != "失败":
            try:
                index_json = str(item.text(0)).split(".")[0]
                self.add_label_info(self.json_array[str(index_json)])
            except Exception:
                print(item.text(0) + ": No info!")

    def pushButton_start_cap_clicked(self):
        self.Ui.pushButton_start_cap.setEnabled(False)
        self.progressBarValue.emit(int(0))
        try:
            self.count_claw += 1
            self.logger.info(f"[*]开始第 {self.count_claw} 次刮削")
            t = threading.Thread(target=self.AVDC_Main)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.log_error(error_info, "pushButton_start_cap_clicked")
            self.add_text_main(
                "[-]Error in pushButton_start_cap_clicked: " + str(error_info)
            )

    # ========================================================================恢复默认config.ini
    def pushButton_init_config_clicked(self):
        try:
            t = threading.Thread(target=self.init_config_clicked)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main(
                "[-]Error in pushButton_save_config_clicked: " + str(error_info)
            )

    def init_config_clicked(self):
        json_config = {
            "show_poster": 1,
            "main_mode": 1,
            "soft_link": 0,
            "switch_debug": 1,
            "failed_file_move": 1,
            "update_check": 1,
            "save_log": 1,
            "website": "all",
            "failed_output_folder": "failed",
            "success_output_folder": "JAV_output",
            "proxy": "",
            "timeout": 7,
            "retry": 3,
            "folder_name": "actor/number-title-release",
            "naming_media": "number-title",
            "naming_file": "number",
            "literals": r"\()",
            "folders": "failed,JAV_output",
            "string": "1080p,720p,22-sht.me,-HD",
            "emby_url": "localhost:8096",
            "api_key": "",
            "media_path": "E:/TEMP",
            "media_type": ".mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.MP4|.AVI|.RMVB|.WMV|.MOV|.MKV|.FLV|.TS|.WEBM",
            "sub_type": ".smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.txt|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml",
            "poster_mark": 1,
            "thumb_mark": 1,
            "mark_size": 3,
            "mark_type": "SUB,LEAK,UNCENSORED",
            "mark_pos": "top_left",
            "uncensored_poster": 0,
            "uncensored_prefix": "S2M|BT|LAF|SMD",
            "nfo_download": 1,
            "poster_download": 1,
            "fanart_download": 1,
            "thumb_download": 1,
            "extrafanart_download": 0,
            "extrafanart_folder": "extrafanart",
        }
        save_config(json_config)
        self.Load_Config()

    # ========================================================================加载config
    def Load_Config(self):
        config_file = "config.ini"
        config = ConfigParser()
        config.read(config_file, encoding="UTF-8")
        # ========================================================================common
        if int(config["common"]["main_mode"]) == 1:
            self.Ui.radioButton.setChecked(True)
        elif int(config["common"]["main_mode"]) == 2:
            self.Ui.radioButton_2.setChecked(True)
        if int(config["common"]["soft_link"]) == 1:
            self.Ui.radioButton_3.setChecked(True)
        elif int(config["common"]["soft_link"]) == 0:
            self.Ui.radioButton_4.setChecked(True)
        if int(config["common"]["failed_file_move"]) == 1:
            self.Ui.radioButton_11.setChecked(True)
        elif int(config["common"]["failed_file_move"]) == 0:
            self.Ui.radioButton_12.setChecked(True)
        # show_poster removed/merged? No checkbox in UI for showing poster in Main tab, but handled by downloads?
        # In old UI checkBox_cover was "Show Poster" on main tab. New UI doesn't have it on main tab.

        if config["common"]["website"] == "all":
            self.Ui.comboBox_2.setCurrentIndex(0)
        elif config["common"]["website"] == "mgstage":
            self.Ui.comboBox_2.setCurrentIndex(1)
        elif config["common"]["website"] == "javbus":
            self.Ui.comboBox_2.setCurrentIndex(2)
        elif config["common"]["website"] == "jav321":
            self.Ui.comboBox_2.setCurrentIndex(3)
        elif config["common"]["website"] == "javdb":
            self.Ui.comboBox_2.setCurrentIndex(4)
        elif config["common"]["website"] == "avsox":
            self.Ui.comboBox_2.setCurrentIndex(5)
        elif config["common"]["website"] == "xcity":
            self.Ui.comboBox_2.setCurrentIndex(6)
        elif config["common"]["website"] == "dmm":
            self.Ui.comboBox_2.setCurrentIndex(7)

        self.Ui.lineEdit_8.setText(config["common"]["success_output_folder"])
        self.Ui.lineEdit_9.setText(config["common"]["failed_output_folder"])
        # ========================================================================proxy
        if config["proxy"]["type"] == "no" or config["proxy"]["type"] == "":
            self.Ui.radioButton_25.setChecked(True)
        elif config["proxy"]["type"] == "http":
            self.Ui.radioButton_19.setChecked(True)
        elif config["proxy"]["type"] == "socks5":
            self.Ui.radioButton_20.setChecked(True)
        self.Ui.lineEdit_14.setText(config["proxy"]["proxy"])
        self.Ui.horizontalSlider_2.setValue(int(config["proxy"]["timeout"]))
        self.Ui.horizontalSlider_3.setValue(int(config["proxy"]["retry"]))
        # ========================================================================Name_Rule
        self.Ui.lineEdit.setText(config["Name_Rule"]["folder_name"])
        self.Ui.lineEdit_3.setText(config["Name_Rule"]["naming_media"])
        self.Ui.lineEdit_2.setText(config["Name_Rule"]["naming_file"])
        # ========================================================================update
        if int(config["update"]["update_check"]) == 1:
            self.Ui.radioButton_7.setChecked(True)
        elif int(config["update"]["update_check"]) == 0:
            self.Ui.radioButton_8.setChecked(True)
        # ========================================================================log
        if int(config["log"]["save_log"]) == 1:
            self.Ui.radioButton_9.setChecked(True)
        elif int(config["log"]["save_log"]) == 0:
            self.Ui.radioButton_10.setChecked(True)
        # ========================================================================media
        self.Ui.lineEdit_6.setText(config["media"]["media_type"])
        self.Ui.lineEdit_4.setText(config["media"]["sub_type"])
        self.Ui.lineEdit_7.setText(
            str(config["media"]["media_path"]).replace("\\", "/")
        )
        # ========================================================================escape
        self.Ui.lineEdit_5.setText(config["escape"]["folders"])
        self.Ui.lineEdit_13.setText(config["escape"]["literals"])
        self.Ui.lineEdit_ExcludeDir.setText(
            config["escape"]["folders"]
        )  # Use same value for tool
        self.Ui.lineEdit_12.setText(config["escape"]["string"])
        # ========================================================================debug_mode
        if int(config["debug_mode"]["switch"]) == 1:
            self.Ui.radioButton_5.setChecked(True)
        elif int(config["debug_mode"]["switch"]) == 0:
            self.Ui.radioButton_6.setChecked(True)
        # ========================================================================emby
        self.Ui.lineEdit_EmbyAddr.setText(config["emby"]["emby_url"])
        self.Ui.lineEdit_APIKey.setText(config["emby"]["api_key"])
        # ========================================================================mark
        if int(config["mark"]["poster_mark"]) == 1:
            self.Ui.radioButton_15.setChecked(True)
        elif int(config["mark"]["poster_mark"]) == 0:
            self.Ui.radioButton_16.setChecked(True)
        if int(config["mark"]["thumb_mark"]) == 1:
            self.Ui.radioButton_17.setChecked(True)
        elif int(config["mark"]["thumb_mark"]) == 0:
            self.Ui.radioButton_18.setChecked(True)
        self.Ui.horizontalSlider.setValue(int(config["mark"]["mark_size"]))
        if "SUB" in str(config["mark"]["mark_type"]).upper():
            self.Ui.checkBox_5.setChecked(True)
        if "LEAK" in str(config["mark"]["mark_type"]).upper():
            self.Ui.checkBox_6.setChecked(True)
        if "UNCENSORED" in str(config["mark"]["mark_type"]).upper():
            self.Ui.checkBox_7.setChecked(True)
        if "top_left" == config["mark"]["mark_pos"]:
            self.Ui.radioButton_21.setChecked(True)
        elif "bottom_left" == config["mark"]["mark_pos"]:
            self.Ui.radioButton_23.setChecked(True)
        elif "top_right" == config["mark"]["mark_pos"]:
            self.Ui.radioButton_24.setChecked(True)
        elif "bottom_right" == config["mark"]["mark_pos"]:
            self.Ui.radioButton_22.setChecked(True)
        # ========================================================================uncensored
        if int(config["uncensored"]["uncensored_poster"]) == 1:
            self.Ui.radioButton_27.setChecked(True)
        elif int(config["uncensored"]["uncensored_poster"]) == 0:
            self.Ui.radioButton_26.setChecked(True)
        self.Ui.lineEdit_11.setText(config["uncensored"]["uncensored_prefix"])
        # ========================================================================file_download
        if int(config["file_download"]["nfo"]) == 1:
            self.Ui.checkBox.setChecked(True)
        elif int(config["file_download"]["nfo"]) == 0:
            self.Ui.checkBox.setChecked(False)
        if int(config["file_download"]["poster"]) == 1:
            self.Ui.checkBox_2.setChecked(True)
        elif int(config["file_download"]["poster"]) == 0:
            self.Ui.checkBox_2.setChecked(False)
        if int(config["file_download"]["fanart"]) == 1:
            self.Ui.checkBox_3.setChecked(True)
        elif int(config["file_download"]["fanart"]) == 0:
            self.Ui.checkBox_3.setChecked(False)
        if int(config["file_download"]["thumb"]) == 1:
            self.Ui.checkBox_4.setChecked(True)
        elif int(config["file_download"]["thumb"]) == 0:
            self.Ui.checkBox_4.setChecked(False)
        # ========================================================================extrafanart
        if int(config["extrafanart"]["extrafanart_download"]) == 1:
            self.Ui.radioButton_13.setChecked(True)
        elif int(config["extrafanart"]["extrafanart_download"]) == 0:
            self.Ui.radioButton_14.setChecked(True)
        self.Ui.lineEdit_10.setText(config["extrafanart"]["extrafanart_folder"])

    # ========================================================================读取设置页设置，保存在config.ini
    def pushButton_save_config_clicked(self):
        try:
            t = threading.Thread(target=self.save_config_clicked)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main(
                "[-]Error in pushButton_save_config_clicked: " + str(error_info)
            )

    def save_config_clicked(self):
        main_mode = 1
        failed_file_move = 1
        soft_link = 0
        show_poster = 0
        switch_debug = 0
        update_check = 0
        save_log = 0
        website = ""
        mark_type = ""
        mark_pos = ""
        uncensored_poster = 0
        nfo_download = 0
        poster_download = 0
        fanart_download = 0
        thumb_download = 0
        extrafanart_download = 0
        proxy_type = ""
        # ========================================================================common
        if self.Ui.radioButton.isChecked():  # 普通模式
            main_mode = 1
        elif self.Ui.radioButton_2.isChecked():  # 整理模式
            main_mode = 2
        if self.Ui.radioButton_3.isChecked():  # 软链接开
            soft_link = 1
        elif self.Ui.radioButton_4.isChecked():  # 软链接关
            soft_link = 0
        if self.Ui.radioButton_5.isChecked():  # 调试模式开
            switch_debug = 1
        elif self.Ui.radioButton_6.isChecked():  # 调试模式关
            switch_debug = 0
        if self.Ui.radioButton_7.isChecked():  # 检查更新
            update_check = 1
        elif self.Ui.radioButton_8.isChecked():  # 不检查更新
            update_check = 0
        if self.Ui.radioButton_9.isChecked():  # 开启日志
            save_log = 1
        elif self.Ui.radioButton_10.isChecked():  # 关闭日志
            save_log = 0
        # show_poster assumed 1 if downloads checked or default

        if self.Ui.radioButton_11.isChecked():  # 失败移动开
            failed_file_move = 1
        elif self.Ui.radioButton_12.isChecked():  # 失败移动关
            failed_file_move = 0

        if self.Ui.comboBox_2.currentText() == "All websites":  # all
            website = "all"
        elif self.Ui.comboBox_2.currentText() == "mgstage":  # mgstage
            website = "mgstage"
        elif self.Ui.comboBox_2.currentText() == "javbus":  # javbus
            website = "javbus"
        elif self.Ui.comboBox_2.currentText() == "jav321":  # jav321
            website = "jav321"
        elif self.Ui.comboBox_2.currentText() == "javdb":  # javdb
            website = "javdb"
        elif self.Ui.comboBox_2.currentText() == "avsox":  # avsox
            website = "avsox"
        elif self.Ui.comboBox_2.currentText() == "xcity":  # xcity
            website = "xcity"
        elif self.Ui.comboBox_2.currentText() == "dmm":  # dmm
            website = "dmm"
        # ========================================================================proxy
        if self.Ui.radioButton_19.isChecked():  # http proxy
            proxy_type = "http"
        elif self.Ui.radioButton_20.isChecked():  # socks5 proxy
            proxy_type = "socks5"
        elif self.Ui.radioButton_25.isChecked():  # nouse proxy
            proxy_type = "no"
        # ========================================================================水印
        if self.Ui.radioButton_15.isChecked():  # 封面添加水印
            poster_mark = 1
        else:  # 关闭封面添加水印
            poster_mark = 0
        if self.Ui.radioButton_17.isChecked():  # 缩略图添加水印
            thumb_mark = 1
        else:  # 关闭缩略图添加水印
            thumb_mark = 0
        if self.Ui.checkBox_5.isChecked():  # 字幕
            mark_type += ",SUB"
        if self.Ui.checkBox_6.isChecked():  # 流出
            mark_type += ",LEAK"
        if self.Ui.checkBox_7.isChecked():  # 无码
            mark_type += ",UNCENSORED"
        if self.Ui.radioButton_21.isChecked():  # 左上
            mark_pos = "top_left"
        elif self.Ui.radioButton_23.isChecked():  # 左下
            mark_pos = "bottom_left"
        elif self.Ui.radioButton_24.isChecked():  # 右上
            mark_pos = "top_right"
        elif self.Ui.radioButton_22.isChecked():  # 右下
            mark_pos = "bottom_right"
        if self.Ui.radioButton_26.isChecked():  # 官方
            uncensored_poster = 0
        elif self.Ui.radioButton_27.isChecked():  # 裁剪
            uncensored_poster = 1
        # ========================================================================下载文件，剧照
        if self.Ui.checkBox.isChecked():
            nfo_download = 1
        else:
            nfo_download = 0
        if self.Ui.checkBox_2.isChecked():
            poster_download = 1
        else:
            poster_download = 0
        if self.Ui.checkBox_3.isChecked():
            fanart_download = 1
        else:
            fanart_download = 0
        if self.Ui.checkBox_4.isChecked():
            thumb_download = 1
        else:
            thumb_download = 0
        if self.Ui.radioButton_13.isChecked():  # 下载剧照
            extrafanart_download = 1
        else:  # 关闭封面
            extrafanart_download = 0

        json_config = {
            "main_mode": main_mode,
            "soft_link": soft_link,
            "switch_debug": switch_debug,
            "show_poster": show_poster,
            "failed_file_move": failed_file_move,
            "update_check": update_check,
            "save_log": save_log,
            "website": website,
            "failed_output_folder": self.Ui.lineEdit_9.text(),
            "success_output_folder": self.Ui.lineEdit_8.text(),
            "type": proxy_type,
            "proxy": self.Ui.lineEdit_14.text(),
            "timeout": self.Ui.horizontalSlider_2.value(),
            "retry": self.Ui.horizontalSlider_3.value(),
            "folder_name": self.Ui.lineEdit.text(),
            "naming_media": self.Ui.lineEdit_3.text(),
            "naming_file": self.Ui.lineEdit_2.text(),
            "literals": self.Ui.lineEdit_13.text(),
            "folders": self.Ui.lineEdit_5.text(),
            "string": self.Ui.lineEdit_12.text(),
            "emby_url": self.Ui.lineEdit_EmbyAddr.text(),
            "api_key": self.Ui.lineEdit_APIKey.text(),
            "media_path": self.Ui.lineEdit_7.text(),
            "media_type": self.Ui.lineEdit_6.text(),
            "sub_type": self.Ui.lineEdit_4.text(),
            "poster_mark": poster_mark,
            "thumb_mark": thumb_mark,
            "mark_size": self.Ui.horizontalSlider.value(),
            "mark_type": mark_type.strip(","),
            "mark_pos": mark_pos,
            "uncensored_poster": uncensored_poster,
            "uncensored_prefix": self.Ui.lineEdit_11.text(),
            "nfo_download": nfo_download,
            "poster_download": poster_download,
            "fanart_download": fanart_download,
            "thumb_download": thumb_download,
            "extrafanart_download": extrafanart_download,
            "extrafanart_folder": self.Ui.lineEdit_10.text(),
        }
        save_config(json_config)

    # ========================================================================小工具-单视频刮削
    def pushButton_select_file_clicked(self):
        path = self.Ui.lineEdit_7.text()
        filepath, filetype = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选取视频文件",
            path,
            "Movie Files(*.mp4 "
            "*.avi *.rmvb *.wmv "
            "*.mov *.mkv *.flv *.ts "
            "*.webm *.MP4 *.AVI "
            "*.RMVB *.WMV *.MOV "
            "*.MKV *.FLV *.TS "
            "*.WEBM);;All Files(*)",
        )
        self.select_file_path = filepath
        self.add_text_main("[+]Selected file: " + filepath)

    def pushButton_start_single_file_clicked(self):
        if self.select_file_path != "":
            self.Ui.tabWidget.setCurrentIndex(1)  # Switch to Log tab
            try:
                t = threading.Thread(target=self.select_file_thread)
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main(
                    "[-]Error in pushButton_start_single_file_clicked: "
                    + str(error_info)
                )
        else:
            self.add_text_main("[-]Please select a file first!")

    def select_file_thread(self):
        file_name = self.select_file_path
        file_root = os.getcwd().replace("\\\\", "/").replace("\\", "/")
        file_path = (
            file_name.replace(file_root, ".").replace("\\\\", "/").replace("\\", "/")
        )
        # 获取去掉拓展名的文件名做为番号
        file_name = os.path.splitext(file_name.split("/")[-1])[0]
        mode = self.Ui.comboBox_ScrapWeb_2.currentIndex() + 1
        # 指定的网址
        appoint_url = self.Ui.lineEdit_ScrapWeb_1.text()
        appoint_number = self.Ui.lineEdit_SerialNumber_2.text()
        try:
            if appoint_number:
                file_name = appoint_number
            else:
                if "-CD" in file_name or "-cd" in file_name:
                    part = ""
                    if re.search(r"-CD\d+", file_name):
                        part = re.findall(r"-CD\d+", file_name)[0]
                    elif re.search(r"-cd\d+", file_name):
                        part = re.findall(r"-cd\d+", file_name)[0]
                    file_name = file_name.replace(part, "")
                if "-c." in file_path or "-C." in file_path:
                    file_name = file_name[0:-2]
            self.add_text_main(
                "[!]Making Data for   ["
                + file_path
                + "], the number is ["
                + file_name
                + "]"
            )
            self.Core_Main(file_path, file_name, mode, 0, appoint_url)
        except Exception as error_info:
            self.add_text_main("[-]Error in select_file_thread: " + str(error_info))
        self.add_text_main("[*]======================================================")

    # ========================================================================小工具-裁剪封面图
    def pushButton_select_thumb_clicked(self):
        path = self.Ui.lineEdit_7.text()
        filePath, fileType = QtWidgets.QFileDialog.getOpenFileName(
            self, "选取缩略图", path, "Picture Files(*.jpg);;All Files(*)"
        )
        if filePath != "":
            self.Ui.tabWidget.setCurrentIndex(1)
            try:
                t = threading.Thread(target=self.select_thumb_thread, args=(filePath,))
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main(
                    "[-]Error in pushButton_select_thumb_clicked: " + str(error_info)
                )

    def select_thumb_thread(self, file_path):
        file_name = file_path.split("/")[-1]
        file_path = file_path.replace("/" + file_name, "")
        self.image_cut(file_path, file_name, 2)
        self.add_text_main("[*]======================================================")

    def image_cut(self, path, file_name, mode=1):
        png_name = file_name.replace("-thumb.jpg", "-poster.jpg")
        file_path = os.path.join(path, file_name)
        png_path = os.path.join(path, png_name)
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
        except Exception as error_info:
            self.add_text_main("[-]Error in image_cut: " + str(error_info))
            return

        result = cut_poster_ai(file_path, png_path)
        if result is None:
            self.add_text_main("[-]Error in image_cut: AI service unavailable")
            return

        self.add_text_main(
            "[+]Poster Cut         " + png_name + " from " + file_name + "!"
        )
        if mode == 2:
            pix = QPixmap(file_path)
            self.Ui.label_thumbnail.setScaledContents(True)
            self.Ui.label_thumbnail.setPixmap(pix)
            pix = QPixmap(png_path)
            self.Ui.label_cover.setScaledContents(True)
            self.Ui.label_cover.setPixmap(pix)

    # ========================================================================小工具-视频移动
    def move_file(self):
        self.Ui.tabWidget.setCurrentIndex(1)
        try:
            t = threading.Thread(target=self.move_file_thread)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main("[-]Error in move_file: " + str(error_info))

    def move_file_thread(self):
        escape_dir = self.Ui.lineEdit_ExcludeDir.text()
        sub_type = self.Ui.lineEdit_4.text().split("|")
        movie_path = self.Ui.lineEdit_7.text()
        movie_type = self.Ui.lineEdit_6.text()
        movie_list = movie_lists(escape_dir, movie_type, movie_path)
        des_path = movie_path + "/Movie_moved"
        if not os.path.exists(des_path):
            self.add_text_main("[+]Created folder Movie_moved!")
            os.makedirs(des_path)
        self.add_text_main("[+]Move Movies Start!")
        for movie in movie_list:
            if des_path in movie:
                continue
            sour = movie
            des = des_path + "/" + sour.split("/")[-1]
            try:
                shutil.move(sour, des)
                self.add_text_main(
                    "   [+]Move " + sour.split("/")[-1] + " to Movie_moved Success!"
                )
                path_old = sour.replace(sour.split("/")[-1], "")
                filename = sour.split("/")[-1].split(".")[0]
                for sub in sub_type:
                    if os.path.exists(path_old + "/" + filename + sub):  # 字幕移动
                        shutil.move(
                            path_old + "/" + filename + sub,
                            des_path + "/" + filename + sub,
                        )
                        self.add_text_main("   [+]Sub moved! " + filename + sub)
            except Exception as error_info:
                self.add_text_main("[-]Error in move_file_thread: " + str(error_info))
        self.add_text_main("[+]Move Movies All Finished!!!")
        self.add_text_main("[*]======================================================")

    # ========================================================================小工具-emby女优头像
    def pushButton_add_actor_pic_clicked(self):  # 添加头像按钮响应
        self.Ui.tabWidget.setCurrentIndex(1)
        emby_url = self.Ui.lineEdit_EmbyAddr.text()
        api_key = self.Ui.lineEdit_APIKey.text()
        if emby_url == "":
            self.add_text_main("[-]The emby_url is empty!")
            self.add_text_main(
                "[*]======================================================"
            )
            return
        elif api_key == "":
            self.add_text_main("[-]The api_key is empty!")
            self.add_text_main(
                "[*]======================================================"
            )
            return
        try:
            t = threading.Thread(target=self.found_profile_picture, args=(1,))
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main(
                "[-]Error in pushButton_add_actor_pic_clicked: " + str(error_info)
            )

    def pushButton_show_pic_actor_clicked(self):  # 查看按钮响应
        self.Ui.tabWidget.setCurrentIndex(1)
        emby_url = self.Ui.lineEdit_EmbyAddr.text()
        api_key = self.Ui.lineEdit_APIKey.text()
        if emby_url == "":
            self.add_text_main("[-]The emby_url is empty!")
            self.add_text_main(
                "[*]======================================================"
            )
            return
        elif api_key == "":
            self.add_text_main("[-]The api_key is empty!")
            self.add_text_main(
                "[*]======================================================"
            )
            return
        if self.Ui.comboBox.currentIndex() == 0:  # 可添加头像的女优
            try:
                t = threading.Thread(target=self.found_profile_picture, args=(2,))
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main(
                    "[-]Error in pushButton_show_pic_actor_clicked: " + str(error_info)
                )
        else:
            try:
                t = threading.Thread(
                    target=self.show_actor,
                    args=(self.Ui.comboBox.currentIndex(),),
                )
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main(
                    "[-]Error in pushButton_show_pic_actor_clicked: " + str(error_info)
                )

    def show_actor(self, mode):  # 按模式显示相应列表
        if mode == 1:  # 没有头像的女优
            self.add_text_main("[+]没有头像的女优!")
        elif mode == 2:  # 有头像的女优
            self.add_text_main("[+]有头像的女优!")
        elif mode == 3:  # 所有女优
            self.add_text_main("[+]所有女优!")
        actor_list = self.get_emby_actor_list()
        if actor_list["TotalRecordCount"] == 0:
            self.add_text_main(
                "[*]======================================================"
            )
            return
        for line in self.remote_service.show_actor_lines(actor_list, mode):
            self.add_text_main(line)
        self.add_text_main("[*]======================================================")

    def get_emby_actor_list(self):  # 获取emby的演员列表
        return self.remote_service.get_emby_actor_list(
            self.Ui.lineEdit_EmbyAddr.text(),
            self.Ui.lineEdit_APIKey.text(),
            self.add_text_main,
        )

    def found_profile_picture(
        self, mode
    ):  # mode=1，上传头像，mode=2，显示可添加头像的女优
        if mode == 1:
            self.add_text_main("[+]Start upload profile pictures!")
        elif mode == 2:
            self.add_text_main("[+]可添加头像的女优!")
        path = "Actor"
        if not os.path.exists(path):
            self.add_text_main("[+]Actor folder not exist!")
            self.add_text_main(
                "[*]======================================================"
            )
            return
        path_success = "Actor/Success"
        if not os.path.exists(path_success):
            os.makedirs(path_success)
        profile_pictures = os.listdir(path)
        actor_list = self.get_emby_actor_list()
        if actor_list["TotalRecordCount"] == 0:
            self.add_text_main(
                "[*]======================================================"
            )
            return
        lines = self.remote_service.find_profile_pictures(
            mode,
            actor_list,
            profile_pictures,
            path_success,
            self.Ui.lineEdit_EmbyAddr.text(),
            self.Ui.lineEdit_APIKey.text(),
            self.add_text_main,
            upload_enabled=True,
        )
        for line in lines:
            self.add_text_main(line)
        self.add_text_main("[*]======================================================")

    def upload_profile_picture(self, count, actor, pic_path):  # 上传头像
        self.remote_service.upload_profile_picture(
            self.Ui.lineEdit_EmbyAddr.text(),
            self.Ui.lineEdit_APIKey.text(),
            count,
            actor,
            pic_path,
            self.add_text_main,
        )

    # ========================================================================自定义文件名
    def get_naming_rule(self, json_data):
        return resolve_name(json_data["naming_file"], json_data)

    # ========================================================================语句添加到日志框
    def add_text_main(self, text):
        """统一的日志输出接口 - 输出到界面、文件和控制台"""
        try:
            # 使用统一的日志系统
            if hasattr(self, 'logger'):
                self.logger.info(str(text))
        except Exception as error_info:
            print(f"[-]Error in add_text_main: {str(error_info)}")

    # ========================================================================移动到失败文件夹
    def moveFailedFolder(self, filepath, failed_folder):
        if self.Ui.radioButton_11.isChecked() and self.Ui.radioButton_4.isChecked():
            try:
                self.fs_service.move_failed_folder(filepath, failed_folder, True)
                self.add_text_main(
                    "[-]Move "
                    + os.path.split(filepath)[1]
                    + " to Failed output folder Success!"
                )
            except Exception as error_info:
                self.add_text_main("[-]Error in moveFailedFolder! " + str(error_info))

    # ========================================================================下载文件
    def DownloadFileWithFilename(
        self, url, filename, path, Config, filepath, failed_folder
    ):
        self.remote_service.download_file_with_filename(
            url,
            filename,
            path,
            filepath,
            failed_folder,
            self.add_text_main,
            self.moveFailedFolder,
        )

    # ========================================================================下载缩略图
    def thumbDownload(
        self, json_data, path, naming_rule, Config, filepath, failed_folder
    ):
        self.remote_service.thumb_download(
            json_data,
            path,
            naming_rule,
            Config,
            filepath,
            failed_folder,
            self.add_text_main,
            self.moveFailedFolder,
        )

    def deletethumb(self, path, naming_rule):
        self.fs_service.delete_thumb(
            path, naming_rule, self.Ui.checkBox_4.isChecked(), self.add_text_main
        )

    # ========================================================================无码片下载封面图
    def smallCoverDownload(
        self, path, naming_rule, json_data, Config, filepath, failed_folder
    ):
        return self.remote_service.small_cover_download(
            path,
            naming_rule,
            json_data,
            Config,
            filepath,
            failed_folder,
            self.add_text_main,
            self.moveFailedFolder,
        )

    # ========================================================================下载剧照
    def extrafanartDownload(self, json_data, path, Config, filepath, failed_folder):
        self.remote_service.extrafanart_download(
            json_data,
            path,
            Config,
            filepath,
            failed_folder,
            self.Ui.lineEdit_10.text(),
            self.add_text_main,
            self.moveFailedFolder,
        )

    # ========================================================================打印NFO
    def PrintFiles(
        self, path, name_file, cn_sub, leak, json_data, filepath, failed_folder
    ):
        self.fs_service.write_nfo(
            path,
            name_file,
            cn_sub,
            leak,
            json_data,
            filepath,
            failed_folder,
            self.Ui.radioButton_11.isChecked(),
            self.add_text_main,
            self.moveFailedFolder,
        )

    # ========================================================================thumb复制为fanart
    def copyRenameJpgToFanart(self, path, naming_rule):
        self.fs_service.copy_fanart(path, naming_rule, self.add_text_main)

    # ========================================================================移动视频、字幕
    def pasteFileToFolder(self, filepath, path, naming_rule, failed_folder):
        return self.fs_service.paste_file_to_folder(
            filepath,
            path,
            naming_rule,
            failed_folder,
            self.Ui.radioButton_11.isChecked(),
            self.Ui.radioButton_3.isChecked(),
            self.Ui.lineEdit_4.text().split("|"),
            self.add_text_main,
            self.moveFailedFolder,
        )

    # ========================================================================有码片裁剪封面
    def cutImage(self, imagecut, path, naming_rule):
        if imagecut != 3:
            thumb_name = naming_rule + "-thumb.jpg"
            poster_name = naming_rule + "-poster.jpg"
            thumb_path = path + "/" + thumb_name
            poster_path = path + "/" + poster_name
            if os.path.exists(poster_path):
                self.add_text_main("[+]Poster Existed!    " + poster_name)
                return
            success = cut_poster(thumb_path, poster_path, imagecut)
            if success:
                self.add_text_main("[+]Poster Cut!        " + poster_name)
            else:
                self.add_text_main("[-]Thumb cut failed!")

    def fix_size(self, path, naming_rule):
        self.fs_service.fix_size(path, naming_rule, self.add_text_main)

    # ========================================================================加水印
    def add_mark(self, poster_path, thumb_path, cn_sub, leak, uncensored, config):
        mark_type = ""
        if self.Ui.checkBox_5.isChecked() and cn_sub:
            mark_type += ",字幕"
        if self.Ui.checkBox_6.isChecked() and leak:
            mark_type += ",流出"
        if self.Ui.checkBox_7.isChecked() and uncensored:
            mark_type += ",无码"
        if (
            self.Ui.radioButton_17.isChecked()
            and mark_type != ""
            and self.Ui.checkBox_4.isChecked()
            and os.path.exists(thumb_path)
        ):
            mark_pos = config["mark"]["mark_pos"]
            mark_size = int(config["mark"]["mark_size"])
            marks = {"cn_sub": cn_sub == 1, "leak": leak == 1, "uncensored": uncensored == 1}
            add_watermark(thumb_path, mark_size, mark_pos, marks)
            self.add_text_main("[+]Thumb Add Mark:    " + mark_type.strip(","))
        if (
            self.Ui.radioButton_15.isChecked()
            and mark_type != ""
            and self.Ui.checkBox_2.isChecked()
            and os.path.exists(poster_path)
        ):
            mark_pos = config["mark"]["mark_pos"]
            mark_size = int(config["mark"]["mark_size"])
            marks = {"cn_sub": cn_sub == 1, "leak": leak == 1, "uncensored": uncensored == 1}
            add_watermark(poster_path, mark_size, mark_pos, marks)
            self.add_text_main("[+]Poster Add Mark:   " + mark_type.strip(","))

    # ========================================================================获取分集序号
    def get_part(self, filepath, failed_folder):
        return self.fs_service.get_part(filepath)

    # ========================================================================更新进度条
    def set_processbar(self, value):
        self.Ui.progressBar_avdc.setProperty("value", value)
        self.Ui.label_percent.setText(str(value) + "%")

    def add_success_item(self, count_claw, count, movie_number, suffix):
        node = QTreeWidgetItem(self.item_succ)
        node.setText(0, str(count_claw) + "-" + str(count) + "." + movie_number + suffix)
        self.item_succ.addChild(node)

    def add_exception_item(self, count_claw, count, filepath, error_info):
        node = QTreeWidgetItem(self.item_fail)
        node.setText(
            0,
            str(count_claw)
            + "-"
            + str(count)
            + "."
            + os.path.splitext(filepath.split("/")[-1])[0],
        )
        self.item_fail.addChild(node)

    # ========================================================================输出调试信息
    def debug_mode(self, json_data):
        try:
            self.add_text_main("[+] ---Debug info---")
            for key, value in json_data.items():
                if value == "" or key == "actor_photo" or key == "extrafanart":
                    continue
                if key == "tag" and len(value) == 0:
                    continue
                elif key == "tag":
                    value = str(json_data["tag"]).strip(" ['']").replace("'", "")
                self.add_text_main("   [+]-" + "%-13s" % key + ": " + str(value))
            self.add_text_main("[+] ---Debug info---")
        except Exception as error_info:
            self.add_text_main("[-]Error in debug_mode: " + str(error_info))

    # ========================================================================创建输出文件夹
    def creatFolder(self, success_folder, json_data, config):
        return self.fs_service.create_folder(success_folder, json_data, config)

    # ========================================================================从指定网站获取json_data
    def get_json_data(self, mode, number, config, appoint_url):
        if mode == 5:  # javdb模式
            self.add_text_main("[!]Please Wait Three Seconds！")
            time.sleep(3)
        json_data = getDataFromJSON(number, config, mode, appoint_url)
        return json_data

    # ========================================================================json_data添加到主界面
    def add_label_info(self, json_data):
        try:
            t = threading.Thread(target=self.add_label_info_Thread, args=(json_data,))
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main(
                "[-]Error in pushButton_start_cap_clicked: " + str(error_info)
            )

    def add_label_info_Thread(self, json_data):
        self.Ui.lineEdit_SerialNumber.setText(json_data["number"])
        self.Ui.lineEdit_ReleaseDate.setText(json_data["release"])
        self.Ui.lineEdit_Director.setText(json_data["director"])
        self.Ui.lineEdit_Serial.setText(json_data["series"])
        self.Ui.lineEdit_Product.setText(json_data["studio"])
        self.Ui.lineEdit_Release.setText(json_data["publisher"])
        self.Ui.lineEdit_Title.setText(json_data["title"])
        self.Ui.lineEdit_Actor.setText(json_data["actor"])
        self.Ui.lineEdit_Intra.setText(json_data["outline"])
        self.Ui.lineEdit_Type.setText(
            str(json_data["tag"]).strip(" [',']").replace("'", "")
        )
        # if self.Ui.checkBox_cover.isChecked(): # No simple check box, always show if exists
        poster_path = json_data["poster_path"]
        thumb_path = json_data["thumb_path"]
        if os.path.exists(poster_path):
            pix = QPixmap(poster_path)
            self.Ui.label_cover.setScaledContents(True)
            self.Ui.label_cover.setPixmap(pix)  # 添加封面图
        if os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            self.Ui.label_thumbnail.setScaledContents(True)
            self.Ui.label_thumbnail.setPixmap(pix)  # 添加缩略图

    # ========================================================================检查更新
    def UpdateCheck(self):
        # 更新检查已禁用
        return "True"

    # ========================================================================新建失败输出文件夹
    def CreatFailedFolder(self, failed_folder):
        if self.Ui.radioButton_11.isChecked() and not os.path.exists(failed_folder):
            try:
                os.makedirs(failed_folder + "/")
                self.add_text_main("[+]Created folder named " + failed_folder + "!")
            except Exception as error_info:
                self.add_text_main("[-]Error in CreatFailedFolder: " + str(error_info))

    # ========================================================================删除空目录
    def CEF(self, path):
        self.fs_service.cleanup_empty_dirs(path, self.add_text_main)

    def Core_Main(self, filepath, number, mode, count, appoint_url=""):
        config_file = "config.ini"
        Config = ConfigParser()
        Config.read(config_file, encoding="UTF-8")
        movie_path = self.Ui.lineEdit_7.text()
        if movie_path == "":
            movie_path = os.getcwd().replace("\\", "/")
        failed_folder = movie_path + "/" + self.Ui.lineEdit_9.text()
        success_folder = movie_path + "/" + self.Ui.lineEdit_8.text()
        deps = FileProcessDependencies(
            log=self.add_text_main,
            debug=self.debug_mode,
            get_json_data=self.get_json_data,
            create_folder=self.creatFolder,
            get_part=self.get_part,
            get_naming_rule=self.get_naming_rule,
            move_failed_folder=self.moveFailedFolder,
            thumb_download=self.thumbDownload,
            small_cover_download=self.smallCoverDownload,
            cut_image=self.cutImage,
            fix_size=self.fix_size,
            copy_fanart=self.copyRenameJpgToFanart,
            delete_thumb=self.deletethumb,
            paste_file=self.pasteFileToFolder,
            print_files=self.PrintFiles,
            extrafanart_download=self.extrafanartDownload,
            add_mark=self.add_mark,
            add_label_info=self.add_label_info,
            register_result=self.register_result,
            is_debug_enabled=lambda: self.Ui.radioButton_5.isChecked(),
            is_program_mode_move=lambda: self.Ui.radioButton.isChecked(),
            is_show_small_cover=lambda: self.Ui.checkBox_2.isChecked(),
            is_copy_fanart_enabled=lambda: self.Ui.checkBox_3.isChecked(),
            is_print_enabled=lambda: self.Ui.checkBox.isChecked(),
            is_extrafanart_enabled=lambda: self.Ui.radioButton_13.isChecked(),
            is_restore_imagecut_enabled=lambda: self.Ui.radioButton_27.isChecked(),
        )
        result = self.file_service.process(
            filepath=filepath,
            number=number,
            mode=mode,
            count_claw=self.count_claw,
            count=count,
            config=Config,
            movie_path=movie_path,
            failed_folder=failed_folder,
            success_folder=success_folder,
            appoint_url=appoint_url,
            deps=deps,
        )
        return result

    def register_result(self, count_claw, count, json_data):
        self.json_array[str(count_claw) + "-" + str(count)] = json_data

    def AVDC_Main(self):
        os.chdir(os.getcwd())
        config_file = "config.ini"
        config = ConfigParser()
        config.read(config_file, encoding="UTF-8")
        movie_path = self.Ui.lineEdit_7.text()
        if movie_path == "":
            movie_path = os.getcwd().replace("\\", "/")
        failed_folder = movie_path + "/" + self.Ui.lineEdit_9.text()
        escape_folder = self.Ui.lineEdit_5.text()
        mode = self.Ui.comboBox_2.currentIndex() + 1
        movie_type = self.Ui.lineEdit_6.text()
        escape_string = self.Ui.lineEdit_12.text()

        if self.UpdateCheck() == "ProxyError":
            self.add_text_main("[-]Connect Failed! Please check your Proxy or Network!")
            self.Ui.pushButton_start_cap.setEnabled(True)
            self.add_text_main("[*]======================================================")
            return

        if self.Ui.radioButton_11.isChecked():
            self.CreatFailedFolder(failed_folder)

        callbacks = BatchCallbacks(
            log=self.add_text_main,
            separator=lambda: self.add_text_main("[*]======================================================"),
            set_progress=self.progressBarValue.emit,
            on_success=self.add_success_item,
            on_exception=self.add_exception_item,
            move_failed=self.moveFailedFolder,
        )
        self.batch_service.run(
            count_claw=self.count_claw,
            movie_path=movie_path,
            escape_folder=escape_folder,
            movie_type=movie_type,
            escape_string=escape_string,
            mode=mode,
            failed_folder=failed_folder,
            failed_move_enabled=self.Ui.radioButton_11.isChecked(),
            soft_link_enabled=config["common"]["soft_link"] == "1",
            process_movie=self.Core_Main,
            callbacks=callbacks,
        )
        self.Ui.pushButton_start_cap.setEnabled(True)
        self.CEF(movie_path)
        self.add_text_main("[+]All finished!!!")
        self.add_text_main("[*]======================================================")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = AVDC_Main_UI()
    window.show()
    sys.exit(app.exec_())
