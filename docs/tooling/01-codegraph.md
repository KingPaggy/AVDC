# CodeGraph 代码智能工具指南

CodeGraph v0.9.4 是 AVDC 项目的主要代码智能工具。

**保持索引最新**：`codegraph sync .`

## 命令速查

| 需求 | 命令 |
|------|------|
| 查找符号定义 | `codegraph query "SymbolName"` |
| 查找函数调用者 | `codegraph callers "methodName"` |
| 查找函数被调用 | `codegraph callees "methodName"` |
| 评估变更影响 | `codegraph impact "SymbolName"` |
| 收集任务相关文件 | `codegraph context "task description"` |
| 浏览项目结构 | `codegraph files` |
| 检查索引状态 | `codegraph status .` |

## 不应使用 CodeGraph 的场景

| 场景 | 替代方案 |
|------|----------|
| 已知文件路径 | 直接用 `read` |
| 搜索文本/注释 | 用 `grep` |
| 文件模式匹配 | 用 `find` |
| 索引过期 | 先运行 `codegraph sync .` |

## 任务特定技巧

- 修改 `CoreEngine` → 先 `codegraph impact "CoreEngine"` 评估影响范围
- 添加新刮削器 → `codegraph context "add scraper X"` 收集上下文
- 不确定文件位置 → `codegraph files` 查看索引结构
