import asyncio
import os
import time

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT_SECONDS", "15"))
MAX_ATTEMPTS = int(os.getenv("API_MAX_ATTEMPTS", "12"))
RETRY_DELAY = float(os.getenv("API_RETRY_DELAY_SECONDS", "5"))
RETRYABLE_STATUS_CODES = {502, 503, 504}


def request_headers() -> dict[str, str]:
    return {"X-Demo-Access-Secret": os.getenv("DEMO_ACCESS_SECRET", "")}


def _is_retryable(exc: Exception) -> bool:
    """Cold starts on free hosting surface as 502/503/504 or transport errors."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return isinstance(exc, httpx.TransportError)


async def post(path: str, payload: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(f"{API_BASE_URL}{path}", json=payload, headers=request_headers())
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
    raise last_error  # type: ignore[misc]


async def get(path: str, params: dict | None = None) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.get(f"{API_BASE_URL}{path}", params=params, headers=request_headers())
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
    raise last_error  # type: ignore[misc]


def post_sync(path: str, payload: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.post(f"{API_BASE_URL}{path}", json=payload, headers=request_headers())
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
    raise last_error  # type: ignore[misc]


def get_sync(path: str, params: dict | None = None) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.get(f"{API_BASE_URL}{path}", params=params, headers=request_headers())
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            if not _is_retryable(exc):
                raise
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY)
    raise last_error  # type: ignore[misc]
