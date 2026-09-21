# docs/tui 目录概览

> tui-go 重构相关文档。主计划见
> [../04-tui-lazygit-refactor.md](../04-tui-lazygit-refactor.md)。

## 索引

| 编号 | 文档 | 类型 | 一句话摘要 |
|------|------|------|-----------|
| d01 | [分阶段详细计划](d01-phase-plan.md) | design | Phase 0-6 每阶段动作、涉及文件与验收 |
| d02 | [lazygit 架构方案](d02-lazygit-architecture.md) | design | lazygit 包结构、核心概念、分层与事件循环 |
| d03 | [lazygit 快捷键体系](d03-lazygit-keybindings.md) | design | lazygit 键位组织逻辑、全局/列表/面板/弹窗键位 |
| d04 | [AVDC 功能划分与面板](d04-avdc-design.md) | design | AVDC 面板布局、Context/Controller/Model 设计 |
| d05 | [AVDC 快捷键设计](d05-avdc-keybindings.md) | design | AVDC 各 context 键位表与现有键位差异 |
| d06 | [操作逻辑重构](d06-interaction-refactor.md) | design | PromptContext 统一输入、键位/反馈闭环、弹窗栈修复 |

## 文档关系

```
d02 lazygit 架构 ──┐
                   ├──→ d04 AVDC 功能/面板设计 ──→ d01 分阶段实施
d03 lazygit 键位 ──┘         │
                             └──→ d05 AVDC 快捷键设计
```

- d02/d03：**lazygit 方案整理**（参考蓝本，只读沉淀）
- d04/d05：**本项目功能设计**（基于方案的应用）
- d06：**交互逻辑重构落地**（PromptContext + 反馈闭环，已实施）
- d01：实施计划（已有，对应 04-tui-lazygit-refactor.md）
