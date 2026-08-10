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
    """Classify by work object, not merely by the word 'paper'.

    Visual and empirical tools often mention papers in their descriptions; those
    signals are checked before the writing/review bucket so a paper figure or
    regression Skill does not become a manuscript-writing Skill.
    """
    ident = slug(name)
    text = f"{name} {description}".lower()
    explicit = {
        "01-topic": "课题基金申请",
        "02-literature-plan": "课题基金申请",
        "03-academic-search": "课题基金申请",
        "04-paper-digest": "课题基金申请",
        "05-synthesis": "课题基金申请",
        "06-helm": "课题基金申请",
        "07-outline": "课题基金申请",
        "08-section-write": "课题基金申请",
        "09-assemble": "课题基金申请",
        "10-review": "课题基金申请",
        "11-output": "课题基金申请",
        "auto": "课题基金申请",
        "fund-background-writer": "课题基金申请",
        "fund-literature-review-writer": "课题基金申请",
        "fund-research-content-writer": "课题基金申请",
        "fund-technical-route-writer": "课题基金申请",
        "review-grant": "课题基金申请",
        "paper-spine": "论文写作与审稿",
        "academic-paper": "论文写作与审稿",
        "academic-paper-reviewer": "论文写作与审稿",
        "academic-paper-writer": "论文写作与审稿",
        "academic-writing-dna-skill": "论文写作与审稿",
        "ara-rigor-reviewer": "论文写作与审稿",
        "benchmark-paper-template": "论文写作与审稿",
        "business-paper-writing": "论文写作与审稿",
        "frontend-design": "代码与工程",
        "journal-template-extract": "论文写作与审稿",
        "ml-paper-writing": "论文写作与审稿",
        "paper-review": "论文写作与审稿",
        "paper-self-review": "论文写作与审稿",
        "thesis-review": "论文写作与审稿",
        "review-paper": "论文写作与审稿",
        "reviewer-response-docx": "论文写作与审稿",
        "paper-framework-figure-studio-pro": "设计与媒体",
        "happy-figure-skill": "设计与媒体",
        "econ-visualization": "设计与媒体",
        "empirical-pipeline": "数据与计量",
        "python-panel-data": "数据与计量",
        "stata-regression": "数据与计量",
        "phd-topic-designer": "研究与文献",
        "deep-research": "研究与文献",
        "citation-verification": "研究与文献",
        "peer-review": "论文写作与审稿",
        "webapp-testing": "代码与工程",
        "nature-reader": "研究与文献",
    }
    if ident in explicit:
        return explicit[ident]
    if any(k in text for k in ["figure", "plotting", "visualization", "diagram", "drawio", "slide", "presentation", "image generation", "科研绘图", "图表", "配图"]):
        return "设计与媒体"
    if any(k in text for k in ["stata", "regression", "econometric", "panel data", "identification strategy", "mechanism analysis", "heterogeneity", "model evaluation", "data analysis", "计量", "回归", "识别策略", "机制检验"]):
        return "数据与计量"
    if any(k in text for k in ["grant", "funding", "fund proposal", "research proposal", "nsfc", "proposal writing", "申请书", "课题申请", "基金申请", "项目申请"]):
        return "课题基金申请"
    if any(k in text for k in ["paper-review", "manuscript", "journal article", "academic paper", "paper writing", "peer review", "reviewer", "thesis", "dissertation", "论文", "审稿", "学位论文"]):
        return "论文写作与审稿"
    if any(k in text for k in ["research", "literature", "citation", "zotero", "topic selection", "paper reader", "文献", "研究", "选题"]):
        return "研究与文献"
    if any(k in text for k in ["code", "coding", "developer", "software", "api", "webapp", "javascript", "typescript", "python package", "编程", "代码"]):
        return "代码与工程"
    if any(k in text for k in ["teach", "course", "lesson", "education", "教学", "课程"]):
        return "教学与课程"
    if any(k in text for k in ["workflow", "task", "calendar", "notion", "obsidian", "automation", "工作流", "自动化"]):
        return "工作流与管理"
    return "其他"


CATEGORY_PURPOSE = {
    "课题基金申请": "课题立项、基金申请书和申报评审材料",
    "论文写作与审稿": "论文写作、修改、审稿或投稿材料",
    "研究与文献": "文献检索、阅读、研究设计或证据整理",
    "数据与计量": "数据处理、计量分析、复现或结果核查",
    "设计与媒体": "图表、网页、PPT、配图或其他视觉媒体",
    "代码与工程": "代码实现、调试、测试或工程交付",
    "教学与课程": "课程设计、教学材料或练习评价",
    "工作流与管理": "笔记、任务、邮件、日历或自动化工作流",
    "其他": "原始说明中定义的专项任务",
}

GENERIC_ZH = {"", "用于检索、阅读、文献综述、引用管理和证据整理。", "用于网页、课件、图表、配图、演示文稿和多媒体制作。", "用于数据清洗、计量分析、绘图、复现和结果核查。", "用途暂未归入主要工作流，打开详情查看原始说明和来源路径。"}


def description_zh(previous: dict[str, Any], name: str, category_name: str) -> str:
    old = str(previous.get("descriptionZh") or "").strip()
    if old and old not in GENERIC_ZH and not old.startswith("待补充"):
        return old
    purpose = CATEGORY_PURPOSE.get(category_name, CATEGORY_PURPOSE["其他"])
    return f"围绕“{name}”处理{purpose}；具体能力以详情中的原始说明和来源文件为准。"


def scenario_for(category_name: str) -> str:
    return {
        "课题基金申请": "当你需要做课题论证、写基金申请书、组织研究方案或进行申报评审时使用。",
        "论文写作与审稿": "当你需要写论文、改稿、审稿、回复意见或准备投稿材料时使用。",
        "研究与文献": "当你需要检索、阅读文献、设计研究问题或整理证据时使用。",
        "数据与计量": "当你需要清洗数据、估计模型、复现结果或核查数据与代码时使用。",
        "设计与媒体": "当你需要制作图表、网页、PPT、配图、音视频或其他视觉交付物时使用。",
        "代码与工程": "当你需要实现功能、排查报错、测试代码、操作仓库或完成工程交付时使用。",
        "教学与课程": "当你需要备课、设计课程、生成练习或建立评价方案时使用。",
        "工作流与管理": "当你需要处理笔记、邮件、日历、任务或自动化流程时使用。",
    }.get(category_name, "当任务与该 Skill 的原始说明直接相关时使用，并先核对输入和前置条件。")


def base_prompt(name: str, description: str, group: str) -> str:
    if group == "课题基金申请":
        return (f"${name}\n\n请完成以下课题或基金申请任务。\n"
                "课题/申报类型：【课题名称、基金类型、申报年度和指南要求】\n"
                "材料：【课题资料、政策/指南、文献、前期成果或项目路径】\n"
                "任务：【立项依据、科学问题、研究内容、技术路线、创新点或评审】\n"
                "约束：【字数、格式、评审标准和证据边界】\n\n"
                "区分已核验事实、研究设想、估计值和待补证内容；输出可直接使用的结果、依据、材料位置和待确认事项。")
    return (f"${name}\n\n请完成与“{description or name}”相关的任务。\n"
            f"目标：【要完成的具体动作】\n材料：【路径或文本；缺失时说明】\n"
            f"约束：【范围、格式、权限和证据边界】\n\n"
            "先检查输入和前置条件，再执行核心任务。输出可直接使用的结果、依据、验证结果和待确认事项；输入缺失时停止并列出缺失项。")


def specialized_variants(name: str, description: str) -> list[tuple[str, str, str]]:
    ident = name.lower()
    if ident in {"academic-paper", "academic-pipeline", "paper-spine", "social-science-paperwork"}:
        return []
    if ident in {"academic-humanizer", "dissertation-polisher-zh", "writing-anti-ai"}:
        return [("voice", "保留作者语气", "润色【段落/章节路径】，保持作者原有语气、论点和证据强度；输出修改稿与不应改动的判断。"), ("mechanical", "降低机械表达", "检查【文本路径】中的模板化、重复和空泛表达，在不增加新事实的前提下改写，并列出具体改动。"), ("academic", "学术语气对照", "为【原文路径】输出原文、学术化修改稿和逐句修改理由；不要改变变量、结论、引用和限定条件。"), ("evidence", "保持证据边界", "重写【文本路径】，只使用已有材料；无法由材料支持的强化表述标记为【待核验】。")]
    if ident in {"preflight-audit", "paper-self-review", "academic-paper-reviewer", "paper-review"}:
        return [("gate", "投稿门禁", "审计【论文/项目路径】是否达到投稿或交付门槛，按致命、重要、一般问题输出阻塞清单。"), ("evidence", "证据审计", "检查【论文路径】的主张、数据、方法、引用和图表是否相互支持；标出证据缺口。"), ("integrity", "格式与完整性", "检查【交付目录】的文件、命名、引用、表图、附录和编译/打开状态，给出修复顺序。"), ("tasks", "生成修订清单", "把【审计结果/论文路径】转换为带文件位置、优先级、验收标准和负责人字段的修订任务表。")]
    hay = f"{name} {description}".lower()
    profiles = [
        (("bibtex", "citation", "zotero", "引用"), [("parse", "解析 BibTeX", "读取【.bib 文件路径】并解析条目；报告键名、作者、标题、年份、DOI 和缺失字段，不要擅自补全。"), ("validate", "校验引用字段", "检查【.bib 文件路径】中的重复键、必填字段、作者格式和 DOI；按错误、警告、待人工核验分级输出。"), ("verify", "核对文献元数据", "根据【BibTeX 条目】和【DOI/数据库来源】逐字段核对标题、作者、年份和期刊；标注冲突来源。"), ("export", "导出引用库", "将【BibTeX/引用数据库路径】清理后导出为【BibTeX/CSL-JSON/CSV】，附变更日志和未解决条目。")]),
        (("playwright", "webapp", "frontend", "网页", "browser"), [("reproduce", "复现交互问题", "在【项目路径】按【复现步骤】验证页面，记录控制台错误、网络请求和实际结果；先复现再判断根因。"), ("implement", "实现页面功能", "在【项目路径】实现【页面/交互功能】，遵守【技术和视觉约束】，补充最小可靠测试。"), ("browser", "浏览器验收", "用浏览器验证【验收标准】，覆盖桌面/移动视口、关键点击、表单状态和控制台错误，只报告实际结果。"), ("deliver", "整理网页交付", "将【项目路径】整理为可运行网页交付物，检查启动命令、资源路径、构建产物和 README。")]),
        (("latex-", "beamer", "tex-to", "typesetting", "omml-to", "convert-latex", "编译 tex", "排版模板"), [("compile", "编译排错", "编译【TeX 项目路径】，定位首个根因，区分环境、语法、引用和排版警告，给出最小修复。"), ("template", "适配期刊模板", "根据【期刊/会议模板路径】调整【TeX 项目】的文档类、宏包、章节、引用和图表格式。"), ("figures", "整理表图与引用", "检查【TeX 项目路径】中的表格、图片、交叉引用和参考文献，输出问题位置和修复补丁。"), ("package", "准备投稿包", "将【TeX 项目路径】整理成可提交压缩包，检查主文件、图片、.bib、辅助文件和匿名化要求。")]),
        (("document-extract", "table-lossless-extract", "text-extract", "pdf-", "docx-", "xlsx-", "omml-", "文档提取", "表格提取"), [("extract", "抽取结构化内容", "从【文档路径】抽取【文本/表格/标题/元数据】，保留页码、表号、单位和原始顺序。"), ("convert", "保留结构转换", "将【源文档路径】转换为【目标格式】，保留标题、表格、脚注、引用和关键格式，并列出转换损失。"), ("batch", "批量处理文档", "批量处理【文件夹路径】中的【文档类型】，先抽样检查，再输出文件清单、失败项和日志。"), ("check", "核验交付文件", "检查【输出文档路径】的内容完整性、页数、表格、链接、编码和可打开性。")]),
        (("stata", "回归", "计量", "面板", "econometric", "event study"), [("audit", "审计变量与面板", "审计【数据路径】的变量定义、单位、缺失、重复、时间/地区键和面板结构；先不估计。"), ("identify", "落实识别策略", "根据【研究问题】、【处理变量】和【数据路径】设计/估计【模型】，明确识别假设、固定效应和聚类层级。"), ("robust", "做稳健性核查", "对【主回归脚本/结果路径】执行【稳健性方案】，核对样本、变量、标准误和结果方向。"), ("output", "输出计量结果", "将【回归结果/代码路径】整理为【表格/图形】，统一变量标签、单位、样本说明并附命令。")]),
        (("data cleaning", "数据清洗", "empirical pipeline", "数据管道", "数据处理"), [("input", "检查数据入口", "检查【项目/数据路径】的原始文件、字段、编码、单位和时间范围，建立输入清单。"), ("run", "执行清洗管道", "运行【脚本/管道入口】处理【数据路径】，记录输入、输出、筛选、缺失和异常。"), ("reproduce", "复现处理结果", "复现【项目路径】生成的【数据/表/图】，核对脚本版本、样本量、变量和输出差异。"), ("handoff", "整理数据交付", "将【处理后数据/项目路径】整理为可复现交付物，补齐字典、来源、命令、质量检查和已知缺口。")]),
        (("infographic", "diagram", "visualization", "科研图表", "图形摘要", "配图", "ppt", "幻灯片"), [("map", "明确内容映射", "根据【数据/文案/论文路径】确定信息层级、变量映射、读者和交付尺寸，再制作。"), ("figure", "制作科研图表", "根据【结果/数据路径】制作【图表/机制图/技术路线图】，保持单位、样本、图例和证据边界准确。"), ("reference", "按参考图改造", "参考【图片路径】，保留【必须保留元素】，修改【目标区域/内容】，输出【格式/尺寸】。"), ("compare", "比较交付方向", "为【内容】生成【数量】个视觉方向，比较信息层级、可读性和适用场景，推荐一个方案。")]),
        (("literature", "文献阅读", "文献检索", "deep research", "研究设计", "证据矩阵"), [("search", "设计检索式", "围绕【研究问题】制定数据库检索式和筛选标准，输出检索记录。"), ("read", "深读单篇文献", "阅读【论文路径/DOI/网址】，提取问题、机制、数据、方法、结论和局限，区分原文与判断。"), ("matrix", "建立证据矩阵", "根据【文献目录/材料路径】建立问题、样本、方法、结论和证据强度矩阵。"), ("memo", "形成研究备忘录", "根据【已核验文献和材料】形成【主题】备忘录，列出争议、证据缺口和下一步检索。")]),
    ]
    for signals, rows in profiles:
        if any(signal in hay for signal in signals):
            return rows
    return []


def variants(name: str, group: str, description: str = "") -> list[dict[str, str]]:
    rows = specialized_variants(name, description)
    if rows:
        return [{"id": ident, "label": label, "when": label, "prompt": f"${name} {ident}\n\n{prompt}"} for ident, label, prompt in rows]
    presets = {
        "课题基金申请": [("background", "写立项依据", "根据【课题资料】、【政策/指南】和【已核验文献】撰写【立项依据/研究意义】，区分事实、判断和待核验内容。"), ("scheme", "搭研究方案", "围绕【核心科学问题】组织【研究目标、研究内容、技术路线、创新点和风险控制】，标注各项依据。"), ("review", "申报前审查", "审查【申请书路径】，对照【申报指南/评审标准】检查科学问题、创新性、可行性、工作基础、预算、格式和证据边界，按优先级输出修改任务。"), ("outline", "拆解写作任务", "把【申请书大纲/材料路径】拆成写作单元，分配目标字数、论证任务、证据来源、图表和前置依赖。")],
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
    parser.add_argument("--install-root", action="append", type=parse_root, help="安装目标 ENV=/absolute/path；默认使用该环境传入的第一个 root")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preserve", type=Path)
    args = parser.parse_args()
    root_groups: dict[str, list[Path]] = {}
    for env, root in args.root:
        root_groups.setdefault(env, []).append(root)
    install_roots = {env: roots[0] for env, roots in root_groups.items() if roots}
    for env, root in args.install_root or []:
        install_roots[env] = root
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
        previous_category = previous.get("category")
        group = category(row["name"], row["description"])
        record = dict(previous)
        record.update(row)
        record["category"] = group
        record["descriptionZh"] = description_zh(previous, row["name"], group)
        record["environments"] = sorted({x["environment"] for x in row["locations"]})
        record["locations"] = sorted(row["locations"], key=lambda x: (x["environment"], x["path"]))
        record["environmentCount"] = len(record["environments"])
        record["overlap"] = record["environmentCount"] > 1
        record["featured"] = bool(previous.get("featured", False))
        record["trigger"] = previous.get("trigger") or f"用 `{ident}`"
        record["scenario"] = scenario_for(group) if previous_category != group or not previous.get("scenario") else previous["scenario"]
        record["keywords"] = previous.get("keywords") or f"{ident} {row['description']} {group}"
        needs_prompt_refresh = previous_category != group or previous.get("promptSchemaVersion") != "atlas-3"
        record["prompt"] = base_prompt(ident, row["description"], group) if needs_prompt_refresh or not previous.get("prompt") else previous["prompt"]
        record["variants"] = variants(ident, group, row["description"]) if needs_prompt_refresh or not previous.get("variants") else previous["variants"]
        record["promptSchemaVersion"] = "atlas-3"
        records.append(record)
    env_counts = {env: sum(env in r["environments"] for r in records) for env in root_groups}
    data = {
        "generatedAt": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "environmentOrder": list(root_groups),
        "roots": {env: [str(root) for root in env_roots] for env, env_roots in root_groups.items()},
        "installRoots": {env: str(install_roots[env]) for env in root_groups if env in install_roots},
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
