"""Lightweight rule-based translation helpers.

This module intentionally implements a deterministic, dependency-free mock translator
to satisfy the bilingual requirement without relying on heavyweight external models.
It covers a curated vocabulary tailored to the healthcare knowledge base scenario.
"""

from __future__ import annotations

import re

from app.config import Settings, get_settings

EN_TO_JA_MULTIWORD = {
    "type 2 diabetes": "2型糖尿病",
    "blood glucose": "血糖",
    "clinical guideline": "臨床ガイドライン",
    "lifestyle modification": "生活習慣の改善",
}

EN_TO_JA_SINGLEWORD = {
    "guideline": "ガイドライン",
    "guidelines": "ガイドライン",
    "patient": "患者",
    "patients": "患者",
    "management": "管理",
    "therapy": "療法",
    "treatment": "治療",
    "insulin": "インスリン",
    "recommendation": "推奨事項",
    "recommendations": "推奨事項",
    "monitoring": "モニタリング",
    "lifestyle": "生活習慣",
    "medication": "薬物療法",
    "diet": "食事",
    "exercise": "運動",
    "risk": "リスク",
    "assessment": "評価",
    "care": "ケア",
    "clinical": "臨床",
    "evidence": "エビデンス",
}

JA_TO_EN_MULTIWORD = {v: k for k, v in EN_TO_JA_MULTIWORD.items()}
JA_TO_EN_SINGLEWORD = {
    "ガイドライン": "guideline",
    "患者": "patient",
    "管理": "management",
    "療法": "therapy",
    "治療": "treatment",
    "インスリン": "insulin",
    "推奨事項": "recommendations",
    "モニタリング": "monitoring",
    "生活習慣": "lifestyle",
    "薬物療法": "medication",
    "食事": "diet",
    "運動": "exercise",
    "リスク": "risk",
    "評価": "assessment",
    "ケア": "care",
    "臨床": "clinical",
    "エビデンス": "evidence",
    "血糖": "blood glucose",
    "2型糖尿病": "type 2 diabetes",
}


class TranslationService:
    """Provides minimal deterministic translation behaviour for en/ja pairs."""

    def __init__(self, _: Settings | None = None):
        # Settings retained for future extension and to keep signature consistent.
        self.settings = get_settings()

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if not text:
            return text
        if source_language == target_language:
            return text
        key = (source_language, target_language)
        if key == ("en", "ja"):
            return _translate_en_to_ja(text)
        if key == ("ja", "en"):
            return _translate_ja_to_en(text)
        raise ValueError(f"Unsupported translation pair: {source_language}->{target_language}")


def _translate_en_to_ja(text: str) -> str:
    output = text
    for phrase, replacement in EN_TO_JA_MULTIWORD.items():
        output = re.sub(phrase, replacement, output, flags=re.IGNORECASE)

    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        lower = word.lower()
        return EN_TO_JA_SINGLEWORD.get(lower, word)

    return re.sub(r"[A-Za-z]+", replace_word, output)


def _translate_ja_to_en(text: str) -> str:
    output = text
    for phrase, replacement in JA_TO_EN_MULTIWORD.items():
        output = output.replace(phrase, replacement)

    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        return JA_TO_EN_SINGLEWORD.get(word, word)

    return re.sub(r"[一-龯ぁ-んァ-ンー]+", replace_word, output)

