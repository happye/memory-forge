# 记忆宫殿结构详解

## 完整目录树

```
memory-forge/                         # 宫殿根目录
├── palace.json                       # 宫殿元数据
│
├── chronicle/                        # 📝 开发编年史
│   ├── YYYY-MM-DD.md                # 每日工作记录
│   └── incidents/                   # 事故与问题
│       └── INC-NNNN.md              # 编号化事故报告
│
├── palace/                           # 🏛️ 记忆宫殿房间
│   ├── projects/                    # 项目房间
│   │   └── <project-name>/          # 每个项目一个房间
│   │       ├── overview.md          # 项目概览
│   │       ├── decisions.md         # 关键决策记录（ADR）
│   │       └── lessons.md           # 经验教训
│   │
│   ├── patterns/                    # 模式房间
│   │   ├── design-patterns.md       # 设计模式
│   │   └── code-patterns.md         # 代码模式/惯用法
│   │
│   ├── solutions/                   # 解决方案房间
│   │   └── <problem-slug>.md        # 每个问题一个文件
│   │
│   └── knowledge/                   # 通用知识房间
│       └── <topic-slug>.md          # 每个主题一个文件
│
├── index/                            # 🔍 索引引擎
│   ├── catalog.json                 # 全文目录（B+树结构）
│   ├── inverted.json                # 倒排索引
│   └── tags.json                    # 标签索引
│
├── changelog/                        # 📦 变更日志
│   ├── CHANGELOG.md                 # 主变更日志
│   └── releases/                    # 版本发布记录
│       └── vN.N.N.md                # 各版本详细说明
│
└── archive/                          # 🧹 归档区
    └── (按时间归档的过时记录)
```

---

## palace.json 格式

```json
{
  "name": "Memory Forge Palace",
  "created": "2026-05-17T12:00:00",
  "version": 1,
  "owner": "QClaw",
  "stats": {
    "last_update": "2026-05-17T12:00:00",
    "total_records": 0
  }
}
```

---

## 编年史格式 (chronicle/YYYY-MM-DD.md)

```markdown
# 开发编年史 — YYYY-MM-DD

## [HH:MM] feat: 实现用户认证模块

**背景**: 项目需要JWT认证来保护API端点
**做了什么**:
- 新增 `auth/jwt.py` 实现token生成与验证
- 新增 `middleware/auth.py` 实现请求拦截
- 更新 `routes/api.py` 添加认证装饰器

**问题与解决**:
- token过期时间设置过短导致频繁登出 → 调整为24小时+刷新机制
- 跨域请求携带cookie失败 → 配置CORS允许credentials

**影响范围**: auth/, middleware/, routes/
**关联标签**: #认证 #JWT #安全

---

## [HH:MM] fix: 修复登录页面样式错位

**背景**: 移动端登录按钮被遮挡
**做了什么**: 调整 `components/Login.vue` 的CSS布局
**问题与解决**: flex布局缺少min-height → 添加min-height: 100vh
**影响范围**: components/Login.vue
**关联标签**: #样式 #移动端
```

---

## 事故报告格式 (chronicle/incidents/INC-NNNN.md)

```markdown
# INC-0001: 生产环境数据库连接池耗尽

> 严重程度: P1 | 状态: 已解决 | 时间: YYYY-MM-DD HH:MM

## 现象
- API响应时间飙升至30s+
- 大量503错误
- 数据库连接数达到max_connections上限

## 根因
- 新上线的批量导出功能未释放数据库连接
- 连接池配置过小（max=10，实际需要50+）

## 修复
1. 紧急：重启应用释放连接
2. 修复批量导出的连接泄漏（添加finally块确保释放）
3. 调整连接池参数 max=100

## 预防
- 添加连接池监控告警
- 代码review重点检查资源释放
- 添加连接泄漏检测中间件

## 关联标签**: #数据库 #P1 #连接池 #生产事故
```

---

## 宫殿房间格式 (palace/*/**.md)

```markdown
# [标题]

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

## CHANGELOG 格式 (changelog/CHANGELOG.md)

```markdown
# 变更日志

所有重要变更均记录在此文件中。

## [Unreleased]

### 新增
- 用户认证模块 (JWT) (#abc1234)

### 修复
- 移动端登录按钮样式错位 (#def5678)

### 变更
- 数据库连接池参数调整 (#ghi9012)

## [1.0.0] - 2026-05-17

### 新增
- 初始版本发布
```

---

## 归档规则

- **chronicle/** 中超过90天未更新的 `.md` 文件移入 `archive/`
- 归档文件保留原文件名，加上日期前缀：`archive/2025_Q1_2025-01-15.md`
- 归档操作后自动重建索引
- 归档文件仍可通过索引检索到（但会标记为已归档）
