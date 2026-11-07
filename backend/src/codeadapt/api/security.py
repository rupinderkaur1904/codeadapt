"""HTTP hardening for the API (ADR-040): response security headers and a request-body limit.

Both are plain ASGI middleware so they also cover responses produced outside FastAPI's
routing (Host-check rejections, 404s, unhandled errors).
"""

from __future__ import annotations

import json
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# The API answers JSON only; its responses carry private learner data.
API_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cache-control", b"no-store"),
    (b"cross-origin-resource-policy", b"same-origin"),
)
# A JSON API needs no content at all. The interactive docs (dev and test only) load scripts
# and styles from a CDN, so they are exempt from this policy.
API_CSP = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
HSTS = (b"strict-transport-security", b"max-age=31536000")
DOCS_PATHS = ("/api/docs", "/api/redoc")
ERROR_BASE = "https://codeadapt.dev/errors/"
PROBLEM_JSON = "application/problem+json"
MAX_BODY_BYTES = 1024 * 1024  # submissions are capped at 64 KiB (schemas.MAX_SOURCE_BYTES)


class SecurityHeaders:
    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app, self.hsts = app, hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        docs = str(scope.get("path", "")).startswith(DOCS_PATHS)

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower() not in {name for name, _ in API_HEADERS}
                ]
                headers += list(API_HEADERS)
                if not docs:
                    headers.append(API_CSP)
                if self.hsts:
                    headers.append(HSTS)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, with_headers)


class BodyLimit:
    """Refuse request bodies over ``limit`` bytes with 413, whether or not Content-Length
    is declared (chunked bodies are counted as they arrive, and never buffered past the
    limit)."""

    def __init__(self, app: ASGIApp, *, limit: int = MAX_BODY_BYTES) -> None:
        self.app, self.limit = app, limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    await _reject(send, 400, "invalid-request", "Invalid Content-Length")
                    return
                if declared > self.limit:
                    await _reject(send, 413, "payload-too-large", "Request body too large")
                    return
        # Read the body (at most `limit` bytes) before the app sees it, then replay it.
        # Raising from inside the app's receive would surface as a 400 parse error instead.
        chunks: list[bytes] = []
        received = 0
        more = True
        while more:
            message = await receive()
            if message["type"] != "http.request":  # client went away
                return
            body = message.get("body", b"")
            received += len(body)
            if received > self.limit:
                await _reject(send, 413, "payload-too-large", "Request body too large")
                return
            chunks.append(body)
            more = message.get("more_body", False)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


async def _reject(send: Send, status: int, slug: str, title: str) -> None:
    body: dict[str, Any] = {"type": ERROR_BASE + slug, "title": title, "status": status}
    payload = json.dumps(body).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", PROBLEM_JSON.encode()),
                (b"content-length", str(len(payload)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})
