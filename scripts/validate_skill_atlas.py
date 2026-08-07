#!/usr/bin/env python3
"""Validate the portable Skill Atlas inventory and generated HTML."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def embedded(html: str) -> dict:
    marker = '<script id="skill-data" type="application/json">'
    if marker not in html:
        raise ValueError("HTML 缺少 skill-data JSON")
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    return json.loads(html[start:end])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.inventory.read_text(encoding="utf-8"))
    page = embedded(args.html.read_text(encoding="utf-8"))
    skills = data.get("skills", [])
    ids = [s.get("id") for s in skills]
    problems: list[str] = []
    if len(ids) != len(set(ids)):
        problems.append("Skill ID 重复")
    if page.get("skillCount") != data.get("skillCount"):
        problems.append("HTML 与 JSON 的 skillCount 不一致")
    if [s.get("id") for s in page.get("skills", [])] != ids:
        problems.append("HTML 与 JSON 的 Skill 顺序或内容不一致")
    for index, skill in enumerate(skills):
        prefix = f"skills[{index}]/{skill.get('id', '?')}"
        for field in ("name", "description", "category", "environments", "locations", "prompt"):
            if not skill.get(field):
                problems.append(f"{prefix} 缺少 {field}")
        if len(skill.get("environments", [])) != skill.get("environmentCount"):
            problems.append(f"{prefix} environmentCount 不一致")
        if bool(skill.get("overlap")) != (len(skill.get("environments", [])) > 1):
            problems.append(f"{prefix} overlap 不一致")
        if len(skill.get("variants", [])) < 1:
            problems.append(f"{prefix} 没有变体 Prompt")
        for variant in skill.get("variants", []):
            if not variant.get("label") or not variant.get("prompt"):
                problems.append(f"{prefix} 存在不完整变体")
    html = args.html.read_text(encoding="utf-8")
    if "{{ATLAS_" in html or "__ATLAS_" in html:
        problems.append("HTML 仍有未替换模板 token")
    if problems:
        print("VALIDATION_FAIL")
        print("\n".join(f"- {p}" for p in problems))
        raise SystemExit(1)
    print(json.dumps({"status": "pass", "skillCount": len(skills), "variantCount": sum(len(s.get("variants", [])) for s in skills)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
