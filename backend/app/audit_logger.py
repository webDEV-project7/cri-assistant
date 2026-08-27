from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import UTC, datetime
from typing import Any, Mapping


AUDIT_LOGGER_NAME = "cri.audit"

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "session",
    "session_token",
    "jwt",
    "document_content",
    "file_content",
    "message",
    "prompt",
    "analysis_context",
}

MAX_DETAIL_STRING_LENGTH = 256


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(
        AUDIT_LOGGER_NAME
    )

    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(
            sys.stdout
        )

        handler.setFormatter(
            logging.Formatter(
                "%(message)s"
            )
        )

        logger.addHandler(handler)

    return logger


logger = _configure_logger()


def new_request_id() -> str:
    return str(uuid.uuid4())


def _sanitize_value(
    value: Any,
) -> str | int | float | bool | None:
    if value is None:
        return None

    if isinstance(
        value,
        (bool, int, float),
    ):
        return value

    text = str(value)

    if len(text) > MAX_DETAIL_STRING_LENGTH:
        return (
            text[
                :MAX_DETAIL_STRING_LENGTH
            ]
            + "..."
        )

    return text


def sanitize_details(
    details: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not details:
        return {}

    sanitized: dict[str, Any] = {}

    for key, value in details.items():
        normalized_key = str(
            key
        ).strip()

        if not normalized_key:
            continue

        if (
            normalized_key.casefold()
            in SENSITIVE_KEYS
        ):
            continue

        sanitized[normalized_key] = (
            _sanitize_value(value)
        )

    return sanitized


def build_audit_payload(
    *,
    event: str,
    status: str,
    endpoint: str | None = None,
    user_id: Any = None,
    request_id: str | None = None,
    duration_ms: int | float | None = None,
    http_status: int | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    event_name = (
        str(event).strip().upper()
        or "UNKNOWN"
    )

    status_name = (
        str(status).strip().lower()
        or "unknown"
    )

    payload: dict[str, Any] = {
        "log_type": "audit",
        "timestamp": (
            datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "event": event_name,
        "status": status_name,
        "request_id": (
            request_id
            or new_request_id()
        ),
    }

    if endpoint:
        payload["endpoint"] = str(
            endpoint
        )

    if user_id is not None:
        payload["user_id"] = str(
            user_id
        )

    if duration_ms is not None:
        payload["duration_ms"] = round(
            max(
                0.0,
                float(duration_ms),
            ),
            2,
        )

    if http_status is not None:
        payload["http_status"] = int(
            http_status
        )

    safe_details = sanitize_details(
        details
    )

    if safe_details:
        payload["details"] = safe_details

    return payload


def audit_event(
    *,
    event: str,
    status: str,
    endpoint: str | None = None,
    user_id: Any = None,
    request_id: str | None = None,
    duration_ms: int | float | None = None,
    http_status: int | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_audit_payload(
        event=event,
        status=status,
        endpoint=endpoint,
        user_id=user_id,
        request_id=request_id,
        duration_ms=duration_ms,
        http_status=http_status,
        details=details,
    )

    line = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    if payload["status"] in {
        "error",
        "failed",
        "failure",
    }:
        logger.warning(line)
    else:
        logger.info(line)

    return payload