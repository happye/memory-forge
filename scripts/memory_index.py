#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Forge — 索引引擎
B+树目录索引 + 倒排索引 + 标签索引
支持 init / update / search 三种操作
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# ─── B+树节点 ───────────────────────────────────────────────

class BPlusTreeNode:
    """B+树节点（内存版，持久化为JSON）"""
    def __init__(self, is_leaf=True):
        self.keys = []        # 排序键（时间戳字符串）
        self.children = []    # 内部节点: 子节点引用; 叶子节点: 记录元数据
        self.is_leaf = is_leaf
        self.next_leaf = None  # 叶子节点链表（范围查询用）

    def to_dict(self):
        d = {"keys": self.keys, "is_leaf": self.is_leaf}
        if self.is_leaf:
            d["children"] = self.children  # 叶子存元数据列表
        else:
            d["children"] = [c.to_dict() if isinstance(c, BPlusTreeNode) else c for c in self.children]
        if self.next_leaf is not None:
            d["next_leaf"] = self.next_leaf
        return d

    @classmethod
    def from_dict(cls, d):
        node = cls(is_leaf=d.get("is_leaf", True))
        node.keys = d["keys"]
        if node.is_leaf:
            node.children = d["children"]
        else:
            node.children = [cls.from_dict(c) for c in d["children"]]
        node.next_leaf = d.get("next_leaf")
        return node


# ─── 索引管理器 ────────────────────────────────────────────

class MemoryIndex:
    """记忆宫殿索引管理器"""

    ORDER = 32  # B+树阶数

    def __init__(self, palace_root):
        self.palace_root = Path(palace_root)
        self.index_dir = self.palace_root / "index"
        self.catalog_path = self.index_dir / "catalog.json"
        self.inverted_path = self.index_dir / "inverted.json"
        self.tags_path = self.index_dir / "tags.json"

        # 索引数据
        self.records = {}        # id -> metadata
        self.inverted = defaultdict(list)  # keyword -> [record_ids]
        self.tags_index = defaultdict(list)  # tag -> [record_ids]
        self.next_id = 1

    def _load(self):
        """从磁盘加载索引"""
        if self.catalog_path.exists():
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.records = data.get("records", {})
                self.next_id = data.get("next_id", 1)

        if self.inverted_path.exists():
            with open(self.inverted_path, "r", encoding="utf-8") as f:
                self.inverted = defaultdict(list, json.load(f))

        if self.tags_path.exists():
            with open(self.tags_path, "r", encoding="utf-8") as f:
                self.tags_index = defaultdict(list, json.load(f))

    def _save(self):
        """持久化索引到磁盘"""
        self.index_dir.mkdir(parents=True, exist_ok=True)

        catalog = {
            "version": 1,
            "updated": datetime.now().isoformat(),
            "next_id": self.next_id,
            "records": self.records,
            # B+树结构在records中已按时间排序，这里存储扁平结构以便快速查询
            "bplus_order": self.ORDER,
        }
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

        with open(self.inverted_path, "w", encoding="utf-8") as f:
            json.dump(dict(self.inverted), f, ensure_ascii=False, indent=2)

        with open(self.tags_path, "w", encoding="utf-8") as f:
            json.dump(dict(self.tags_index), f, ensure_ascii=False, indent=2)

    # ─── 初始化 ─────────────────────────────────────

    def init_palace(self):
        """初始化记忆宫殿目录结构"""
        dirs = [
            "chronicle/incidents",
            "palace/projects",
            "palace/patterns",
            "palace/solutions",
            "palace/knowledge",
            "index",
            "changelog/releases",
        ]
        for d in dirs:
            (self.palace_root / d).mkdir(parents=True, exist_ok=True)

        # 创建palace.json元数据
        meta_path = self.palace_root / "palace.json"
        if not meta_path.exists():
            meta = {
                "name": "Memory Forge Palace",
                "created": datetime.now().isoformat(),
                "version": 1,
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

        # 创建初始CHANGELOG
        cl_path = self.palace_root / "changelog" / "CHANGELOG.md"
        if not cl_path.exists():
            with open(cl_path, "w", encoding="utf-8") as f:
                f.write("# 变更日志\n\n## [Unreleased]\n\n")

        # 创建初始索引
        self._save()
        return {"status": "ok", "message": "记忆宫殿初始化完成", "path": str(self.palace_root)}

    # ─── 扫描并更新索引 ──────────────────────────────

    def update_index(self):
        """扫描所有记录文件，重建索引"""
        self._load()

        # 收集所有markdown文件
        all_md = []
        for pattern in ["chronicle/*.md", "chronicle/incidents/*.md",
                        "palace/**/*.md", "changelog/*.md"]:
            all_md.extend(self.palace_root.glob(pattern))

        new_records = {}
        new_inverted = defaultdict(list)
        new_tags = defaultdict(list)
        rid = self.next_id

        for md_file in all_md:
            rel_path = md_file.relative_to(self.palace_root)
            path_str = str(rel_path).replace("\\", "/")

            # 读取文件内容
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # 提取元数据
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
            title = self._extract_title(content)
            tags = self._extract_tags(content)
            keywords = self._extract_keywords(content)
            category = self._infer_category(path_str)

            record = {
                "id": rid,
                "path": path_str,
                "title": title,
                "mtime": mtime,
                "tags": tags,
                "category": category,
                "size": md_file.stat().st_size,
            }
            new_records[str(rid)] = record

            # 倒排索引
            for kw in keywords:
                new_inverted[kw].append(str(rid))

            # 标签索引
            for tag in tags:
                new_tags[tag].append(str(rid))

            rid += 1

        self.records = new_records
        self.inverted = new_inverted
        self.tags_index = new_tags
        self.next_id = rid
        self._save()

        return {
            "status": "ok",
            "message": f"索引更新完成，共 {len(new_records)} 条记录",
            "records": len(new_records),
            "keywords": len(new_inverted),
            "tags": len(new_tags),
        }

    # ─── 搜索 ───────────────────────────────────────

    def search(self, query, tags=None, from_date=None, to_date=None, mode="and"):
        """
        搜索记忆
        query: 查询关键词（空格分隔，支持AND/OR）
        tags: 标签列表
        from_date/to_date: 时间范围过滤
        mode: "and" | "or"
        """
        self._load()

        if not self.records:
            return {"status": "ok", "results": [], "total": 0, "message": "索引为空，请先运行 update"}

        # 1. 关键词检索
        query_keywords = [kw.lower() for kw in re.split(r'\s+', query.strip()) if kw]
        keyword_hits = defaultdict(int)  # rid -> hit_count

        for kw in query_keywords:
            # 精确匹配 + 前缀匹配
            for idx_kw, rids in self.inverted.items():
                if kw in idx_kw or idx_kw.startswith(kw):
                    for rid in rids:
                        keyword_hits[rid] += 1

        # 2. 标签检索
        tag_hits = defaultdict(int)
        if tags:
            for tag in tags:
                tag_clean = tag.lstrip("#")
                for idx_tag, rids in self.tags_index.items():
                    if tag_clean.lower() in idx_tag.lower():
                        for rid in rids:
                            tag_hits[rid] += 1

        # 3. 合并结果
        candidate_ids = set()
        if query_keywords and tags:
            if mode == "and":
                candidate_ids = set(keyword_hits.keys()) & set(tag_hits.keys())
            else:
                candidate_ids = set(keyword_hits.keys()) | set(tag_hits.keys())
        elif query_keywords:
            candidate_ids = set(keyword_hits.keys())
        elif tags:
            candidate_ids = set(tag_hits.keys())
        else:
            # 无条件搜索：返回所有
            candidate_ids = set(self.records.keys())

        # 4. 时间范围过滤
        results = []
        for rid in candidate_ids:
            rec = self.records.get(rid)
            if not rec:
                continue
            if from_date and rec["mtime"] < from_date:
                continue
            if to_date and rec["mtime"] > to_date:
                continue

            # 计算相关度分数
            score = keyword_hits.get(rid, 0) + tag_hits.get(rid, 0) * 2
            results.append({**rec, "score": score})

        # 5. 按相关度+时间排序
        results.sort(key=lambda x: (x["score"], x["mtime"]), reverse=True)

        return {
            "status": "ok",
            "total": len(results),
            "results": results[:50],  # 最多返回50条
            "query": query,
            "tags": tags,
        }

    # ─── 辅助方法 ───────────────────────────────────

    @staticmethod
    def _extract_title(content):
        """从markdown中提取第一个标题"""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("# ").strip()
        return "(无标题)"

    @staticmethod
    def _extract_tags(content):
        """提取 #标签"""
        return list(set(re.findall(r'#([\w\u4e00-\u9fff]+)', content)))

    @staticmethod
    def _extract_keywords(content, top_n=20):
        """
        提取关键词（基于词频的简单方案）
        过滤停用词，取高频词作为索引词
        """
        # 简单中文分词：按标点和空格切分
        stopwords = set(
            "的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这 "
            "他 她 它 们 那 里 为 什么 怎么 可以 因为 所以 但是 如果 虽然 而且 或者 以及 对于 关于 "
            "the a an is are was were be been being have has had do does did will would shall should "
            "can could may might must need to of in for on with at by from as into through during "
            "before after above below between out off over under again further then once here there "
            "when where why how all each both few more most other some such no nor not only own same "
            "so than too very just because but and or if while this that these those it its "
            "我们 他们 你们 之 中 与 等 被 把 让 给 向 从 往".split()
        )

        # 切词：非字母/非CJK字符分割
        tokens = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', content.lower())
        tokens = [t for t in tokens if t not in stopwords and len(t) >= 2]

        # 词频统计
        freq = defaultdict(int)
        for t in tokens:
            freq[t] += 1

        # 取top N高频词
        sorted_words = sorted(freq.items(), key=lambda x: -x[1])
        return [w for w, c in sorted_words[:top_n]]

    @staticmethod
    def _infer_category(path_str):
        """从路径推断记录类别"""
        if "chronicle/incidents" in path_str:
            return "incident"
        elif "chronicle/" in path_str:
            return "chronicle"
        elif "palace/projects" in path_str:
            return "project"
        elif "palace/patterns" in path_str:
            return "pattern"
        elif "palace/solutions" in path_str:
            return "solution"
        elif "palace/knowledge" in path_str:
            return "knowledge"
        elif "changelog" in path_str:
            return "changelog"
        return "other"


# ─── CLI入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Memory Forge 索引引擎")
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="初始化记忆宫殿")
    p_init.add_argument("--palace-root", required=True, help="宫殿根目录")

    # update
    p_update = sub.add_parser("update", help="更新索引")
    p_update.add_argument("--palace-root", required=True, help="宫殿根目录")

    # search
    p_search = sub.add_parser("search", help="搜索记忆")
    p_search.add_argument("--palace-root", required=True, help="宫殿根目录")
    p_search.add_argument("--query", default="", help="查询关键词")
    p_search.add_argument("--tags", default="", help="标签，逗号分隔")
    p_search.add_argument("--from", dest="from_date", help="起始日期 YYYY-MM-DD")
    p_search.add_argument("--to", dest="to_date", help="结束日期 YYYY-MM-DD")
    p_search.add_argument("--mode", default="and", choices=["and", "or"], help="查询模式")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    idx = MemoryIndex(args.palace_root)

    if args.command == "init":
        result = idx.init_palace()
    elif args.command == "update":
        result = idx.update_index()
    elif args.command == "search":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        result = idx.search(
            query=args.query,
            tags=tags,
            from_date=args.from_date,
            to_date=args.to_date,
            mode=args.mode,
        )
    else:
        result = {"status": "error", "message": f"未知命令: {args.command}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
