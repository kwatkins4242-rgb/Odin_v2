"""
Brain stack settings — single source of truth.
Ubuntu / Linux paths only. All secrets come from .env (never hardcode keys here).
"""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"


class Settings(BaseSettings):
    """Ports follow Read_Me/AI SYSTEM WORK ORDER — Brain :7000, Sense :8000, Bridge :8099."""

    odin_version: str = "3.0.0"

    # ── AI (OpenAI-compatible clients) ─────────────────
    ai_provider: str = "MOONSHOT"

    # Many .env files use API_KEY + BASE_URL + MODEL for DashScope / OpenAI-compatible hosts.
    compat_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("API_KEY", "COMPAT_API_KEY", "DASHSCOPE_API_KEY"),
    )
    compat_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("BASE_URL", "COMPAT_BASE_URL", "DASHSCOPE_BASE_URL"),
    )
    compat_model: str = Field(
        default="",
        validation_alias=AliasChoices("MODEL", "COMPAT_MODEL", "DASHSCOPE_MODEL"),
    )
    # When MODEL is a TTS / realtime id, use this for text chat instead.
    compat_chat_model: str = Field(
        default="",
        validation_alias=AliasChoices("QWEN_CHAT_MODEL", "CHAT_MODEL", "COMPAT_CHAT_MODEL"),
    )

    moonshot_api_key: str = ""
    moonshot_base_url: str = "https://api.moonshot.ai/v1"
    moonshot_model: str = "kimi-k2-turbo-preview"
    moonshot_vision_model: str = "moonshot-v1-8k-vision-preview"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = "https://api.openai.com/v1"

    nvidia_api_key: str = ""
    nvidia_model: str = "moonshotai/kimi-k2.5"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_vision_model: str = "microsoft/phi-3.5-vision-instruct"

    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-001"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_voice_model: str = "whisper-large-v3"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ── Bridge auth (header X-ODIN-KEY or JSON api_key) ──
    odin_bridge_key: str = ""
    bridge_key: str = ""  # alias from BRIDGE_KEY in .env

    # ── Service URLs (override in .env if needed) ───────
    bridge_url: str = "http://127.0.0.1:8099"
    sense_url: str = "http://127.0.0.1:8000"
    memory_url: str = "http://127.0.0.1:7001"

    # ── Ports ───────────────────────────────────────────
    port_brain: int = 7000
    port_memory: int = 7001
    port_dashboards: int = 7500
    port_sense: int = 8000
    port_hunter: int = 8500
    port_bridge: int = 8099
    port_n8n: int = 5678

    # Legacy names used by older modules
    port_core: int = 8000
    port_vision: int = 8015

    # ── Agent Tom (optional) ──────────────────────────────
    tom_max_screen_width: int = 1024
    tom_loop_delay: int = 2
    tom_auto_trust: bool = False

    # ── Webhooks ─────────────────────────────────────────
    n8n_memory_webhook: str = ""
    n8n_memory_hook_url: str = ""

    # ── Backups (under project root by default) ───────────
    backup_root: str = ""

    # ── Audio ─────────────────────────────────────────────
    sample_rate: int = 16000
    channels: int = 1
    chunk: int = 1024
    listen_timeout: int = 8
    odin_persona: str = "You are ODIN, Charles's local engineering partner."

    @property
    def core_url(self) -> str:
        return self.sense_url

    @property
    def SAMPLE_RATE(self) -> int:
        return self.sample_rate

    @property
    def CHANNELS(self) -> int:
        return self.channels

    @property
    def CHUNK(self) -> int:
        return self.chunk

    @property
    def port_m1(self) -> int:
        return self.port_brain

    @property
    def LISTEN_TIMEOUT(self) -> int:
        return self.listen_timeout

    @property
    def ODIN_PERSONA(self) -> str:
        return self.odin_persona

    @property
    def memory_dir(self) -> Path:
        """Layer 2–4 JSON stores live here (same tree Memory Pro uses)."""
        return ROOT / "M1" / "memory" / "data"

    @property
    def personality_file(self) -> Path:
        return ROOT / "M1" / "Brain" / "config" / "personality.py"

    @property
    def tools_dir(self) -> Path:
        return ROOT / "tools"

    @property
    def dashboard_dir(self) -> Path:
        p = ROOT / "M1" / "dashboards"
        return p if p.exists() else (ROOT / "static")

    @property
    def static_dir(self) -> Path:
        s = ROOT / "static"
        return s if s.exists() else (ROOT / "M1" / "Brain" / "static")

    @property
    def effective_bridge_key(self) -> str:
        return self.bridge_key or self.odin_bridge_key

    @property
    def backup_path(self) -> Path:
        return Path(self.backup_root).expanduser() if self.backup_root else (ROOT / "backups")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )


def get_settings() -> Settings:
    """Fresh load each call so edits to .env apply (no stale lru_cache)."""
    return Settings()


if __name__ == "__main__":
    s = get_settings()
    print(f"Brain stack v{s.odin_version}")
    print(f"ROOT          : {ROOT}")
    print(f"Compat API    : {'OK' if s.compat_api_key else 'MISSING'} (API_KEY + BASE_URL)")
    print(f"Moonshot      : {'OK' if s.moonshot_api_key else 'MISSING'}")
    print(f"Bridge key    : {'OK' if s.effective_bridge_key else 'MISSING'}")
    print(f"Memory dir    : {s.memory_dir}")
