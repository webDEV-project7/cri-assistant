import re
import unicodedata

from app.prompts import SYSTEM_PROMPT


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        text.lower(),
    ).strip()


PROMPT = normalize(SYSTEM_PROMPT)


def test_prompt_identifies_cri_assistant():
    assert "cri assistant" in PROMPT
    assert "guelmim oued noun" in PROMPT


def test_prompt_requires_documentary_grounding():
    assert "contexte documentaire" in PROMPT
    assert "n invente" in PROMPT
    assert "documents officiels" in PROMPT


def test_prompt_forbids_internal_technical_vocabulary():
    assert "terme informatique interne" in PROMPT


def test_prompt_forbids_urls_in_generated_answer():
    assert "ne redige aucune url dans la reponse" in PROMPT


def test_prompt_forbids_guaranteeing_administrative_outcome():
    assert (
        "ne garantis jamais qu un projet sera accepte "
        "autorise ou eligible"
    ) in PROMPT


def test_prompt_requires_complete_official_conditions():
    assert (
        "la concision ne doit jamais supprimer "
        "une condition officielle"
    ) in PROMPT