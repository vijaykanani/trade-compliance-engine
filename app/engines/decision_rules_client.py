"""
DecisionRules.io API client.

Docs: https://docs.decisionrules.io/api/rule-solver-api
Each rule call: POST /rule/solve/{ruleId}/{version}
Input:  {"data": [{...your input object...}]}
Output: [{...result object...}]
"""
import httpx
import logging
from typing import Any
from app.config import get_settings

logger = logging.getLogger(__name__)


class DecisionRulesClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.decision_rules_base_url
        self.api_key = self.settings.decision_rules_api_key

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def solve(
        self,
        rule_id: str,
        input_data: dict[str, Any],
        version: str = "1",
    ) -> list[dict]:
        """
        Call a single DecisionRules rule and return results.
        Returns empty list on error so callers can fall through to local rules.
        """
        if not self.api_key or not rule_id:
            return []

        url = f"{self.base_url}/rule/solve/{rule_id}/{version}"
        payload = {"data": [input_data]}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("DecisionRules HTTP error %s for rule %s: %s", e.response.status_code, rule_id, e)
        except Exception as e:
            logger.error("DecisionRules call failed for rule %s: %s", rule_id, e)

        return []

    async def solve_many(
        self,
        rule_id: str,
        input_records: list[dict[str, Any]],
        version: str = "1",
    ) -> list[dict]:
        """Batch-solve multiple records against the same rule."""
        if not self.api_key or not rule_id:
            return []

        url = f"{self.base_url}/rule/solve/{rule_id}/{version}"
        payload = {"data": input_records}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error("DecisionRules batch call failed for rule %s: %s", rule_id, e)

        return []
