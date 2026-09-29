import json
import hmac
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from streamlit_app.rule_store import create_rule, delete_rule, load_rule_registry, save_rule_registry

router = APIRouter(prefix="/rules", tags=["Rules"])


def require_rule_admin(x_rule_admin_key: str = Header(default="", alias="X-Rule-Admin-Key")):
    expected_key = get_settings().rule_admin_api_key
    if not expected_key or not hmac.compare_digest(x_rule_admin_key, expected_key):
        raise HTTPException(status_code=403, detail="Rule administration is not authorized")


class RuleCreatePayload(BaseModel):
    jurisdiction: str
    name: str
    regulation: str
    severity: str = "WARNING"
    phase: str = "PRE"
    notes: str = ""


@router.get("/", summary="List available rule sets")
async def list_rule_sets():
    registry = load_rule_registry()
    return registry


@router.get("/{jurisdiction}", summary="Get rules for a specific jurisdiction or market")
async def get_jurisdiction_rules(jurisdiction: str):
    registry = load_rule_registry()
    key = jurisdiction.lower()
    if key not in registry:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return {"jurisdiction": key, "rules": registry[key].get("rules", [])}


@router.post("/", summary="Create a new rule in the app registry", dependencies=[Depends(require_rule_admin)])
async def create_rule_api(payload: RuleCreatePayload):
    registry = load_rule_registry()
    created = create_rule(
        jurisdiction=payload.jurisdiction,
        name=payload.name,
        regulation=payload.regulation,
        severity=payload.severity,
        phase=payload.phase,
        notes=payload.notes,
        registry=registry,
        registry_path="streamlit_app/rule_registry.json",
        audit_path="streamlit_app/rule_audit.json",
    )
    return {"status": "created", "rule": created}


@router.delete("/{jurisdiction}/{rule_id}", summary="Delete a rule from the app registry", dependencies=[Depends(require_rule_admin)])
async def delete_rule_api(jurisdiction: str, rule_id: str):
    registry = load_rule_registry()
    deleted = delete_rule(
        jurisdiction=jurisdiction,
        rule_id=rule_id,
        registry=registry,
        registry_path="streamlit_app/rule_registry.json",
        audit_path="streamlit_app/rule_audit.json",
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted", "rule_id": rule_id}


@router.get("/export", summary="Export current rule registry")
async def export_rule_registry():
    return load_rule_registry()


@router.post("/import", summary="Import a complete registry payload", dependencies=[Depends(require_rule_admin)])
async def import_rule_registry(payload: dict):
    save_rule_registry(payload, "streamlit_app/rule_registry.json")
    return {"status": "imported", "groups": list(payload.keys())}


@router.get("/decision-rules-config/{name}", summary="Get file-based rule config")
async def get_dr_config(name: str):
    allowed = {"pre_trade_corporate", "pre_trade_usa", "pre_trade_emea", "post_trade_corporate", "post_trade_usa", "post_trade_emea"}
    if name not in allowed:
        raise HTTPException(status_code=404, detail="Config not found")

    rules_dir = os.path.join(os.path.dirname(__file__), "../../decision_rules_config")
    path = os.path.join(rules_dir, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"error": "Config file not yet generated"}
