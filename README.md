# Skill Atlas Builder

Build a private, local Skill Atlas for **your own computer**.

This is a reusable Agent Skill plus a small, dependency-free toolchain. It scans the Skill directories you explicitly provide, merges duplicate Skills across runtimes, and generates a standalone HTML workbench with search, task filters, environment badges, favorites, editable Prompts, and validation.

It does **not** upload your local Skill list, Prompt edits, paths, or personal data anywhere. The generated inventory and HTML stay in the output directory you choose.

## What it creates

- `skill-inventory.json` — your machine's discovered Skills and source locations;
- `skill-atlas.html` — a standalone page you can open directly in a browser;
- optional local install/delete commands shown in the page;
- validation output confirming that the JSON and embedded HTML data agree.

## Install the Skill

Install the Skill folder into the Agent environment you use:

```bash
# Cola
mkdir -p ~/.cola/skills
cp -R skills/skill-atlas-builder ~/.cola/skills/

# Codex
mkdir -p ~/.codex/skills
cp -R skills/skill-atlas-builder ~/.codex/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R skills/skill-atlas-builder ~/.claude/skills/
```

Or copy this repository's `skills/skill-atlas-builder/` directory into the relevant Skill directory. Start a new Agent session after installation so it can discover the Skill.

## Build your own Atlas

Run these commands from the Skill directory or reference the scripts with their full paths:

```bash
mkdir -p build

python3 scripts/scan_skill_roots.py \
  --root Codex="$HOME/.codex/skills" \
  --root Claude="$HOME/.claude/skills" \
  --root Cola="$HOME/.cola/skills" \
  --output build/skill-inventory.json

python3 scripts/build_skill_atlas.py \
  --template assets/skill-atlas-template.html \
  --inventory build/skill-inventory.json \
  --output build/skill-atlas.html \
  --title "我的 Skill Atlas" \
  --subtitle "我的多环境技能速查"

python3 scripts/validate_skill_atlas.py \
  --inventory build/skill-inventory.json \
  --html build/skill-atlas.html

open build/skill-atlas.html       # macOS
# xdg-open build/skill-atlas.html # Linux
```

Only pass roots that exist on your computer. The same environment can be passed more than once when it has multiple Skill locations:

```bash
python3 scripts/scan_skill_roots.py \
  --root Codex="$HOME/.codex/skills" \
  --root Codex="$HOME/.codex/plugins/cache" \
  --root Claude="$HOME/.claude/skills" \
  --output build/skill-inventory.json
```

For pi or another runtime, provide the directory that actually contains its `SKILL.md` files:

```bash
python3 scripts/scan_skill_roots.py \
  --root pi="$HOME/.pi/agent/npm/node_modules" \
  --output build/skill-inventory.json
```

## Preserve your curation

Pass an earlier inventory with `--preserve` to keep manually curated fields such as Chinese descriptions, featured flags, Prompt edits stored in the JSON, scenarios, and keywords:

```bash
python3 scripts/scan_skill_roots.py \
  --root Codex="$HOME/.codex/skills" \
  --preserve build/skill-inventory.json \
  --output build/skill-inventory.json.new
mv build/skill-inventory.json.new build/skill-inventory.json
```

Review generated Prompt templates before treating them as final. The scanner creates a useful starting point; semantic curation belongs to the person maintaining the Atlas.

## Classification behavior

The scanner classifies by the Skill's work object rather than by the word `paper` alone:

- manuscript writing, peer review, submission, and reviewer-response tools → `论文写作与审稿`;
- grant topic framing, proposal writing, research plans, application review, and submission output → `课题基金申请`;
- literature reading, topic design, and research scouting → `研究与文献`;
- regression, identification, mechanism, heterogeneity, and model evaluation → `数据与计量`;
- figures, plotting, diagrams, slides, and presentation design → `设计与媒体`;
- coding, runtime, and developer utilities → `代码与工程`.

This keeps a paper figure in the visual category and a paper's regression tool in the data category, while keeping the manuscript workflow in the paper category.

## Design and behavior

The template provides:

- task-first navigation, with task counts derived from each Skill's primary work-object category rather than loose keyword matches;
- explicit note that per-runtime counts are independent and can overlap;
- all, featured, favorites, and multi-runtime views;
- environment and category filters;
- relevance search across names, descriptions, scenarios, keywords, and Prompts;
- detail modal with source paths and editable main Prompt;
- four scenario variants per curated Skill;
- localStorage for favorites and Prompt edits;
- safe command generation; deletion moves to the system Trash instead of permanently removing a directory;
- direct file opening without a server.

The page never executes installation, deletion, or synchronization commands by itself. A person must review and run any command in Terminal.

## File layout

```text
skill-atlas-builder/
├── SKILL.md
├── README.md
├── LICENSE
├── assets/
│   ├── inventory.example.json
│   └── skill-atlas-template.html
├── examples/
├── references/
└── scripts/
    ├── scan_skill_roots.py
    ├── build_skill_atlas.py
    └── validate_skill_atlas.py
```

Read `SKILL.md` when asking an Agent to design or maintain an Atlas. Read the files in `references/` when changing the data contract, Prompt behavior, UI, or validation rules.

## License and attribution

This package is released under [CC BY-NC-SA 4.0](LICENSE). The HTML template is adapted from the Esther Design System and retains the required source attribution. It is intended for non-commercial sharing and adaptation under the same license.
