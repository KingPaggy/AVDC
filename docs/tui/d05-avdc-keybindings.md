# d05 AVDC TUI 快捷键设计

> 继承 lazygit 键位逻辑（全局一致 / mnemonic / 弹窗统
> 一），为 AVDC 各 context 设计键位表。标注与现有
> TUI 的差异，供迁移参考。

## 1. 设计原则

继承 d03 的 lazygit 键位逻辑，结合 AVDC 场景：

1. **全局键位恒定**：esc/q/?/R 在任何 context 含义一致
2. **mnemonic 优先**：功能键用动作首字母
   （s=scrape、o=organize、c=config、r=refresh）
3. **弹窗统一**：enter 确认 / esc 取消
4. **多等价键**：方向键 + vim 键（j/k）并存
5. **列表共享导航**：ListController 一套键位
6. **`?` 可发现**：随时查看当前 context 键位
7. **破坏性操作双确认**：organize 会移动文件，
   必须经 Confirmation 弹窗

## 2. 全局键位

所有 context 生效（GlobalController 注册）：

| 键 | 动作 | 说明 |
|----|------|------|
| `q`, `<ctrl+c>` | 退出 | 双保险 |
| `<esc>` | 取消 / 返回 | 弹栈回 files |
| `?` | 键位帮助 | HelpContext |
| `R` | 刷新扫描 | 重新 scan 当前目录 |
| `+` / `_` | 屏幕模式 | normal/half/fullscreen |
| `: ` | 执行 shell 命令 | 可选（lazygit 同款） |
| `<ctrl+z>` | 挂起应用 | 回 shell |

## 3. 列表导航键位

files / result / menu / config 共享（ListController）：

| 键 | 动作 |
|----|------|
| `j`, `<down>` / `k`, `<up>` | 下 / 上移动一行 |
| `g` / `G` | 滚动到顶部 / 底部 |
| `,` / `.` | 上一页 / 下一页 |
| `<pgup>` / `<pgdn>` | 上 / 下翻页 |
| `/` | 搜索过滤（Phase 6） |
| `v` | 范围选择（Phase 6） |
| `<enter>` | 执行选中项 |

## 4. 各 Context 键位表

### files（核心）

| 键 | 动作 | mnemonic |
|----|------|---------|
| `<enter>` | 弹菜单：Scrape / Organize | |
| `s` | 直接刮削（跳过菜单） | s=scrape |
| `o` | 直接整理（先弹确认） | o=organize |
| `r` | 刷新扫描 | r=refresh |
| `space` | 标记 / 取消多选 | 空格=标记 |
| `a` | 全选 / 取消全选 | a=all |
| `c` | 打开配置编辑 | c=config |
| `x` | 取消当前刮削任务 | x=cancel |
| `d` | 删除选中文件（弹确认） | d=delete |
| `h` / `l` | 焦点切换（左/右面板） | |

### log（主区域）

| 键 | 动作 |
|----|------|
| `]` / `[` | 切到 result / 上一 tab |
| `j` / `k` | 滚动 |
| `g` / `G` | 顶部 / 底部（含自动跟随） |
| `/` | 搜索日志 |
| `x` | 取消当前任务 |

### result（主区域）

| 键 | 动作 |
|----|------|
| `]` / `[` | 切到 log / 上一 tab |
| `t` | 循环过滤：全部 / 成功 / 失败 | t=tab |
| `<enter>` | 查看选中项详情（文件名/原因） |
| `j` / `k` | 移动 |

### config

| 键 | 动作 |
|----|------|
| `j` / `k` | 字段导航 |
| `<enter>` | 编辑当前字段（inline prompt） |
| `s` | 保存 config.ini 并关闭 | s=save |
| `<esc>` | 放弃并关闭 |

### menu

| 键 | 动作 |
|----|------|
| `j` / `k` | 移动选项 |
| `<enter>` | 确认选中 |
| `/` | 过滤选项 |
| `<esc>`, `q` | 取消 |

### confirm

| 键 | 动作 |
|----|------|
| `y` / `n` | 是 / 否 |
| `<enter>` | 确认默认项 |
| `<esc>` | 取消 |

### prompt（目录路径输入）

| 键 | 动作 |
|----|------|
| `<enter>` | 确认输入 |
| `<esc>` | 取消 |
| `<ctrl+u>` | 清空行 |

### help

| 键 | 动作 |
|----|------|
| `<tab>`, `]` / `[` | 切换键位分类 |
| `j` / `k` | 滚动 |
| `<esc>`, `q`, `<enter>` | 关闭 |

## 5. 弹窗键位

统一约定：

- 所有弹窗：`<enter>` 确认 / `<esc>` 取消
- menu 额外 `j`/`k` + `/`；confirm 额外 `y`/`n`
- 弹窗打开时全局键（q/?/R）暂时失效，esc 优先弹栈
  ——与 lazygit 行为一致

## 6. 键位冲突检查

| 冲突项 | 处理 |
|--------|------|
| `c`：files 里是 config，lazygit commits 里是
  checkout | AVDC 无 commits 面板，无实际冲突；
  跨面板语义在 AVDC 内保持 d/e/o 类一致即可 |
| `s`：files 里是 scrape | 与 lazygit 的 stash 无关，
  AVDC 场景无冲突 |
| `x`：files/log 里是取消 | 全局语义：x=取消任务 |
| `?` 与 `shift+/` | 终端需确认 `?` 可输入（现状
  已用 `?` 绑定帮助，无问题） |
| `+`/`_` 与 `=`/`-` | `=` 保留（展开），`-` 保留
  （收起）；屏幕模式用 `+`/`_` |

结论：现有键位无硬冲突；新增面板键位时对照本表。

## 7. 与现有 TUI 的差异

| 现有键位 | 新设计 | 说明 |
|---------|--------|------|
| `Enter`（files）直接弹菜单 | 不变 | 弹菜单行为保留 |
| `h`/`l` 面板切换 | 不变 | 保留 |
| `r` 刷新 | 不变 | 保留 |
| `c` 配置编辑 | 不变 | 保留 |
| `?` 帮助 | 不变 | 保留，改绑 HelpContext |
| 无 `s`/`o` 直达键 | 新增 `s`/`o` | 跳过菜单快速操作 |
| 无 `x` 取消 | 新增 `x` | Phase 5 引入 |
| 无 `space` 多选 | 新增 `space`/`a` | Phase 6 引入 |
| log/result 并排 | 改为 Tab 切换 | 布局重构（Phase 3） |
| 菜单键位散绑各 view | 统一 ListController | 架构重构（Phase 2）
  |

迁移原则：**现有单键语义全部保留**，只新增键位与
重构注册方式，用户上手成本为零。
