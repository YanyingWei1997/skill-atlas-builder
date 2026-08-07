# 脚本说明

## `scan_skill_roots.py`

将多个环境根目录扫描为一个索引。用重复的 `--root ENV=PATH` 传入环境；支持 `--preserve` 保留人工整理字段。它只认包含 `SKILL.md` 的目录，不把普通 README 当作 Skill。

## `build_skill_atlas.py`

读取 HTML 模板和 JSON 索引，把索引嵌入 `<script id="skill-data" type="application/json">`，并替换标题、字幕和简介 token。它不会修改原始模板，也不会重新扫描目录。

## `validate_skill_atlas.py`

检查 JSON 与 HTML 内嵌数据是否一致、ID 是否唯一、位置和环境是否完整、主 Prompt 与变体是否存在、模板 token 是否已经替换。它不能代替浏览器中的交互验收。

## 组合命令

```bash
python3 scripts/scan_skill_roots.py \
  --root Codex=/path/to/codex/skills \
  --root Claude=/path/to/claude/skills \
  --output build/skill-inventory.json

python3 scripts/build_skill_atlas.py \
  --template assets/skill-atlas-template.html \
  --inventory build/skill-inventory.json \
  --output build/skill-atlas.html

python3 scripts/validate_skill_atlas.py \
  --inventory build/skill-inventory.json \
  --html build/skill-atlas.html
```
