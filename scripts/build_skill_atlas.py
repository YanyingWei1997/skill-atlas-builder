#!/usr/bin/env python3
"""Embed an inventory into the Skill Atlas HTML shell."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="Skill Atlas")
    parser.add_argument("--subtitle", default="多环境技能速查")
    parser.add_argument("--eyebrow", default="SKILL INDEX / 中文速读版")
    parser.add_argument("--headline", default="先说任务，<span class=\"hl-yellow\">再选 Skill。</span>")
    parser.add_argument("--intro", default="按工作任务、主题和运行环境找到合适的 Skill，并复制可以继续编辑的 Prompt。")
    args = parser.parse_args()
    html = args.template.read_text(encoding="utf-8")
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    marker = '<script id="skill-data" type="application/json">'
    if marker not in html:
        raise SystemExit("模板缺少 skill-data JSON 标记")
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html[:start] + payload + html[end:]
    replacements = {
        "__ATLAS_TITLE__": args.title,
        "__ATLAS_SUBTITLE__": args.subtitle,
        "__ATLAS_EYEBROW__": args.eyebrow,
        "__ATLAS_HEADLINE__": args.headline,
        "__ATLAS_INTRO__": args.intro,
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "skillCount": data.get("skillCount", len(data.get("skills", [])))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
