"""Language detection utilities."""

from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

SUPPORTED_LANGUAGES = {"en", "ja"}

# Ensure deterministic results.
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """Detect the predominant language code of the given text."""

    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Cannot detect language of empty content.")

    try:
        detected = detect(cleaned)
    except LangDetectException as exc:  # pragma: no cover - passthrough for clarity
        raise ValueError("Unable to detect language for the provided text.") from exc

    if detected not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language detected: {detected}")

    return detected

