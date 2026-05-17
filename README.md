# 🏛️ Memory Forge — AI 记忆锻造系统

> "文件系统即宫殿，目录即房间，索引即路径，检索即回忆。"

Memory Forge 是一个为 AI Agent 设计的全方位记忆管理系统，融合五大核心能力，让 AI 在持续开发过程中拥有可追溯、可检索、可维护的长期记忆。

## ✨ 核心特性

| 模块 | 功能 | 说明 |
|------|------|------|
| 📝 Dev Chronicle | 开发编年史 | 实时记录工作痕迹、问题和解决方案 |
| 🏛️ Memory Palace | 记忆宫殿 | 基于文件系统的空间记忆结构 |
| 🔍 Index Engine | 索引引擎 | B+树索引 + 倒排索引，高效检索 |
| 📦 Git Chronicler | Git 纪事官 | 自动生成中文 commit message + CHANGELOG |
| 🧹 Memory Janitor | 记忆管家 | 定期清理冗余、合并重复、归档过时信息 |

## 🚀 快速开始

### 1. 初始化记忆宫殿

```bash
python scripts/memory_index.py init --palace-root ./memory-forge
```

这将创建完整的宫殿目录结构：

```
memory-forge/
├── palace.json                # 宫殿元数据
├── chronicle/                 # 📝 开发编年史
│   ├── YYYY-MM-DD.md         # 每日工作记录
│   └── incidents/            # 事故与问题记录
├── palace/                    # 🏛️ 记忆宫殿房间
│   ├── projects/             # 项目房间
│   ├── patterns/             # 模式房间
│   ├── solutions/            # 解决方案房间
│   └── knowledge/            # 通用知识房间
├── index/                     # 🔍 索引引擎
│   ├── catalog.json          # 全文目录（B+树结构）
│   ├── inverted.json         # 倒排索引
│   └── tags.json             # 标签索引
└── changelog/                 # 📦 变更日志
    └── CHANGELOG.md
```

### 2. 更新索引

```bash
python scripts/memory_index.py update --palace-root ./memory-forge
```

扫描所有 Markdown 文件，构建三层索引。

### 3. 检索记忆

```bash
# 关键词搜索
python scripts/memory_index.py search --palace-root ./memory-forge --query "认证 bug"

# 标签搜索
python scripts/memory_index.py search --palace-root ./memory-forge --tags "安全,性能"

# 时间范围
python scripts/memory_index.py search --palace-root ./memory-forge --query "修复" --from 2026-01-01 --to 2026-05-17
```

### 4. Git 纪事

```bash
# 生成中文 commit message（不提交）
python scripts/git_chronicler.py generate --repo /path/to/repo

# 自动提交 + 更新 CHANGELOG
python scripts/git_chronicler.py commit --repo /path/to/repo --auto-changelog
```

自动生成的 commit message 格式：

```
feat(认证): 新增 jwt.py: 实现token生成与验证; auth.py: 请求拦截

- 新增 auth/jwt.py
- 新增 middleware/auth.py
- 修改 routes/api.py
```

### 5. 记忆管家

```bash
# 查看清理建议
python scripts/memory_janitor.py suggest --palace-root ./memory-forge

# 预览清理（不实际执行）
python scripts/memory_janitor.py clean --palace-root ./memory-forge --dry-run

# 执行清理
python scripts/memory_janitor.py clean --palace-root ./memory-forge --days 90

# 查看统计
python scripts/memory_janitor.py stats --palace-root ./memory-forge
```

## 📝 记录格式

### 编年史 (chronicle/YYYY-MM-DD.md)

```markdown
## [14:30] feat: 实现用户认证模块

**背景**: 项目需要 JWT 认证保护 API 端点
**做了什么**:
- 新增 auth/jwt.py 实现令牌生成与验证
- 新增 middleware/auth.py 实现请求拦截

**问题与解决**:
- token 过期时间过短 → 调整为 24 小时 + 刷新机制

**影响范围**: auth/, middleware/
**关联标签**: #认证 #JWT #安全
```

### 事故报告 (chronicle/incidents/INC-NNNN.md)

```markdown
# INC-0001: 生产环境数据库连接池耗尽

> 严重程度: P1 | 状态: 已解决 | 时间: 2026-05-17 14:30

## 现象
- API 响应时间飙升至 30s+
- 大量 503 错误

## 根因
- 批量导出功能未释放数据库连接

## 修复
1. 紧急：重启应用释放连接
2. 修复连接泄漏

## 预防
- 添加连接池监控告警
```

## 🔍 索引架构

Memory Forge 使用三层索引实现高效检索：

```
用户查询: "查找上周关于认证 bug 的记录"
              ↓
   ┌──────────────────────────┐
   │ 1. 解析查询              │
   │   关键词: ["认证", "bug"] │
   │   时间: 上周              │
   └──────────┬───────────────┘
              ↓
   ┌──────────────────────────┐
   │ 2. 倒排索引检索           │
   │   "认证" → {7,15,33}     │
   │   "bug"  → {3,7,15,42}   │
   │   AND: {7,15}            │
   └──────────┬───────────────┘
              ↓
   ┌──────────────────────────┐
   │ 3. 时间范围过滤           │
   │   {7,15} ∩ 上周范围       │
   │   → {15}                 │
   └──────────┬───────────────┘
              ↓
   ┌──────────────────────────┐
   │ 4. 按相关度+时间排序返回  │
   └──────────────────────────┘
```

详细算法说明见 [references/index_algorithms.md](references/index_algorithms.md)。

## 🏛️ 设计哲学

1. **记录即回忆** — 不记录的终将遗忘，每条记录都是未来自己的线索
2. **结构即记忆** — 宫殿的房间结构本身就是记忆的骨架
3. **索引即速度** — 高效检索让记忆在需要时可以被召回
4. **清理即保鲜** — 冗余的记忆是噪音，定期清理保持清晰度
5. **留痕即责任** — AI 的工作痕迹是可追溯的，对人类负责

## 📋 技术特性

- **零外部依赖** — 纯 Python 标准库实现，兼容 Python 3.6+
- **跨平台** — 支持 Windows / macOS / Linux
- **UTF-8 全链路** — 文件读写、索引、搜索均使用 UTF-8 编码
- **增量索引** — 每次更新只扫描变更文件
- **中文友好** — commit message、CHANGELOG、搜索均原生支持中文

## 📁 项目结构

```
memory-forge/
├── SKILL.md                          # 技能定义文件（OpenClaw skill 规范）
├── scripts/
│   ├── memory_index.py               # 索引引擎（B+树 + 倒排索引 + 标签索引）
│   ├── git_chronicler.py             # Git 纪事官（中文 commit + CHANGELOG）
│   └── memory_janitor.py             # 记忆管家（清理/归档/统计）
├── references/
│   ├── index_algorithms.md           # 索引算法详解
│   └── palace_structure.md           # 宫殿结构规范
└── templates/                        # 模板文件（预留）
```

## License

MIT
