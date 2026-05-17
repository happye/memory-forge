#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Forge — 记忆管家
定期清理冗余、合并重复、归档过时信息
"""

import json
import os
import re
import sys
import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class MemoryJanitor:
    """记忆管家：清理和维护记忆宫殿"""

    def __init__(self, palace_root, days=90):
        self.palace_root = Path(palace_root)
        self.days = days
        self.archive_dir = self.palace_root / "archive"

    def _read_md(self, path):
        """读取markdown文件"""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _write_md(self, path, content):
        """写入markdown文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _file_age_days(self, path):
        """文件最后修改距今天数"""
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days

    # ─── 建议模式 ────────────────────────────────────

    def suggest(self):
        """分析并给出清理建议，不实际执行"""
        suggestions = []

        # 1. 检查过时记录
        chronicle_dir = self.palace_root / "chronicle"
        if chronicle_dir.exists():
            for md in chronicle_dir.glob("*.md"):
                age = self._file_age_days(md)
                if age > self.days:
                    suggestions.append({
                        "type": "archive",
                        "path": str(md.relative_to(self.palace_root)),
                        "reason": f"超过 {age} 天未更新（阈值 {self.days} 天）",
                        "size": md.stat().st_size,
                    })

        # 2. 检查空文件
        for md in self.palace_root.rglob("*.md"):
            if md.stat().st_size < 10:
                suggestions.append({
                    "type": "empty",
                    "path": str(md.relative_to(self.palace_root)),
                    "reason": "文件内容几乎为空",
                    "size": md.stat().st_size,
                })

        # 3. 检查潜在重复
        titles = defaultdict(list)
        for md in self.palace_root.rglob("*.md"):
            content = self._read_md(md)
            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if title_match:
                titles[title_match.group(1).strip()].append(
                    str(md.relative_to(self.palace_root))
                )

        for title, paths in titles.items():
            if len(paths) > 1:
                suggestions.append({
                    "type": "duplicate",
                    "title": title,
                    "paths": paths,
                    "reason": f"发现 {len(paths)} 个同名记录",
                })

        # 4. 索引健康检查
        index_dir = self.palace_root / "index"
        catalog_path = index_dir / "catalog.json"
        if catalog_path.exists():
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
            records = catalog.get("records", {})
            stale_refs = []
            for rid, rec in records.items():
                fpath = self.palace_root / rec.get("path", "")
                if not fpath.exists():
                    stale_refs.append(rec["path"])
            if stale_refs:
                suggestions.append({
                    "type": "stale_index",
                    "paths": stale_refs,
                    "reason": f"索引中有 {len(stale_refs)} 条指向不存在的文件",
                })
        else:
            suggestions.append({
                "type": "no_index",
                "reason": "索引文件不存在，建议运行 memory_index.py update",
            })

        return {
            "status": "ok",
            "suggestions": suggestions,
            "total": len(suggestions),
            "palace_root": str(self.palace_root),
        }

    # ─── 清理模式 ────────────────────────────────────

    def clean(self, dry_run=False):
        """执行清理"""
        results = {"archived": [], "emptied": [], "deduplicated": [], "index_rebuilt": False}
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # 1. 归档过时记录
        chronicle_dir = self.palace_root / "chronicle"
        if chronicle_dir.exists():
            for md in chronicle_dir.glob("*.md"):
                age = self._file_age_days(md)
                if age > self.days:
                    rel = str(md.relative_to(self.palace_root))
                    if dry_run:
                        results["archived"].append(f"[dry-run] {rel}")
                    else:
                        dest = self.archive_dir / rel.replace("/", "_")
                        shutil.move(str(md), str(dest))
                        results["archived"].append(rel)

        # 2. 清理空文件
        for md in list(self.palace_root.rglob("*.md")):
            if md.stat().st_size < 10 and md.parent.name != "archive":
                rel = str(md.relative_to(self.palace_root))
                if dry_run:
                    results["emptied"].append(f"[dry-run] {rel}")
                else:
                    md.unlink()
                    results["emptied"].append(rel)

        # 3. 重建索引
        if not dry_run:
            from memory_index import MemoryIndex
            idx = MemoryIndex(str(self.palace_root))
            idx.update_index()
            results["index_rebuilt"] = True

        return {
            "status": "ok",
            "dry_run": dry_run,
            "results": results,
            "summary": {
                "archived": len(results["archived"]),
                "emptied": len(results["emptied"]),
                "index_rebuilt": results["index_rebuilt"],
            },
        }

    # ─── 统计模式 ────────────────────────────────────

    def stats(self):
        """记忆宫殿统计信息"""
        stats = {
            "chronicle_entries": 0,
            "palace_rooms": 0,
            "total_files": 0,
            "total_size": 0,
            "by_category": defaultdict(int),
            "oldest": None,
            "newest": None,
            "tags": defaultdict(int),
        }

        for md in self.palace_root.rglob("*.md"):
            if "archive" in md.parts:
                continue
            stats["total_files"] += 1
            stats["total_size"] += md.stat().st_size

            rel = str(md.relative_to(self.palace_root))
            if rel.startswith("chronicle/"):
                stats["chronicle_entries"] += 1
                stats["by_category"]["chronicle"] += 1
            elif rel.startswith("palace/"):
                stats["palace_rooms"] += 1
                parts = rel.split("/")
                if len(parts) >= 3:
                    stats["by_category"][parts[1] + "/" + parts[2]] += 1
            elif rel.startswith("changelog/"):
                stats["by_category"]["changelog"] += 1

            # 时间统计
            mtime = datetime.fromtimestamp(md.stat().st_mtime)
            if stats["oldest"] is None or mtime < datetime.fromisoformat(stats["oldest"]):
                stats["oldest"] = mtime.isoformat()
            if stats["newest"] is None or mtime > datetime.fromisoformat(stats["newest"]):
                stats["newest"] = mtime.isoformat()

            # 标签统计
            content = self._read_md(md)
            for tag in re.findall(r'#([\w\u4e00-\u9fff]+)', content):
                stats["tags"][tag] += 1

        # 人类可读大小
        size = stats["total_size"]
        if size < 1024:
            stats["total_size_human"] = f"{size} B"
        elif size < 1024 * 1024:
            stats["total_size_human"] = f"{size / 1024:.1f} KB"
        else:
            stats["total_size_human"] = f"{size / 1024 / 1024:.1f} MB"

        stats["by_category"] = dict(stats["by_category"])
        stats["tags"] = dict(sorted(stats["tags"].items(), key=lambda x: -x[1])[:20])

        return {"status": "ok", "stats": stats}


def main():
    parser = argparse.ArgumentParser(description="Memory Forge 记忆管家")
    sub = parser.add_subparsers(dest="command")

    # suggest
    p_suggest = sub.add_parser("suggest", help="查看清理建议")
    p_suggest.add_argument("--palace-root", required=True, help="宫殿根目录")

    # clean
    p_clean = sub.add_parser("clean", help="执行清理")
    p_clean.add_argument("--palace-root", required=True, help="宫殿根目录")
    p_clean.add_argument("--days", type=int, default=90, help="归档天数阈值")
    p_clean.add_argument("--dry-run", action="store_true", help="只预览不执行")

    # stats
    p_stats = sub.add_parser("stats", help="查看统计信息")
    p_stats.add_argument("--palace-root", required=True, help="宫殿根目录")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    janitor = MemoryJanitor(args.palace_root, days=getattr(args, "days", 90))

    if args.command == "suggest":
        result = janitor.suggest()
    elif args.command == "clean":
        result = janitor.clean(dry_run=args.dry_run)
    elif args.command == "stats":
        result = janitor.stats()
    else:
        result = {"status": "error", "message": f"未知命令: {args.command}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
