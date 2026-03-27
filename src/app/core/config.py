from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "SUPPORT"
    jira_poll_interval_seconds: int = 300
    jira_lookback_minutes: int = 30

    database_url: str = "sqlite:///./ai_support.db"

    llm_provider: str = "local"
    llm_local_backend: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:14b-instruct"
    llm_timeout_seconds: int = 120
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: str = ""
    demo_agent_name: str = "Gael"
    demo_agent_style: str = (
        "Professional, calm, concise. Start by acknowledging the issue. "
        "State the most likely direction without overstating certainty. "
        "Ask only the missing data that matters. Prefer short paragraphs and concrete next steps. "
        "When useful, provide both a likely explanation and prevention guidance."
    )

    enable_jira_comment_publish: bool = False
    enable_scheduler: bool = False
    webhook_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
