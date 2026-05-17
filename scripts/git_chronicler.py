#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Forge — Git纪事官
自动生成中文commit message + CHANGELOG更新
"""

import json
import os
import re
import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path


# ─── 中文类型映射 ────────────────────────────────────────────

TYPE_MAP = {
    "feat": "新增",
    "fix": "修复",
    "refactor": "重构",
    "docs": "文档",
    "style": "格式",
    "test": "测试",
    "chore": "构建",
    "perf": "性能",
    "ci": "CI",
    "build": "构建",
}

# 文件扩展名 → 模块推断
EXT_MODULE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "react",
    ".tsx": "react",
    ".vue": "vue",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".md": "文档",
    ".css": "样式",
    ".scss": "样式",
    ".html": "页面",
    ".json": "配置",
    ".yaml": "配置",
    ".yml": "配置",
    ".toml": "配置",
    ".sql": "数据库",
    ".sh": "脚本",
    ".bat": "脚本",
    ".ps1": "脚本",
}


def run_git(repo_path, *args):
    """执行git命令并返回输出"""
    cmd = ["git", "-C", str(repo_path)] + list(args)
    try:
        result = subprocess.run(
            cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_staged_files(repo_path):
    """获取暂存区文件列表"""
    output = run_git(repo_path, "diff", "--cached", "--name-status")
    files = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            status, filepath = parts[0], parts[1]
            files.append({"status": status, "path": filepath})
    return files


def get_unstaged_files(repo_path):
    """获取未暂存的修改"""
    output = run_git(repo_path, "diff", "--name-status")
    files = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append({"status": parts[0], "path": parts[1]})
    return files


def get_untracked_files(repo_path):
    """获取未追踪的文件"""
    output = run_git(repo_path, "ls-files", "--others", "--exclude-standard")
    return [f for f in output.split("\n") if f.strip()]


def infer_type(file_changes):
    """根据文件变更推断commit类型"""
    if not file_changes:
        return "chore"

    paths = [f["path"] for f in file_changes]
    statuses = [f["status"] for f in file_changes]

    # 纯文档变更
    if all(p.endswith(".md") or "/docs/" in p for p in paths):
        return "docs"

    # 纯测试变更
    if all("test" in p.lower() or "spec" in p.lower() for p in paths):
        return "test"

    # 纯样式变更
    if all(p.endswith((".css", ".scss", ".less", ".sass")) for p in paths):
        return "style"

    # 纯配置变更
    if all(p.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".env")) for p in paths):
        return "chore"

    # 有新增文件 → feat
    if any(s.startswith("A") for s in statuses):
        return "feat"

    # 有修改 → 默认fix（如果有更多上下文可以更准确）
    return "fix"


def infer_scope(file_changes):
    """推断变更范围"""
    if not file_changes:
        return ""

    modules = set()
    for f in file_changes:
        path = f["path"]
        # 尝试从路径提取模块名
        parts = Path(path).parts
        if len(parts) > 1:
            # src/module/file.py → module
            for p in parts[:-1]:
                if p not in ("src", "lib", "pkg", "app", "internal", "cmd"):
                    modules.add(p)
                    break
        else:
            # 根目录文件，用扩展名推断
            ext = Path(path).suffix
            if ext in EXT_MODULE:
                modules.add(EXT_MODULE[ext])

    return ",".join(sorted(modules)) if modules else ""


def generate_commit_message(repo_path, custom_type=None, custom_scope=None, custom_desc=None):
    """生成中文commit message"""
    staged = get_staged_files(repo_path)
    unstaged = get_unstaged_files(repo_path)
    untracked = get_untracked_files(repo_path)

    if not staged and not unstaged and not untracked:
        return {
            "status": "info",
            "message": "没有需要提交的变更",
            "staged": [],
            "unstaged": [],
            "untracked": [],
        }

    # 如果有未暂存的变更，提示用户
    if not staged and (unstaged or untracked):
        return {
            "status": "warning",
            "message": "有变更但未暂存，请先 git add",
            "staged": [],
            "unstaged": unstaged,
            "untracked": untracked,
            "suggestion": "运行 git add -A 或选择性地添加文件",
        }

    # 推断类型和范围
    commit_type = custom_type or infer_type(staged)
    scope = custom_scope or infer_scope(staged)

    # 生成简述
    if custom_desc:
        desc = custom_desc
    else:
        type_label = TYPE_MAP.get(commit_type, commit_type)
        if len(staged) == 1:
            desc = f"{type_label} {Path(staged[0]['path']).name} 的相关修改"
        else:
            # 按模块分组描述
            module_files = defaultdict(list)
            for f in staged:
                mod = infer_scope([f]) or "其他"
                module_files[mod].append(Path(f["path"]).name)
            parts = []
            for mod, fnames in module_files.items():
                if len(fnames) <= 3:
                    parts.append(f"{mod}: {', '.join(fnames)}")
                else:
                    parts.append(f"{mod}: {', '.join(fnames[:3])} 等{len(fnames)}个文件")
            desc = f"{type_label} " + "; ".join(parts)

    # 生成详细说明
    details = []
    for f in staged:
        status_label = {"A": "新增", "M": "修改", "D": "删除", "R": "重命名"}.get(
            f["status"][0], f["status"]
        )
        details.append(f"- {status_label} {f['path']}")

    # 组装commit message
    scope_str = f"({scope})" if scope else ""
    header = f"{commit_type}{scope_str}: {desc}"
    body = "\n".join(details)

    commit_msg = f"{header}\n\n{body}"

    return {
        "status": "ok",
        "commit_message": commit_msg,
        "type": commit_type,
        "scope": scope,
        "desc": desc,
        "files": staged,
    }


def update_changelog(repo_path, commit_msg, commit_hash="HEAD"):
    """更新CHANGELOG.md"""
    changelog_path = Path(repo_path) / "CHANGELOG.md"

    if changelog_path.exists():
        content = changelog_path.read_text(encoding="utf-8")
    else:
        content = "# 变更日志\n\n## [Unreleased]\n\n"

    # 解析commit类型
    lines = commit_msg.split("\n")
    header = lines[0]
    body_lines = lines[2:] if len(lines) > 2 else []

    # 判断分类
    if header.startswith("feat"):
        section = "### 新增\n"
    elif header.startswith("fix"):
        section = "### 修复\n"
    elif header.startswith("refactor"):
        section = "### 变更\n"
    elif header.startswith("perf"):
        section = "### 性能\n"
    else:
        section = "### 其他\n"

    # 提取简述
    desc = re.sub(r'^(feat|fix|refactor|docs|style|test|chore|perf|ci|build)(\(.+?\))?:\s*', '', header)
    hash_ref = f" ({commit_hash[:7]})" if commit_hash != "HEAD" else ""

    entry = f"- {desc}{hash_ref}\n"

    # 在 [Unreleased] 下的对应分类中插入
    unreleased_marker = "## [Unreleased]"
    if unreleased_marker in content:
        idx = content.index(unreleased_marker) + len(unreleased_marker)
        # 检查是否已有该分类
        section_idx = content.find(section, idx)
        if section_idx != -1 and section_idx < content.find("## ", idx + 10):
            # 在该分类下插入
            insert_idx = section_idx + len(section)
            content = content[:insert_idx] + entry + content[insert_idx:]
        else:
            # 添加新分类
            content = content[:idx] + "\n\n" + section + entry + content[idx:]
    else:
        content += f"\n{unreleased_marker}\n\n{section}{entry}"

    changelog_path.write_text(content, encoding="utf-8")
    return {"status": "ok", "message": "CHANGELOG.md 已更新", "entry": entry.strip()}


def do_commit(repo_path, auto_changelog=False):
    """执行git commit"""
    result = generate_commit_message(repo_path)

    if result["status"] != "ok":
        return result

    commit_msg = result["commit_message"]

    # 执行commit
    output = run_git(repo_path, "commit", "-m", commit_msg)

    if "ERROR" in output:
        return {"status": "error", "message": f"提交失败: {output}"}

    # 获取commit hash
    commit_hash = run_git(repo_path, "rev-parse", "HEAD")

    # 更新CHANGELOG
    changelog_result = None
    if auto_changelog:
        changelog_result = update_changelog(repo_path, commit_msg, commit_hash)

    return {
        "status": "ok",
        "message": "提交成功",
        "commit_hash": commit_hash,
        "commit_message": commit_msg,
        "changelog": changelog_result,
    }


def main():
    parser = argparse.ArgumentParser(description="Memory Forge Git纪事官")
    sub = parser.add_subparsers(dest="command")

    # generate
    p_gen = sub.add_parser("generate", help="生成commit message")
    p_gen.add_argument("--repo", required=True, help="仓库路径")
    p_gen.add_argument("--type", help="自定义commit类型")
    p_gen.add_argument("--scope", help="自定义范围")
    p_gen.add_argument("--desc", help="自定义简述")

    # commit
    p_commit = sub.add_parser("commit", help="执行提交")
    p_commit.add_argument("--repo", required=True, help="仓库路径")
    p_commit.add_argument("--auto-changelog", action="store_true", help="自动更新CHANGELOG")

    # changelog
    p_cl = sub.add_parser("changelog", help="手动更新CHANGELOG")
    p_cl.add_argument("--repo", required=True, help="仓库路径")
    p_cl.add_argument("--message", required=True, help="commit message")
    p_cl.add_argument("--hash", default="HEAD", help="commit hash")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        result = generate_commit_message(
            args.repo,
            custom_type=args.type,
            custom_scope=args.scope,
            custom_desc=args.desc,
        )
    elif args.command == "commit":
        result = do_commit(args.repo, auto_changelog=args.auto_changelog)
    elif args.command == "changelog":
        result = update_changelog(args.repo, args.message, args.hash)
    else:
        result = {"status": "error", "message": f"未知命令: {args.command}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
