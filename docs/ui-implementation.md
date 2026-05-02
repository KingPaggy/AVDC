# UI 实现技术与逻辑

本文档描述 AVDC 用户界面的实现技术、组件结构、事件绑定、配置管理和图像处理集成。

## 技术栈

### PyQt5 + Qt Designer

UI 开发流程：
1. 在 Qt Designer 中编辑 `Ui/AVDC_new.ui`（121KB）
2. 通过 `pyuic5` 编译为 `Ui/AVDC_new.py`（~900 行 Python 代码）
3. 运行时加载编译后的 UI 类

```python
from Ui.AVDC_new import Ui_MainWindow

class AVDC_Main_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Ui = Ui_MainWindow()      # 组合式：包含 Ui_MainWindow 实例
        self.Ui.setupUi(self)           # 配置 QMainWindow
```

`Ui_MainWindow` 是普通 Python 对象（非 Qt widget），`setupUi()` 方法在其接收的 `MainWindow` 上创建和布局所有子控件。

## UI 组件结构

### 5 个主 Tab

| Tab 索引 | 名称 | 功能 |
|----------|------|------|
| 0 | 主页 (`tab_main`) | 刮削结果树 + 信息面板 + 海报/缩略图预览 + 进度条 + 开始按钮 |
| 1 | 日志 (`tab_log`) | QTextBrowser 实时日志显示 |
| 2 | 工具 (`tab_tool`) | 文件移动、单文件刮削、Emby 演员头像、封面裁剪 |
| 3 | 设置 (`tab_setting`) | 嵌套 QTabWidget，4 个子 Tab（普通设置 / 目录设置 / 水印设置 / 其他设置） |
| 4 | 关于 (`tab_about`) | QTextBrowser 渲染 HTML 文档 |

### 设置子 Tab

| 子 Tab | 内容 |
|--------|------|
| 普通设置 | RadioButton 选择主模式（刮削/整理）、软链接、失败文件移动 |
| 目录设置 | LineEdit 配置文件夹命名规则、媒体路径、输出目录 |
| 水印设置 | RadioButton 启用水印、CheckBox 选择类型（SUB/LEAK/UNCENSORED）、位置选择、Slider 控制大小 |
| 其他设置 | 代理配置（HTTP/SOCKS5）、超时/重试 Slider、排除设置、Emby 地址/API Key |

### 动态控件

以下控件在运行时动态创建（不在 Qt Designer .ui 文件中）：

| 控件 | 创建位置 | 说明 |
|------|----------|------|
| `pushButton_start_cap` | `Init_Ui()` | "开始刮削"按钮，最小高度 40px |
| `progressBar_avdc` | `Init_Ui()` | 进度条，最小高度 40px |
| `treeWidget_number` | `Init_Ui()` | 替换原有 QListView，用于显示成功/失败结果树 |

### 结果树

`QTreeWidget` 替换了 Designer 中的 `QListView`，结构为两级树：

```
刮削结果
├── 成功
│   ├── 1-SSIS-123
│   ├── 1-ABP-456-C
│   └── ...
└── 失败
    ├── 2-unknown_movie
    └── ...
```

点击子节点时，右侧信息面板显示该影片的元数据（番号、标题、演员、导演、日期等）。

### 快捷键

`Init_Ui()` 中配置了 5 个快捷键：

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+1` | 切换到主页 |
| `Ctrl+2` | 切换到日志 |
| `Ctrl+3` | 切换到工具 |
| `Ctrl+4` | 切换到设置 |
| `Ctrl+5` | 切换到关于 |

## 事件绑定

`Init()` 方法（第 244-263 行）绑定了 12 个信号-槽连接：

| 信号源 | 槽函数 | 功能 |
|--------|--------|------|
| `treeWidget_number.clicked` | `treeWidget_number_clicked` | 点击结果节点显示详情 |
| `pushButton_ChooseFile.clicked` | `pushButton_select_file_clicked` | 选择单文件 |
| `pushButton_start_cap.clicked` | `pushButton_start_cap_clicked` | 开始批量刮削 |
| `pushButton.clicked` | `pushButton_save_config_clicked` | 保存配置 |
| `pushButton_2.clicked` | `pushButton_init_config_clicked` | 恢复默认配置 |
| `pushButton_StartMove.clicked` | `move_file` | 手动移动文件 |
| `pushButton_AddAvatar.clicked` | `pushButton_add_actor_pic_clicked` | 添加演员头像 |
| `pushButton_Check.clicked` | `pushButton_show_pic_actor_clicked` | 检查演员头像 |
| `pushButton_6.clicked` | `pushButton_select_thumb_clicked` | 选择缩略图 |
| `pushButton_StartScrap.clicked` | `pushButton_start_single_file_clicked` | 开始单文件刮削 |
| `horizontalSlider_2.valueChanged` | `lcdNumber_timeout_change` | 更新超时 LCD 显示 |
| `horizontalSlider_3.valueChanged` | `lcdNumber_retry_change` | 更新重试 LCD 显示 |
| `horizontalSlider.valueChanged` | `lcdNumber_mark_size_change` | 更新水印大小 LCD 显示 |

## 配置加载/保存逻辑

### 加载：`Load_Config()`

从 `config.ini` 读取 → 批量更新 UI 控件：

```python
def Load_Config(self):
    config = ConfigParser()
    config.read("config.ini", encoding="UTF-8")

    # RadioButton 状态
    if int(config["common"]["main_mode"]) == 1:
        self.Ui.radioButton.setChecked(True)
    elif int(config["common"]["main_mode"]) == 2:
        self.Ui.radioButton_2.setChecked(True)

    # LineEdit 文本
    self.Ui.lineEdit_8.setText(config["common"]["success_output_folder"])

    # Slider 值
    self.Ui.horizontalSlider_2.setValue(int(config["proxy"]["timeout"]))

    # ... 遍历全部 17 个 section
```

### 保存：`save_config_clicked()`

读取 UI 控件状态 → 构建 JSON dict → 调用 `save_config()` 写回 `config.ini`：

```python
def save_config_clicked(self):
    json_config = {
        "main_mode": main_mode,          # 来自 RadioButton
        "soft_link": soft_link,
        "proxy": self.Ui.lineEdit_14.text(),  # 来自 LineEdit
        "timeout": self.Ui.horizontalSlider_2.value(),  # 来自 Slider
        "mark_type": ",".join(filter(None, [
            "SUB" if self.Ui.checkBox_5.isChecked() else "",
            "LEAK" if self.Ui.checkBox_6.isChecked() else "",
            "UNCENSORED" if self.Ui.checkBox_7.isChecked() else "",
        ])),
        # ... 30+ 个字段
    }
    save_config(json_config)  # core/_config/config_io.py
```

### 17 个 config.ini Section 映射

| Section | 包含字段 | UI 控件类型 |
|---------|----------|-------------|
| common | main_mode, soft_link, failed_file_move, website, success/failed_output_folder | RadioButton, LineEdit, ComboBox |
| proxy | type, proxy, timeout, retry | RadioButton, LineEdit, Slider |
| Name_Rule | folder_name, naming_media, naming_file | LineEdit |
| update | update_check | RadioButton |
| log | save_log | RadioButton |
| media | media_type, sub_type, media_path | LineEdit |
| escape | literals, folders, string | LineEdit |
| debug_mode | switch | RadioButton |
| emby | emby_url, api_key | LineEdit |
| mark | poster_mark, thumb_mark, mark_size, mark_type, mark_pos | RadioButton, CheckBox, Slider |
| uncensored | uncensored_poster, uncensored_prefix | RadioButton, LineEdit |
| file_download | nfo, poster, fanart, thumb | CheckBox |
| extrafanart | extrafanart_download, extrafanart_folder | RadioButton, LineEdit |
| baidu | app_id, api_key, secret_key | 隐藏字段（不在 UI 中编辑） |

## 日志系统

### QTimer 轮询机制

```python
LOG_POLL_INTERVAL_MS = 200

def setup_logger(self):
    self.logger = avdc_logger  # core._config.logger 的 logger
    self._log_file_path = get_log_file_path()
    self._log_file_offset = 0

    self._log_poll_timer = QTimer(self)
    self._log_poll_timer.timeout.connect(self._poll_log_file)
    self._log_poll_timer.start(LOG_POLL_INTERVAL_MS)
```

UI 不直接接收日志流，而是通过 `QTimer` 每 200ms 读取日志文件新增内容，追加到 `textBrowser_log` 显示区。这种方式避免了跨线程写入 Qt 控件的问题。

### 日志文件管理

- 自动清理：保留最新 100 个日志文件，超出自动删除
- 文件命名：`Log/app_YYYYMMDD.log`

## 图像处理集成

### 海报裁剪 — Baidu AI 人脸检测

```python
def image_cut(self, path, file_name, mode=1):
    config = self._get_app_config()
    image_ops_crop(
        path, file_name, mode=mode,
        app_id=config.baidu_app_id,
        api_key=config.baidu_api_key,
        secret_key=config.baidu_secret_key,
    )
```

`crop_by_face_detection` 函数调用 Baidu AIP 的 `AipBodyAnalysis` 服务检测人脸位置，智能裁剪海报。如果未配置 Baidu 凭证，则退化为默认裁剪模式。

### 水印系统

3 种水印类型 × 4 个位置 × 2 层叠加：

| 维度 | 选项 |
|------|------|
| 类型 | SUB（字幕）、LEAK（流出）、UNCENSORED（无码） |
| 位置 | top_left、bottom_left、top_right、bottom_right |
| 目标层 | poster（封面海报）、thumb（缩略图） |

水印资源位于 `resources/icons/` 目录（SUB.png / LEAK.png / UNCENSORED.png）。

## 工具 Tab 功能

| 按钮 | 功能 | 说明 |
|------|------|------|
| 移动文件 | `move_file()` | 手动将视频文件按命名规则移动到输出目录 |
| 单文件刮削 | `pushButton_start_single_file_clicked()` | 指定文件路径 + 番号 + 目标网站进行单文件处理 |
| Emby 演员头像 | `pushButton_add_actor_pic_clicked()` | 连接 Emby API 上传演员头像 |
| 封面裁剪 | `pushButton_show_pic_actor_clicked()` | 使用 Baidu AI 智能裁剪封面 |

## 启动流程

```
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AVDC_Main_UI()          # 初始化
    window.show()
    sys.exit(app.exec_())

AVDC_Main_UI.__init__():
    self.Ui.setupUi(self)            # 1. Qt Designer 布局
    self.setup_logger()              # 2. 日志系统（QTimer 轮询）
    self.Init_Ui()                   # 3. 动态控件 + 快捷键
    self.Init()                      # 4. 事件绑定
    self.Load_Config()               # 5. 加载配置
    self.show_version()              # 6. 显示版本号
```

## 资源文件

```
resources/
├── icons/
│   ├── AVDC-ico.png          # 窗口图标（47KB）
│   ├── AVDC.ico              # Windows 图标（1.1MB）
│   ├── SUB.png               # 字幕水印
│   ├── LEAK.png              # 流出水印
│   ├── UNCENSORED.png        # 无码水印
│   ├── about.png             # 关于页图片
│   └── emby.png              # Emby 集成说明
├── watermarks/               # 水印素材
└── screenshots/              # README 截图
```
