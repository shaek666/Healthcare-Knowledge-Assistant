from langdetect import DetectorFactory, detect

supportedLanguages = {"en", "ja"}
DetectorFactory.seed = 0


def detectLanguage(text: str) -> str:
    cleanedText = (text or "").strip()
    if not cleanedText:
        raise ValueError("Cannot detect language of empty content.")
    detectedLanguage = detect(cleanedText)
    if detectedLanguage not in supportedLanguages:
        raise ValueError(f"Unsupported language detected: {detectedLanguage}")
    return detectedLanguage

