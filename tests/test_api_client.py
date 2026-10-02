import httpx
import pytest

from streamlit_app.utils import api_client


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://api.test/x")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    responses: list = []
    calls: int = 0

    def __init__(self, timeout: float = 15.0):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _next(self):
        type(self).calls += 1
        item = type(self).responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def get(self, *args, **kwargs):
        return self._next()

    def post(self, *args, **kwargs):
        return self._next()


@pytest.fixture
def fake_client(monkeypatch):
    FakeClient.responses = []
    FakeClient.calls = 0
    monkeypatch.setattr(api_client.httpx, "Client", FakeClient)
    monkeypatch.setattr(api_client.time, "sleep", lambda _seconds: None)
    return FakeClient


def test_get_sync_retries_through_cold_start_bad_gateways(fake_client):
    fake_client.responses = [
        FakeResponse(502),
        FakeResponse(503),
        FakeResponse(200, {"status": "ok"}),
    ]

    assert api_client.get_sync("/health") == {"status": "ok"}
    assert fake_client.calls == 3


def test_get_sync_does_not_retry_client_errors(fake_client):
    fake_client.responses = [FakeResponse(403)]

    with pytest.raises(httpx.HTTPStatusError):
        api_client.get_sync("/rules/")
    assert fake_client.calls == 1


def test_get_sync_retries_transport_errors(fake_client):
    fake_client.responses = [
        httpx.ConnectError("connection refused"),
        FakeResponse(200, {"ok": True}),
    ]

    assert api_client.get_sync("/x") == {"ok": True}
    assert fake_client.calls == 2


def test_post_sync_gives_up_after_max_attempts(fake_client, monkeypatch):
    monkeypatch.setattr(api_client, "MAX_ATTEMPTS", 3)
    fake_client.responses = [FakeResponse(502), FakeResponse(502), FakeResponse(502)]

    with pytest.raises(httpx.HTTPStatusError):
        api_client.post_sync("/compliance/stats", {})
    assert fake_client.calls == 3
