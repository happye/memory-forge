---
name: memory-forge
description: |
  AI记忆锻造系统——开发留痕+记忆宫殿+高效检索+Git纪事。让AI在持续开发过程中实时记录工作痕迹、问题和解决方案，用工整格式生成变更日志，自动管理Git提交附带详细中文注释，并通过B+树索引和倒排索引实现高效检索，搭建可快速查找的记忆宫殿。
  触发词：记忆宫殿、记忆锻造、记录工作、留痕、devlog、开发日志、变更记录、changelog、工作记录、记录问题、记录解决方案、AI做了什么、改了什么、新功能记录、版本记录、记忆检索、查找记忆、搜索记忆、memory palace、memory forge、记忆管理、记忆清理、记忆索引。
  当用户要求AI记录它做了什么、追踪开发进展、生成变更说明、管理Git提交信息、检索过往工作记录、或提到"记忆""留痕""工作日志""开发记录"时，必须使用此skill。
metadata:
  openclaw:
    emoji: "🏛️"
---

# 🏛️ Memory Forge — AI记忆锻造系统

> "文件系统即宫殿，目录即房间，索引即路径，检索即回忆。"

Memory Forge 是一个为AI Agent设计的全方位记忆管理系统，融合五大核心能力：

1. **📝 Dev Chronicle** — 实时记录AI工作痕迹、问题和解决方案
2. **🏛️ Memory Palace** — 基于文件系统的空间记忆结构
3. **🔍 Index Engine** — B+树索引 + 倒排索引，高效检索
4. **📦 Git Chronicler** — 自动生成中文commit message + CHANGELOG
5. **🧹 Memory Janitor** — 定期清理冗余、合并重复、归档过时信息

---

## 🏗️ 记忆宫殿结构

Memory Forge 在workspace下维护以下目录结构：

```
workspace/
├── memory-forge/                    # 记忆宫殿根目录
│   ├── palace.json                  # 宫殿元数据（索引根）
│   ├── chronicle/                   # 📝 开发编年史
│   │   ├── YYYY-MM-DD.md           # 每日工作记录
│   │   └── incidents/              # 事故与问题记录
│   │       └── INC-NNNN.md         # 编号化的事故报告
│   ├── palace/                      # 🏛️ 记忆宫殿房间
│   │   ├── projects/               # 项目房间
│   │   │   └── <project>/          # 每个项目一个房间
│   │   │       ├── overview.md     # 项目概览
│   │   │       ├── decisions.md    # 关键决策记录
│   │   │       └── lessons.md      # 经验教训
│   │   ├── patterns/               # 模式房间（设计模式、代码模式）
│   │   ├── solutions/              # 解决方案房间
│   │   └── knowledge/              # 通用知识房间
│   ├── index/                       # 🔍 索引引擎
│   │   ├── catalog.json            # 全文目录（B+树结构）
│   │   ├── inverted.json           # 倒排索引
│   │   └── tags.json               # 标签索引
│   └── changelog/                   # 📦 变更日志
│       ├── CHANGELOG.md            # 主变更日志
│       └── releases/               # 版本发布记录
│           └── vN.N.N.md           # 各版本详细说明
```

---

## 🚀 核心工作流

### 工作流 1：📝 实时记录（Dev Chronicle）

**触发时机**：AI完成一项实质性工作后（修复bug、实现功能、做出决策等）

**执行步骤**：

1. 判断记录类型：
   - `feat` — 新功能实现
   - `fix` — Bug修复
   - `refactor` — 重构
   - `decision` — 关键决策
   - `incident` — 事故/问题
   - `learn` — 经验教训

2. 写入当日编年史 `memory-forge/chronicle/YYYY-MM-DD.md`：
   ```markdown
   ## [HH:MM] 类型: 简述

   **背景**: 为什么做这件事
   **做了什么**: 具体操作和改动
   **问题与解决**: 遇到的问题及解决方案（如有）
   **影响范围**: 改动影响的文件/模块
   **关联标签**: #标签1 #标签2
   ```

3. 如果是 `incident` 类型，额外生成 `memory-forge/chronicle/incidents/INC-NNNN.md`
4. 更新索引（见工作流3）

**记录原则**：
- 每条记录都是独立的、自包含的
- 用工整的格式，让未来的自己（或人类）能快速理解
- 中文注释，清晰易懂
- 不记录无关紧要的琐事，只记录有价值的工作痕迹

---

### 工作流 2：🏛️ 记忆宫殿管理

**触发时机**：用户要求记录/查找/组织知识，或AI判断需要归档重要信息

**房间类型与归档规则**：

| 房间 | 内容 | 归档条件 |
|------|------|---------|
| `projects/<name>/` | 项目级信息 | 跨会话持续工作的项目 |
| `patterns/` | 设计模式、代码模式 | 发现可复用的模式 |
| `solutions/` | 问题和解决方案 | 解决了非平凡问题 |
| `knowledge/` | 通用知识 | 学到新的重要知识 |

**归档格式**（每个文件）：
```markdown
# 标题

> 一句话摘要

## 背景
为什么需要这个知识/决策/方案

## 核心内容
具体内容（代码、方案、推理过程等）

## 关联
- 相关文件: `path/to/file`
- 相关标签: #标签1 #标签2
- 来源: chronicle/YYYY-MM-DD 或 外部链接

## 最后更新
YYYY-MM-DD
```

---

### 工作流 3：🔍 索引引擎

**触发时机**：每次写入新记录后自动更新索引，或用户要求检索时

**索引结构说明**（详见 `references/index_algorithms.md`）：

1. **catalog.json** — B+树结构的目录索引
   - 按时间排序，支持范围查询
   - 叶子节点存储记录路径和元数据摘要

2. **inverted.json** — 倒排索引
   - 关键词 → 记录ID列表的映射
   - 支持布尔查询（AND / OR / NOT）

3. **tags.json** — 标签索引
   - 标签 → 记录ID列表的映射
   - 支持标签组合查询

**检索流程**：
1. 解析用户查询为关键词 + 标签
2. 在倒排索引中查找关键词命中的记录ID集合
3. 在标签索引中查找标签命中的记录ID集合
4. 对两个集合取交集（AND）或并集（OR）
5. 在catalog.json中按时间范围过滤
6. 返回排序后的结果列表

**脚本调用**：
```bash
# 更新索引
python3 "{SKILL_DIR}/scripts/memory_index.py" update --palace-root "<workspace>/memory-forge"

# 检索
python3 "{SKILL_DIR}/scripts/memory_index.py" search --palace-root "<workspace>/memory-forge" --query "查询词" [--tags "标签1,标签2"] [--from "YYYY-MM-DD"] [--to "YYYY-MM-DD"]
```

---

### 工作流 4：📦 Git纪事官

**触发时机**：用户要求提交代码，或在重大变更后建议提交

**执行步骤**：

1. 检查当前Git状态，获取所有变更文件
2. 根据变更内容自动生成commit message：
   ```
   <类型>(<范围>): <中文简述>

   <详细说明>
   - 改动1的具体描述
   - 改动2的具体描述

   关联: chronicle/YYYY-MM-DD#HH:MM
   ```

3. commit类型对照：
   - `feat` → 新功能
   - `fix` → 修复bug
   - `refactor` → 重构（不改功能）
   - `docs` → 文档更新
   - `style` → 代码格式
   - `test` → 测试相关
   - `chore` → 构建/工具
   - `perf` → 性能优化

4. 更新CHANGELOG.md：
   ```markdown
   ## [Unreleased]

   ### 新增
   - 功能描述 (#commit-hash)

   ### 修复
   - 修复描述 (#commit-hash)

   ### 变更
   - 变更描述 (#commit-hash)
   ```

**脚本调用**：
```bash
# 生成commit message
python3 "{SKILL_DIR}/scripts/git_chronicler.py" generate --repo "<repo-path>"

# 执行提交
python3 "{SKILL_DIR}/scripts/git_chronicler.py" commit --repo "<repo-path>" [--auto-changelog]
```

---

### 工作流 5：🧹 记忆管家

**触发时机**：定期（建议每周）或在用户要求时

**执行步骤**：

1. **扫描重复**：检查chronicle和palace中内容重叠的记录
2. **合并关联**：将同一主题的碎片化记录合并为完整文档
3. **归档过时**：将超过90天且无近期引用的记录移入archive
4. **索引重建**：清理后重建索引，保证检索效率
5. **报告**：生成清理报告，列出已合并/归档/删除的内容

**脚本调用**：
```bash
# 执行清理
python3 "{SKILL_DIR}/scripts/memory_janitor.py" clean --palace-root "<workspace>/memory-forge" [--days 90] [--dry-run]

# 查看清理建议
python3 "{SKILL_DIR}/scripts/memory_janitor.py" suggest --palace-root "<workspace>/memory-forge"
```

---

## 📋 快速命令参考

| 命令 | 说明 |
|------|------|
| 记录工作 / 写编年史 | 触发工作流1，记录当前工作 |
| 归档到宫殿 / 记忆归档 | 触发工作流2，将知识归档到宫殿房间 |
| 搜索记忆 / 查找记录 | 触发工作流3，检索过往记录 |
| 提交代码 / git纪事 | 触发工作流4，生成中文commit并更新CHANGELOG |
| 清理记忆 / 记忆管家 | 触发工作流5，清理冗余和过时信息 |
| 记忆宫殿状态 | 查看宫殿整体状态和统计 |

---

## ⚡ 初始化

首次使用时，运行初始化创建宫殿结构：

```bash
python3 "{SKILL_DIR}/scripts/memory_index.py" init --palace-root "<workspace>/memory-forge"
```

这将创建所有必要的目录和初始索引文件。

---

## 🔗 参考文档

- **索引算法详解**：`references/index_algorithms.md` — B+树和倒排索引的实现细节
- **宫殿结构详解**：`references/palace_structure.md` — 记忆宫殿的完整目录规范

---

## 💡 设计哲学

1. **记录即回忆** — 不记录的终将遗忘，每条记录都是未来自己的线索
2. **结构即记忆** — 宫殿的房间结构本身就是记忆的骨架
3. **索引即速度** — 高效检索让记忆在需要时可以被召回
4. **清理即保鲜** — 冗余的记忆是噪音，定期清理保持记忆的清晰度
5. **留痕即责任** — AI的工作痕迹是可追溯的，对人类负责
