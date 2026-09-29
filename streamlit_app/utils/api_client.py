import httpx
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def request_headers() -> dict[str, str]:
    return {"X-Demo-Access-Secret": os.getenv("DEMO_ACCESS_SECRET", "")}


async def post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(f"{API_BASE_URL}{path}", json=payload, headers=request_headers())
        resp.raise_for_status()
        return resp.json()


async def get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{API_BASE_URL}{path}", params=params, headers=request_headers())
        resp.raise_for_status()
        return resp.json()


def post_sync(path: str, payload: dict) -> dict:
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(f"{API_BASE_URL}{path}", json=payload, headers=request_headers())
        resp.raise_for_status()
        return resp.json()


def get_sync(path: str, params: dict | None = None) -> dict:
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(f"{API_BASE_URL}{path}", params=params, headers=request_headers())
        resp.raise_for_status()
        return resp.json()
