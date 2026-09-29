import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
DEFAULT_OVERRIDE_PATH = APP_DIR / "override_history.json"


def load_overrides(path: str | Path | None = None) -> list[dict[str, Any]]:
    file_path = Path(path) if path is not None else DEFAULT_OVERRIDE_PATH
    if not file_path.exists():
        file_path.write_text("[]", encoding="utf-8")
        return []

    try:
        with file_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_overrides(entries: list[dict[str, Any]], path: str | Path | None = None) -> None:
    file_path = Path(path) if path is not None else DEFAULT_OVERRIDE_PATH
    file_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def record_override(
    breach_id: str,
    decision: str,
    notes: str,
    user: str = "local-admin",
    path: str | Path | None = None,
) -> dict[str, Any]:
    file_path = Path(path) if path is not None else DEFAULT_OVERRIDE_PATH
    overrides = load_overrides(file_path)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "breach_id": breach_id,
        "decision": decision,
        "notes": notes,
        "user": user,
    }
    overrides.append(record)
    save_overrides(overrides, file_path)
    return record
