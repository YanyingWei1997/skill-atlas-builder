---
name: skill-atlas-builder
description: >
  制作只保存在本机的 Skill Atlas / 技能速查网页：扫描使用者自己电脑上多个 AI Agent 环境中的 SKILL.md，合并成可搜索、按任务筛选、按主题和运行环境过滤的索引，提供收藏、详情、Prompt 复制与本地编辑、可选安装/删除命令生成、同步和验证。Use when someone asks to build a personal skill directory, prompt workbench, skill catalog, multi-runtime skill index, searchable local HTML dashboard, or a similar tool for Codex, Claude, pi, Cola, or other agent environments. Never upload the scanned inventory unless the person explicitly asks for publication.
---

# Skill Atlas Builder

把一组分散的 Skill 目录做成一个真正能用的本地网页工作台，而不是只生成一张静态卡片墙。工作台的核心是：先按工作任务找到候选 Skill，再查看运行环境和来源，最后复制一个可以继续编辑的 Prompt。

## 什么时候使用

当需求包含“Skill 索引/目录/速查”“Prompt 工作台”“Codex、Claude、pi、Cola 统一管理”“搜索和收藏 Skill”“安装/删除 Skill 按钮”“本地 HTML 技能面板”或“做一个类似这个页面”时使用。

## 交付目标

交付一个可直接打开的 HTML、一个可重建的 JSON 索引、一个可重复运行的扫描/构建脚本，以及一份 README。网页应能脱离服务器运行；安装和删除只生成供人确认后执行的 Terminal 命令，不在页面中静默改写本机目录。

## 工作流

### 1. 锁定输入与边界

先确认以下输入；缺少时用合理默认值并把假设写进 README：

- 输出目录和网页名称；
- 要扫描的环境及其 Skill 根目录；每个环境可有多个根目录；
- 是否保留已有索引中的中文说明、收藏、Prompt 和 featured 标记；
- 是否允许页面生成安装/删除命令；pi 这类由 npm 扩展管理的环境应只展示来源，不伪造目录复制命令；
- 页面标题、品牌色、任务入口和主题分类。

不要把当前电脑的绝对路径写死在模板、Skill 正文或示例中。绝对路径只能来自用户的配置或扫描命令。

### 2. 读取必要参考

- 设计页面或 App 型工作台时，读取 `references/ui-blueprint.md`；
- 设计索引数据时，读取 `references/inventory-schema.md`；
- 设计 Prompt 复制区时，读取 `references/prompt-schema.md`；
- 使用扫描、构建或验证脚本时，读取 `references/scripts.md`；
- 交付前读取 `references/validation.md`；
- 面向其他电脑或公开发布时读取 `references/portability.md`，检查路径、平台和隐私边界。

如果用户要求 YING 风格且当前环境提供 `ying-design-system`，先读取它并沿用固定色板和 App 场景规则；如果该设计 Skill 不存在，就使用本 Skill 的通用模板，不要假设任何本机品牌资源。不要把本 Skill 的示例模板当成 YING 设计系统的唯一权威。

### 3. 生成或更新索引

优先使用：

```bash
python3 scripts/scan_skill_roots.py \
  --root Codex=/path/to/codex/skills \
  --root Claude=/path/to/claude/skills \
  --root Cola=/path/to/cola/skills \
  --preserve /path/to/old-inventory.json \
  --output /path/to/skill-inventory.json
```

扫描器只把实际存在且包含 `SKILL.md` 的目录纳入索引。相同 Skill 在多个环境出现时合并为一个条目，并保留所有来源位置；无法读取的目录进入报告，不要静默当成“没有 Skill”。

### 4. 做语义整理

扫描只是底稿，不是最终内容。逐项检查：

- 中文用途是否说明“能解决什么问题”，而不是只翻译名称；
- 分类是否符合真实能力，不能因为批量模板把基金评审归成数据分析、把前端设计归成配图；
- 主 Prompt 是否有明确动作、输入、前置条件、约束、输出和验证；
- 变体是否对应该 Skill 的真实场景；代码、数据、评审、研究、视觉、文件提取和工作流使用不同字段；
- 缺少材料时是否停止并列出缺失项，而不是臆造；
- 只读 Skill 的输出不要默认写“修改文件”，有副作用的 Skill 要明确标注。

可使用 `references/prompt-schema.md` 中的结构化字段，再渲染成自然语言 Prompt。占位符必须使用统一的 `【字段名】` 形式，并在附近说明字段是否必填和示例；不要混用 `{}`、`[]`、`{{}}`。

### 5. 构建网页

使用 `assets/skill-atlas-template.html` 作为受控起点，不要从空白 HTML 重新拼一个近似页面：

```bash
python3 scripts/build_skill_atlas.py \
  --template assets/skill-atlas-template.html \
  --inventory /path/to/skill-inventory.json \
  --output /path/to/skill-atlas.html \
  --title "我的 Skill Atlas" \
  --subtitle "多环境技能速查"
```

网页至少保留这些能力：

1. 工作任务入口；
2. 全部、工作集、收藏、多端共有视图；
3. 环境和主题过滤；
4. 名称、中文用途、场景、关键词和 Prompt 的相关度搜索；
5. 紧凑卡片和详情弹窗；
6. 主 Prompt 编辑、保存、重置、复制；
7. 4 个有明确用途的变体，并支持“套用变体后继续编辑”；
8. 收藏和本地自动保存；
9. 安装/删除命令生成，删除命令移动到系统废纸篓；
10. 导出 JSON、同步时间和无服务器直接打开。

如果用户只需要索引，不要强行加入安装/删除动作；如果用户需要真实安装，先说明网页本身只负责生成命令，实际执行必须由人确认。

### 6. 验证和交付

运行：

```bash
python3 scripts/validate_skill_atlas.py \
  --inventory /path/to/skill-inventory.json \
  --html /path/to/skill-atlas.html
```

然后用浏览器打开 HTML，至少实测：搜索、任务入口、环境过滤、打开详情、复制主 Prompt、套用变体、保存/重置、收藏和移动端布局。详情见 `references/validation.md`。

## 输出契约

最终目录至少包含：

```text
skill-atlas/
├── skill-atlas.html
├── skill-inventory.json
├── README.md
├── LICENSE
└── scripts/
    ├── scan_skill_roots.py
    ├── build_skill_atlas.py
    └── validate_skill_atlas.py
```

若用户要求把“制作方法”本身做成 Skill，则将本目录复制或链接到 Agent 的 Skill 目录，并把当前网页作为一个示例，不要把 574 个具体 Skill 数据硬编码进 Skill 正文。

## 失败处理

- 找不到 Skill 根目录：报告路径和可扫描的其他根目录，不猜测；
- 没有 `SKILL.md`：输出空索引并明确说明，不把普通文件夹算作 Skill；
- 索引和 HTML 不一致：停止交付，重新构建，不手改嵌入 JSON；
- Prompt 主题错配：保留原始 Skill 描述，标记待人工整理，并阻止生成“看似完整但实际不适用”的变体；
- 浏览器验证失败：记录页面、操作、控制台错误和复现步骤。
