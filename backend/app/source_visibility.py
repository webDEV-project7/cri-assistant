from __future__ import annotations

import os
import re
import unicodedata
from typing import Any
from urllib.parse import urlparse


DEFAULT_OFFICIAL_DOMAINS = (
    "cri-invest.ma",
    "guelmiminvest.ma",
    "adala.justice.gov.ma",
)


CONVERSATIONAL_MESSAGES = {
    "bonjour",
    "bonsoir",
    "salut",
    "hello",
    "hi",
    "salam",
    "salam alaykoum",
    "السلام عليكم",
    "مرحبا",
    "شكرا",
    "شكرا لك",
    "merci",
    "merci beaucoup",
    "au revoir",
    "bye",
    "ok",
    "okay",
    "d accord",
}


CONVERSATIONAL_PREFIXES = (
    "bonjour ",
    "bonsoir ",
    "salut ",
    "merci ",
    "salam ",
    "السلام عليكم ",
    "شكرا ",
)


TRANSFORMATION_PREFIXES = (
    "traduis ",
    "traduire ",
    "traduisez ",
    "translate ",
    "reformule ",
    "reformuler ",
    "reformulez ",
    "corrige ",
    "corriger ",
    "corrigez ",
    "resume ",
    "resumer ",
    "résume ",
    "résumer ",
    "ترجم ",
    "أعد صياغة ",
)


CLARIFICATION_PREFIXES = (
    "veuillez préciser",
    "veuillez preciser",
    "souhaitez-vous",
    "souhaitez vous",
    "quelle procédure",
    "quelle procedure",
    "quel type",
    "laquelle souhaitez-vous",
    "laquelle souhaitez vous",
    "votre demande couvre plusieurs",
    "يرجى تحديد",
    "ما المسطرة",
    "ما الإجراء",
    "هل ترغب",
    "أي مسطرة",
    "أي إجراء",
    "please specify",
    "which procedure",
    "which type",
    "would you like",
    "your request covers several",
)


def _normaliser(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = re.sub(
        r"[^\w\u0600-\u06ff]+",
        " ",
        normalized,
    )

    return " ".join(normalized.split())


def _source_url(source: Any) -> str:
    if isinstance(source, dict):
        value = source.get("url", "")
    else:
        value = getattr(source, "url", "")

    if not isinstance(value, str):
        return ""

    return value.strip()


def _official_domains() -> tuple[str, ...]:
    configured = os.getenv(
        "OFFICIAL_SOURCE_DOMAINS",
        "",
    ).strip()

    if not configured:
        return DEFAULT_OFFICIAL_DOMAINS

    values = tuple(
        item.strip().lower()
        for item in configured.split(",")
        if item.strip()
    )

    return values or DEFAULT_OFFICIAL_DOMAINS


def _is_official_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = (parsed.hostname or "").lower()

    if not hostname:
        return False

    return any(
        hostname == domain
        or hostname.endswith(f".{domain}")
        for domain in _official_domains()
    )


def _is_conversational_or_transformation(
    user_message: str,
) -> bool:
    normalized = _normaliser(user_message)

    if not normalized:
        return True

    if normalized in CONVERSATIONAL_MESSAGES:
        return True

    words = normalized.split()

    if (
        len(words) <= 8
        and normalized.startswith(
            CONVERSATIONAL_PREFIXES
        )
    ):
        return True

    return normalized.startswith(
        TRANSFORMATION_PREFIXES
    )


def _is_clarification(
    assistant_response: str,
) -> bool:
    normalized = _normaliser(
        assistant_response
    )

    if normalized.startswith(
        CLARIFICATION_PREFIXES
    ):
        return True

    contains_question = (
        "?" in assistant_response
        or "؟" in assistant_response
    )

    contains_numbered_choices = bool(
        re.search(
            r"(?m)^\s*[1-4][.)]?\s+",
            assistant_response,
        )
    )

    return (
        contains_question
        and contains_numbered_choices
        and len(assistant_response) < 1200
    )


def filter_visible_sources(
    *,
    user_message: str,
    assistant_response: str,
    sources: list[Any],
) -> list[Any]:
    if not sources:
        return []

    if _is_conversational_or_transformation(
        user_message
    ):
        return []

    if _is_clarification(
        assistant_response
    ):
        return []

    visible_sources: list[Any] = []
    seen_urls: set[str] = set()

    for source in sources:
        url = _source_url(source)

        if not _is_official_url(url):
            continue

        normalized_url = url.rstrip("/").lower()

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)
        visible_sources.append(source)

        if len(visible_sources) == 3:
            break

    return visible_sources