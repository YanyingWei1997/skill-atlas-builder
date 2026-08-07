# Skill Atlas 索引数据契约

## 顶层对象

```json
{
  "generatedAt": "2026-08-07T19:30:00+08:00",
  "environmentOrder": ["Codex", "Claude", "pi", "Cola"],
  "roots": {"Codex": ["/path/to/skills"]},
  "installRoots": {"Codex": "/path/to/skills", "pi": null},
  "skillCount": 1,
  "environmentCounts": {"Codex": 1},
  "skills": []
}
```

## Skill 条目

```json
{
  "id": "paper-spine",
  "name": "paper-spine",
  "description": "原始 SKILL.md 的英文或原文说明",
  "descriptionZh": "给人看的中文用途说明",
  "category": "论文写作与审稿",
  "environments": ["Codex", "Cola"],
  "locations": [
    {"environment": "Codex", "path": "/path/to/paper-spine/SKILL.md", "relative": "paper-spine/SKILL.md"}
  ],
  "prompt": "可直接复制的主 Prompt",
  "variants": [
    {"id": "audit", "label": "审计", "when": "已有稿件并需要检查", "prompt": "可直接复制的变体 Prompt"}
  ],
  "trigger": "$paper-spine",
  "scenario": "适用场景",
  "keywords": "paper 论文 审计 投稿",
  "featured": true,
  "overlap": true,
  "environmentCount": 2,
  "promptSchemaVersion": "atlas-1"
}
```

## 规则

- `id` 使用稳定的 kebab-case；同名 Skill 跨环境合并，不能产生重复卡片；
- `locations` 保留所有来源，不能用一个路径覆盖其他环境；
- `description` 保留原始说明，`descriptionZh` 负责中文速读，两者不要互相覆盖；
- `environmentCount` 应等于 `environments.length`，`overlap` 应等于是否大于 1；
- 至少一个主 Prompt；推荐 4 个变体，每个变体都有 `label`、`when`、`prompt`；
- Prompt 可使用 `【字段名】`，但必须在 Prompt 中说明字段含义和缺失时的行为；
- 只读任务要把 `sideEffects` 写成 `read-only`，不要默认输出“修改文件”；
- 索引中不保存收藏和用户编辑结果，它们属于浏览器本地状态。
