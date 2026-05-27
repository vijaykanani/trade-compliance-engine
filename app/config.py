from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DecisionRules.io
    decision_rules_api_key: str = ""
    decision_rules_base_url: str = "https://api.decisionrules.io"

    # Rule IDs
    dr_rule_id_pre_trade_corporate: str = ""
    dr_rule_id_pre_trade_usa: str = ""
    dr_rule_id_pre_trade_emea: str = ""
    dr_rule_id_post_trade_corporate: str = ""
    dr_rule_id_post_trade_usa: str = ""
    dr_rule_id_post_trade_emea: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "dev-secret-key"

    # Database
    database_url: str = "sqlite+aiosqlite:///./compliance.db"

    # Streamlit
    api_base_url: str = "http://localhost:8000"

    # Fallback to local rules if DecisionRules not configured
    use_local_rules_fallback: bool = True

    # Alerts
    alert_email: str = ""
    slack_webhook_url: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def decision_rules_configured(self) -> bool:
        return bool(self.decision_rules_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
