# d03 lazygit 快捷键体系整理

> 提炼 lazygit 官方 Keybindings 全表的组织逻辑与设计
> 原则，作为 AVDC 快捷键设计的参照。

## 1. 组织原则

lazygit 键位按 **context（面板/弹窗）分组**，每组一个
表格（官方 `docs/keybindings/Keybindings_en.md` 由
`pkg/cheatsheet` 从 i18n 字符串自动生成）：

- **Global**：任何 context 都生效的基础键位
- **List panel navigation**：所有列表面板共享（由
  ListController 分配），如 branches/commits/files
- **各面板**：Files / Commits / Local branches / Stash /
  Remotes / Tags / Submodules / Status / Reflog 等
- **主面板变体**：normal / staging / patch building /
  merging，同一 window 不同模式
- **弹窗**：Menu / Confirmation / Input prompt /
  Commit summary，交互高度一致

键位设计三条主线：**全局一致**（esc/q/方向键含义固定）、
**动作首字母 mnemonic**（c=commit、s=stash）、**弹窗
统一**（enter 确认 / esc 取消）。

## 2. 全局键位

| 键 | 动作 | 设计点 |
|----|------|-------|
| `q`, `<ctrl+c>` | 退出 | 双保险 |
| `<esc>` | 取消 / 返回上级 | 唯一返回键 |
| `?` | 打开键位菜单 | 随时可查 |
| `R` | 刷新所有面板 | 大写 = 全局刷新 |
| `z` / `Z` | 撤销 / 重做 | vim 记忆 |
| `+` / `_` | 下一 / 上一屏幕模式 | normal/half/fullscreen |
| `:` | 执行 shell 命令 | 快捷入口 |
| `<ctrl+r>` | 切换最近仓库 | |
| `<pgup>`, `K`, `<ctrl+u>` | 主窗口上滚 | 三种等价键 |
| `<pgdn>`, `J`, `<ctrl+d>` | 主窗口下滚 | 三种等价键 |
| `<ctrl+z>` | 挂起应用 | 回 shell |
| `<alt+shift+c>` | 编辑配置文件 | 外置编辑器 |

要点：**同一动作绑定多个等价键**（方向键 + vim 键 +
ctrl 组合），照顾不同习惯；`?` 提供即席帮助。

## 3. 列表导航键位

所有列表面板（branches/commits/files/tags/stash...）
共享同一套导航，由 ListController 一次注册多处复用：

| 键 | 动作 |
|----|------|
| `,` / `.` | 上一页 / 下一页 |
| `<` / `>`（或 home/end） | 滚动到顶部 / 底部 |
| `v` | 切换范围选择 |
| `<shift+down>` / `<shift+up>` | 范围选择向下 / 向上扩展 |
| `/` | 按文本搜索当前 view |
| `H` / `L` | 水平滚动左 / 右 |
| `]` / `[` | 下一个 / 上一个 tab |
| `<enter>` | 执行选中项（各面板定义自己的动作） |

> 注：上下移动（`j`/`k`、方向键）由 gocui 层处理，
> 未列入此表；列表面板的移动/选中是统一行为。

## 4. 面板键位的 mnemonic 逻辑

Files 面板（节选）：

| 键 | 动作 | 记忆 |
|----|------|------|
| `c` | Commit | c=commit |
| `s` | Stash | s=stash |
| `a` | Stage all | a=all |
| `d` | Discard | d=discard |
| `e` / `o` | 外部编辑器 / 默认应用打开 | e/o |
| `f` / `i` / `r` | Fetch / Ignore / Refresh | 首字母 |
| `space` | Stage 选中项 | 空格 = 标记 |
| `C` | Commit（用 git 编辑器） | 大写 = 变体 |
| `S` | View stash options | 大写 = 二级菜单 |

Commits 面板（节选）：

| 键 | 动作 |
|----|------|
| `s` / `f` / `r` | Squash / Fixup / Reword |
| `d` / `e` / `p` | Drop / Edit / Pick |
| `t` / `g` / `T` | Revert / Reset / Tag |
| `C` / `V` | Copy（cherry-pick）/ Paste |
| `<ctrl+j>` / `<ctrl+k>` | 提交下移 / 上移 |

设计模式：

- **小写 = 常用动作首字母**；大写 = 变体/二级菜单
- 大小写区分不同动作（`c` commit vs `C` copy）
- 跨面板保持**同键同语义**（`d` 都是 delete/discard 类、
  `e` 都是 edit、`o` 都是 open、`g` 都是 reset/Go）

## 5. 弹窗键位的一致性

| 弹窗 | 键位 |
|------|------|
| Menu | `enter` 执行 / `esc` 取消 / `/` 过滤 |
| Confirmation | `enter` 确认 / `esc` 取消 / `<ctrl+o>` 复制 |
| Input prompt | `enter` 确认 / `esc` 取消 |
| Commit summary | `enter` 确认 / `esc` 关闭 |

所有弹窗：**enter 确认、esc 取消**，零学习成本；
menu 支持 `/` 过滤，大菜单可搜。

## 6. 可配置与可发现性

- **用户可覆盖全部键位**：Config 的 `keybinding` 节，
  默认值合并用户配置（分层覆盖）
- **`?` 键位菜单**：按 context 展示当前可用键位，
  自动生成、多语言
- **options bar**：底部常驻显示当前 context 的关键键位
  提示（可开关）
- 键位表从 i18n 字符串生成，文档与实现不脱节

## 7. 设计启示

1. **先定全局与列表导航**，再为每个面板补专属键位——
   大部分操作共享基础键位，面板键位量小且好记
2. **mnemonic 优先**：功能键用动作首字母，大小写做
   变体；避免无意义键位
3. **弹窗交互统一**：enter/esc 全应用一致
4. **多等价键**：方向键 + vim 键并存
5. **`?` 可发现性**：用户永远能查到当前 context 的键位
6. **同键同语义跨面板**：d/e/o/g 等在不同面板含义一致，
   迁移成本低
