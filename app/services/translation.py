import re

from app.config import Settings, getSettings

enToJaMultiword = {
    "type 2 diabetes": "2\u578b\u7cd6\u5c3f\u75c5",
    "blood glucose": "\u8840\u7cd6",
    "clinical guideline": "\u81e8\u5e8a\u30ac\u30a4\u30c9\u30e9\u30a4\u30f3",
    "lifestyle modification": "\u751f\u6d3b\u7fd2\u6163\u306e\u6539\u5584",
}

enToJaSingleword = {
    "guideline": "\u30ac\u30a4\u30c9\u30e9\u30a4\u30f3",
    "guidelines": "\u30ac\u30a4\u30c9\u30e9\u30a4\u30f3",
    "patient": "\u60a3\u8005",
    "patients": "\u60a3\u8005",
    "management": "\u7ba1\u7406",
    "therapy": "\u7642\u6cd5",
    "treatment": "\u6cbb\u7642",
    "insulin": "\u30a4\u30f3\u30b9\u30ea\u30f3",
    "recommendation": "\u63a8\u5968\u4e8b\u9805",
    "recommendations": "\u63a8\u5968\u4e8b\u9805",
    "monitoring": "\u30e2\u30cb\u30bf\u30ea\u30f3\u30b0",
    "lifestyle": "\u751f\u6d3b\u7fd2\u6163",
    "medication": "\u85ac\u7269\u7642\u6cd5",
    "diet": "\u98df\u4e8b",
    "exercise": "\u904b\u52d5",
    "risk": "\u30ea\u30b9\u30af",
    "assessment": "\u8a55\u4fa1",
    "care": "\u30b1\u30a2",
    "clinical": "\u81e8\u5e8a",
    "evidence": "\u30a8\u30d3\u30c7\u30f3\u30b9",
}

jaToEnMultiword = {value: key for key, value in enToJaMultiword.items()}
jaToEnSingleword = {
    "\u30ac\u30a4\u30c9\u30e9\u30a4\u30f3": "guideline",
    "\u60a3\u8005": "patient",
    "\u7ba1\u7406": "management",
    "\u7642\u6cd5": "therapy",
    "\u6cbb\u7642": "treatment",
    "\u30a4\u30f3\u30b9\u30ea\u30f3": "insulin",
    "\u63a8\u5968\u4e8b\u9805": "recommendations",
    "\u30e2\u30cb\u30bf\u30ea\u30f3\u30b0": "monitoring",
    "\u751f\u6d3b\u7fd2\u6163": "lifestyle",
    "\u85ac\u7269\u7642\u6cd5": "medication",
    "\u98df\u4e8b": "diet",
    "\u904b\u52d5": "exercise",
    "\u30ea\u30b9\u30af": "risk",
    "\u8a55\u4fa1": "assessment",
    "\u30b1\u30a2": "care",
    "\u81e8\u5e8a": "clinical",
    "\u30a8\u30d3\u30c7\u30f3\u30b9": "evidence",
    "\u8840\u7cd6": "blood glucose",
    "2\u578b\u7cd6\u5c3f\u75c5": "type 2 diabetes",
}


class TranslationService:
    def __init__(self, _: Settings | None = None):
        self.settings = getSettings()

    def translate(self, text: str, sourceLanguage: str, targetLanguage: str) -> str:
        if not text:
            return text
        if sourceLanguage == targetLanguage:
            return text
        languageKey = (sourceLanguage, targetLanguage)
        if languageKey == ("en", "ja"):
            return translateEnToJa(text)
        if languageKey == ("ja", "en"):
            return translateJaToEn(text)
        raise ValueError(f"Unsupported translation pair: {sourceLanguage}->{targetLanguage}")


def translateEnToJa(text: str) -> str:
    outputText = text
    for phrase, replacement in enToJaMultiword.items():
        outputText = re.sub(phrase, replacement, outputText, flags=re.IGNORECASE)

    def replaceWord(match: re.Match[str]) -> str:
        word = match.group(0)
        lowerWord = word.lower()
        return enToJaSingleword.get(lowerWord, word)

    return re.sub(r"[A-Za-z]+", replaceWord, outputText)


def translateJaToEn(text: str) -> str:
    outputText = text
    for phrase, replacement in jaToEnMultiword.items():
        outputText = outputText.replace(phrase, replacement)

    def replaceWord(match: re.Match[str]) -> str:
        word = match.group(0)
        return jaToEnSingleword.get(word, word)

    return re.sub(r"[\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f3\u30fc]+", replaceWord, outputText)

