from __future__ import annotations

import math
import re
from pathlib import Path

from .models import Cue
from .srt import read_text


DEFAULT_STOPWORDS = {
    "一个",
    "一些",
    "这个",
    "那个",
    "这些",
    "那些",
    "自己",
    "因为",
    "所以",
    "但是",
    "然后",
    "就是",
    "其实",
    "感觉",
    "可能",
    "应该",
    "比较",
    "如果",
    "不是",
    "没有",
    "可以",
    "需要",
    "还是",
    "现在",
    "之前",
    "之后",
    "下来",
    "起来",
    "里面",
    "这里",
    "那里",
    "这么",
    "这么个",
    "一遍",
    "一下",
    "大家",
    "我们",
    "你们",
    "他们",
    "它们",
    "时候",
    "东西",
    "问题",
    "内容",
    "视频",
    "时间",
    "工具",
    "方式",
    "方案",
    "操作",
    "进行",
    "做法",
    "今天",
    "比如",
    "而是",
    "先别",
    "先做",
    "直接",
    "执行",
    "关注",
    "普通人",
    "也能",
    "做出",
    "记住",
    "玩转",
    "下一",
    "第二",
    "第三",
    "第一",
    "几个",
    "告诉",
    "这三",
    "目标",
    "结构",
    "上线",
    "完美",
    "系统",
    "跟进",
    "用户",
    "介绍",
    "提交",
    "感觉",
    "知道",
    "看到",
    "发现",
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "you",
    "your",
}


DOMAIN_TERMS = [
    "剪映",
    "CapCut",
    "字幕",
    "关键词",
    "高亮",
    "自动字幕",
    "识别字幕",
    "文稿匹配",
    "开源工具",
    "知识库",
    "时间线",
    "草稿",
    "导出",
    "导入",
    "AI",
    "LLM",
    "API",
    "MCP",
    "Codex",
    "ChatGPT",
    "Python",
    "脚本",
    "工作流",
    "自动化",
    "模型",
    "提示词",
    "转写",
    "校对",
    "复盘",
    "需求",
    "方案",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def split_keywords(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，;；|、\n]+", value) if item.strip()]


def load_keywords(
    cues: list[Cue],
    *,
    keywords: str | None = None,
    keywords_file: str | None = None,
    auto_keyword_limit: int = 24,
) -> list[str]:
    selected: list[str] = []
    if keywords:
        selected.extend(split_keywords(keywords))
    if keywords_file:
        for line in read_text(Path(keywords_file)).splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                selected.extend(split_keywords(line))

    if not selected:
        selected = auto_keywords(cues, limit=auto_keyword_limit)

    seen: set[str] = set()
    result: list[str] = []
    for keyword in selected:
        keyword = keyword.strip()
        if not keyword:
            continue
        key = normalize_text(keyword)
        if key and key not in seen:
            seen.add(key)
            result.append(keyword)
    return sorted(result, key=len, reverse=True)


def auto_keywords(cues: list[Cue], limit: int) -> list[str]:
    full_text = "\n".join(cue.text for cue in cues)
    scores: dict[str, float] = {}
    total_len = max(len(full_text), 1)

    for term in DOMAIN_TERMS:
        count = len(re.findall(re.escape(term), full_text, flags=re.IGNORECASE))
        if count:
            scores[term] = scores.get(term, 0.0) + count * (4.0 + min(len(term), 8))

    for token in re.findall(r"[A-Za-z][A-Za-z0-9_+#.-]{1,}", full_text):
        lowered = token.lower()
        if lowered in DEFAULT_STOPWORDS:
            continue
        scores[token] = scores.get(token, 0.0) + 3.0 + math.log2(len(token) + 1)

    cjk_runs = re.findall(r"[\u4e00-\u9fff]{2,}", full_text)
    for run in cjk_runs:
        for n in range(2, min(8, len(run)) + 1):
            for i in range(0, len(run) - n + 1):
                gram = run[i : i + n]
                if gram in DEFAULT_STOPWORDS:
                    continue
                if any(stop in gram for stop in ("这个", "那个", "然后", "就是", "可以", "没有")):
                    continue
                count = full_text.count(gram)
                if count < 2:
                    continue
                density_boost = min(3.0, count * 400 / total_len)
                scores[gram] = scores.get(gram, 0.0) + count * (n**1.35) + density_boost

    ranked = sorted(scores.items(), key=lambda item: (item[1], len(item[0])), reverse=True)
    selected: list[str] = []
    for term, score in ranked:
        if score <= 0:
            continue
        norm = normalize_text(term)
        if len(norm) < 2:
            continue
        if any(norm in normalize_text(existing) for existing in selected):
            continue
        if any(normalize_text(existing) in norm and len(term) <= len(existing) + 1 for existing in selected):
            continue
        selected.append(term)
        if len(selected) >= limit:
            break
    return selected
