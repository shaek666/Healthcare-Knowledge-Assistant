import threading
from typing import Dict, FrozenSet, Tuple
from deep_translator import GoogleTranslator

SUPPORTED_LANGUAGE_PAIRS: FrozenSet[Tuple[str, str]] = frozenset({("en", "ja"), ("ja", "en")})

class TranslationService:
    def __init__(self) -> None:
        self._translator_cache: Dict[Tuple[str, str], GoogleTranslator] = {}
        self._cache_lock = threading.Lock()

    def translate(self, text: str, sourceLanguage: str, targetLanguage: str) -> str:
        if not text:
            return text
        source = (sourceLanguage or "").lower()
        target = (targetLanguage or "").lower()
        if source == target:
            return text
        pair = (source, target)
        if pair not in SUPPORTED_LANGUAGE_PAIRS:
            raise ValueError(f"Unsupported translation pair: {sourceLanguage}->{targetLanguage}")
        translator = self._get_translator(pair)
        return translator.translate(text)

    def _get_translator(self, pair: Tuple[str, str]) -> GoogleTranslator:
        with self._cache_lock:
            translator = self._translator_cache.get(pair)
            if translator is None:
                source, target = pair
                translator = GoogleTranslator(source=source, target=target)
                self._translator_cache[pair] = translator
            return translator