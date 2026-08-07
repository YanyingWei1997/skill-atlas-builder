#!/usr/bin/env python3
"""Scan multiple Skill roots into a portable Skill Atlas inventory."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "unnamed-skill"


def frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    result: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            for line in text[3:end].splitlines():
                match = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.+?)\s*$", line)
                if match:
                    value = match.group(2).strip().strip('"\'')
                    result[match.group(1).lower()] = value.replace("\\n", " ")
            return result
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            result["description"] = line[:500]
            break
    return result


def iter_skill_files(root: Path):
    if not root.exists():
        return
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".DS_Store", "node_modules/.cache"}]
        if "SKILL.md" in files:
            yield Path(current) / "SKILL.md"


def parse_root(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--root 使用 ENV=/absolute/path 格式")
    env, raw = value.split("=", 1)
    if not env.strip() or not raw.strip():
        raise argparse.ArgumentTypeError("环境名和路径都不能为空")
    return env.strip(), Path(raw).expanduser().resolve()


def category(name: str, description: str) -> str:
    text = f"{name} {description}".lower()
    groups = [
        ("论文写作与审稿", ["paper", "manuscript", "journal", "review", "论文", "审稿"]),
        ("研究与文献", ["research", "literature", "citation", "zotero", "文献", "研究"]),
        ("数据与计量", ["stata", "regression", "econometric", "panel", "data", "计量", "数据"]),
        ("设计与媒体", ["design", "diagram", "slide", "image", "video", "visual", "图表", "设计"]),
        ("教学与课程", ["teach", "course", "lesson", "education", "教学", "课程"]),
        ("代码与工程", ["code", "coding", "developer", "software", "webapp", "python", "javascript", "编程", "代码"]),
        ("工作流与管理", ["workflow", "task", "calendar", "notion", "obsidian", "automation", "工作流", "自动化"]),
    ]
    for label, words in groups:
        if any(word in text for word in words):
            return label
    return "其他"


def base_prompt(name: str, description: str, group: str) -> str:
    return (f"${name}\n\n请完成与“{description or name}”相关的任务。\n"
            f"目标：【要完成的具体动作】\n材料：【路径或文本；缺失时说明】\n"
            f"约束：【范围、格式、权限和证据边界】\n\n"
            "先检查输入和前置条件，再执行核心任务。输出可直接使用的结果、依据、验证结果和待确认事项；输入缺失时停止并列出缺失项。")


def variants(name: str, group: str) -> list[dict[str, str]]:
    presets = {
        "代码与工程": [("implement", "实现功能", "在【项目路径】实现【功能】，遵守【技术和兼容性约束】，运行测试并输出变更文件、命令和结果。"), ("debug", "排查报错", "分析【错误信息】和【复现步骤】，先复现再定位，输出根因、最小修复和验证步骤。"), ("review", "代码审查", "审查【diff/目录路径】，按严重程度输出文件位置、证据、影响和可执行修复建议。"), ("deliver", "整理交付", "把【项目路径】整理为可运行交付物，补齐入口、README、测试和运行命令。")],
        "数据与计量": [("audit", "先做数据审计", "审计【数据路径】，检查变量、单位、缺失、重复、异常和时间/面板结构；先不要估计。"), ("estimate", "指定模型估计", "使用【因变量】、【核心变量】、【控制变量】和【模型】分析【数据路径】，说明识别假设和推断方案。"), ("reproduce", "复现结果", "复现【项目路径】中的【表/图】，核对数据、脚本、样本、变量和结果，输出差异与根因。"), ("output", "输出表图", "把【结果/代码路径】整理成【Markdown/CSV/LaTeX/PNG】表图，附生成代码和单位说明。")],
        "论文写作与审稿": [("draft", "快速起草", "根据【材料路径】起草【章节/段落】，遵守【期刊和字数约束】，输出初稿与待补证据。"), ("review", "投稿前审计", "审计【论文路径】，覆盖贡献、方法、证据、引用和格式，按严重程度输出修改任务。"), ("respond", "回复审稿人", "根据【论文路径】和【审稿意见】逐条生成回复，标注修改位置和仍需补证内容。"), ("polish", "保持证据边界", "润色【段落路径】，保持原意；无法由材料支持的表述标记为【待核验】。")],
        "研究与文献": [("search", "围绕问题检索", "围绕【研究问题】检索【主题/地区/年份】，输出检索式、来源、核心结论和证据缺口。"), ("read", "阅读单篇文献", "阅读【论文路径/DOI/网址】，提取问题、机制、数据、方法、结论、局限和可借鉴之处。"), ("matrix", "建立证据矩阵", "根据【文献目录】建立证据矩阵，缺失字段留空并标注，不补写不存在的信息。"), ("synthesize", "形成研究备忘录", "根据【已核验材料】形成研究备忘录，区分原文事实、综合判断和待核验事项。")],
    }
    rows = presets.get(group, [("quick", "快速开始", "处理【目标】；材料是【路径或文本】，约束是【约束】，输出可直接使用的结果。"), ("step", "分步执行", "把【任务】拆成步骤，先检查输入，再执行并报告风险和待确认事项。"), ("check", "深度检查", "检查【对象/路径】的内容、逻辑、事实和格式，按优先级输出问题清单。"), ("handoff", "整理交接", "把【现有材料】整理成可交接结果，附状态、产物路径、阻塞项和下一步。")])
    return [{"id": ident, "label": label, "when": label, "prompt": f"${name} {ident}\n\n{prompt}"} for ident, label, prompt in rows]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", required=True, type=parse_root, help="ENV=/absolute/path，可重复")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preserve", type=Path)
    args = parser.parse_args()
    root_groups: dict[str, list[Path]] = {}
    for env, root in args.root:
        root_groups.setdefault(env, []).append(root)
    old = load_json(args.preserve) if args.preserve else {}
    old_by_id = {str(item.get("id")): item for item in old.get("skills", []) if item.get("id")}
    grouped: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for env, env_roots in root_groups.items():
        for root in env_roots:
            if not root.exists():
                errors.append(f"{env}: 根目录不存在 {root}")
                continue
            for path in iter_skill_files(root) or []:
                meta = frontmatter(path)
                name = meta.get("name") or path.parent.name
                ident = slug(name)
                try:
                    relative = str(path.relative_to(root))
                except ValueError:
                    relative = path.name
                row = grouped.setdefault(ident, {"id": ident, "name": name, "description": meta.get("description", ""), "locations": []})
                if meta.get("description") and not row.get("description"):
                    row["description"] = meta["description"]
                row["locations"].append({"environment": env, "path": str(path), "relative": relative})
    records: list[dict[str, Any]] = []
    for ident, row in sorted(grouped.items()):
        previous = old_by_id.get(ident, {})
        group = previous.get("category") or category(row["name"], row["description"])
        record = dict(previous)
        record.update(row)
        record["category"] = group
        record["descriptionZh"] = previous.get("descriptionZh") or row["description"] or f"处理 {row['name']} 相关任务。"
        record["environments"] = sorted({x["environment"] for x in row["locations"]})
        record["locations"] = sorted(row["locations"], key=lambda x: (x["environment"], x["path"]))
        record["environmentCount"] = len(record["environments"])
        record["overlap"] = record["environmentCount"] > 1
        record["featured"] = bool(previous.get("featured", False))
        record["trigger"] = previous.get("trigger") or f"${ident}"
        record["scenario"] = previous.get("scenario") or ""
        record["keywords"] = previous.get("keywords") or f"{ident} {row['description']} {group}"
        record["prompt"] = previous.get("prompt") or base_prompt(ident, row["description"], group)
        record["variants"] = previous.get("variants") or variants(ident, group)
        record["promptSchemaVersion"] = previous.get("promptSchemaVersion") or "atlas-1"
        records.append(record)
    env_counts = {env: sum(env in r["environments"] for r in records) for env in root_groups}
    data = {
        "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "environmentOrder": list(root_groups),
        "roots": {env: [str(root) for root in env_roots] for env, env_roots in root_groups.items()},
        "installRoots": {env: str(env_roots[0]) for env, env_roots in root_groups.items()},
        "skillCount": len(records),
        "environmentCounts": env_counts,
        "scanErrors": errors,
        "skills": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "skillCount": len(records), "environmentCounts": env_counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
