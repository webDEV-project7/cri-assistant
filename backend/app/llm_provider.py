from __future__ import annotations

from dataclasses import dataclass
import logging
import os
import time
from typing import Any

import httpx


logger = logging.getLogger(__name__)

GROQ_CHAT_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)


@dataclass(frozen=True, slots=True)
class LLMResult:
    content: str
    model: str
    provider: str


def _read_positive_float(
    variable_name: str,
    default: float,
) -> float:
    raw_value = os.getenv(variable_name, str(default))

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return default

    if value <= 0:
        return default

    return value


async def _call_groq(
    *,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> LLMResult:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "La variable GROQ_API_KEY est absente."
        )

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    ).strip()

    if not model:
        raise RuntimeError(
            "La variable GROQ_MODEL est vide."
        )

    timeout_seconds = _read_positive_float(
        "GROQ_TIMEOUT_SECONDS",
        60.0,
    )

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": max(
            float(temperature),
            0.00000001,
        ),
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(
        timeout=timeout_seconds,
        connect=min(10.0, timeout_seconds),
    )

    # Diagnostic Groq : taille de la requête
    total_message_characters = sum(
        len(str(message.get("content", "")))
        for message in messages
        if isinstance(message, dict)
    )

    logger.warning(
        (
            "Groq diagnostic requête | messages=%s "
            "| caractères=%s | max_tokens=%s "
            "| modèle=%s"
        ),
        len(messages),
        total_message_characters,
        max_tokens,
        model,
    )

    request_started_at = time.perf_counter()

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:
        response = await client.post(
            GROQ_CHAT_URL,
            headers=headers,
            json=payload,
        )

        # Diagnostic Groq : erreur HTTP détaillée
        if response.is_error:
            error_detail = response.text[:800]

            try:
                error_payload = response.json()
                error_value = error_payload.get("error")

                if isinstance(error_value, dict):
                    error_detail = (
                        f"type={error_value.get('type')} | "
                        f"code={error_value.get('code')} | "
                        f"message={error_value.get('message')}"
                    )

            except ValueError:
                pass

            logger.warning(
                "Groq diagnostic HTTP %s | %s",
                response.status_code,
                error_detail,
            )

        response.raise_for_status()

    data = response.json()

    request_duration = (
        time.perf_counter()
        - request_started_at
    )

    usage = data.get("usage")

    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
    else:
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

    diagnostic_model = str(
        data.get("model") or model
    ).strip()

    logger.warning(
        (
            "DeepSeek diagnostic reponse | duree=%.3fs "
            "| prompt_tokens=%s | completion_tokens=%s "
            "| total_tokens=%s | modele=%s"
        ),
        request_duration,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        diagnostic_model,
    )

    choices = data.get("choices")

    if not isinstance(choices, list) or not choices:
        raise RuntimeError(
            "Groq n'a retourné aucun choix."
        )

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        raise RuntimeError(
            "La réponse Groq est invalide."
        )

    message = first_choice.get("message")

    if not isinstance(message, dict):
        raise RuntimeError(
            "La réponse Groq ne contient pas de message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "Groq a retourné une réponse vide."
        )

    returned_model = str(
        data.get("model") or model
    ).strip()

    return LLMResult(
        content=content.strip(),
        model=returned_model,
        provider="groq",
    )


async def _call_deepseek(
    *,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> LLMResult:
    api_key = os.getenv(
        "DEEPSEEK_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "La variable DEEPSEEK_API_KEY est absente."
        )

    base_url = os.getenv(
        "DEEPSEEK_BASE_URL",
        "https://api.deepseek.com",
    ).strip().rstrip("/")

    if not base_url:
        raise RuntimeError(
            "La variable DEEPSEEK_BASE_URL est vide."
        )

    model = os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-v4-pro",
    ).strip()

    if not model:
        raise RuntimeError(
            "La variable DEEPSEEK_MODEL est vide."
        )

    timeout_seconds = _read_positive_float(
        "DEEPSEEK_TIMEOUT_SECONDS",
        60.0,
    )

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "thinking": {
            "type": "disabled",
        },
        "temperature": max(
            float(temperature),
            0.00000001,
        ),
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(
        timeout=timeout_seconds,
        connect=min(10.0, timeout_seconds),
    )

    total_message_characters = sum(
        len(str(message.get("content", "")))
        for message in messages
        if isinstance(message, dict)
    )

    logger.warning(
        (
            "DeepSeek diagnostic requete | messages=%s "
            "| caracteres=%s | max_tokens=%s "
            "| modele=%s"
        ),
        len(messages),
        total_message_characters,
        max_tokens,
        model,
    )

    request_started_at = time.perf_counter()

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.is_error:
            logger.warning(
                "DeepSeek diagnostic HTTP %s | %s",
                response.status_code,
                response.text[:800],
            )

        response.raise_for_status()

    data = response.json()

    request_duration = (
        time.perf_counter()
        - request_started_at
    )

    usage = data.get("usage")

    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
    else:
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

    diagnostic_model = str(
        data.get("model") or model
    ).strip()

    logger.warning(
        (
            "DeepSeek diagnostic reponse | duree=%.3fs "
            "| prompt_tokens=%s | completion_tokens=%s "
            "| total_tokens=%s | modele=%s"
        ),
        request_duration,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        diagnostic_model,
    )

    choices = data.get("choices")

    if not isinstance(choices, list) or not choices:
        raise RuntimeError(
            "DeepSeek n'a retourne aucun choix."
        )

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        raise RuntimeError(
            "La reponse DeepSeek est invalide."
        )

    message = first_choice.get("message")

    if not isinstance(message, dict):
        raise RuntimeError(
            "La reponse DeepSeek ne contient pas de message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "DeepSeek a retourne une reponse vide."
        )

    returned_model = str(
        data.get("model") or model
    ).strip()

    return LLMResult(
        content=content.strip(),
        model=returned_model,
        provider="deepseek",
    )

async def _call_ollama(
    *,
    messages: list[dict[str, str]],
    ollama_base_url: str,
    ollama_model: str,
    ollama_context_size: int,
    max_tokens: int,
    temperature: float,
) -> LLMResult:
    payload = {
        "model": ollama_model,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": {
            "temperature": temperature,
            "num_ctx": ollama_context_size,
            "num_predict": max_tokens,
        },
    }

    timeout = httpx.Timeout(
        timeout=300.0,
        connect=10.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        trust_env=False,
    ) as client:
        response = await client.post(
            f"{ollama_base_url}/api/chat",
            json=payload,
        )

        response.raise_for_status()

    data = response.json()
    message = data.get("message")

    if not isinstance(message, dict):
        raise RuntimeError(
            "Ollama n'a pas retourné de message."
        )

    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "Ollama a retourné une réponse vide."
        )

    returned_model = str(
        data.get("model") or ollama_model
    ).strip()

    return LLMResult(
        content=content.strip(),
        model=returned_model,
        provider="ollama",
    )


async def generate_chat_response(
    *,
    messages: list[dict[str, str]],
    ollama_base_url: str,
    ollama_model: str,
    ollama_context_size: int,
    max_response_tokens: int,
    temperature: float = 0.1,
) -> LLMResult:
    primary_provider = os.getenv(
        "LLM_PROVIDER",
        "ollama",
    ).strip().lower()

    fallback_provider = os.getenv(
        "LLM_FALLBACK_PROVIDER",
        "ollama",
    ).strip().lower()

    providers: list[str] = []

    for provider in (
        primary_provider,
        fallback_provider,
    ):
        if provider and provider not in providers:
            providers.append(provider)

    if not providers:
        providers = ["ollama"]

    last_error: Exception | None = None

    for provider in providers:
        try:
            if provider == "deepseek":
                return await _call_deepseek(
                    messages=messages,
                    max_tokens=max_response_tokens,
                    temperature=temperature,
                )

            if provider == "groq":
                return await _call_groq(
                    messages=messages,
                    max_tokens=max_response_tokens,
                    temperature=temperature,
                )

            if provider == "ollama":
                return await _call_ollama(
                    messages=messages,
                    ollama_base_url=ollama_base_url,
                    ollama_model=ollama_model,
                    ollama_context_size=(
                        ollama_context_size
                    ),
                    max_tokens=max_response_tokens,
                    temperature=temperature,
                )

            logger.warning(
                "Fournisseur LLM inconnu ignoré : %s",
                provider,
            )

        except Exception as error:
            last_error = error

            logger.warning(
                "Échec du fournisseur LLM %s : %s",
                provider,
                type(error).__name__,
            )

    raise RuntimeError(
        "Tous les fournisseurs LLM ont échoué."
    ) from last_error