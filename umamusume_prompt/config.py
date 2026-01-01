from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Config:
    # LLM settings
    info_llm_model_name: str = os.getenv("INFO_LLM_MODEL_NAME", "qwen-max-latest")
    info_llm_model_base_url: str = os.getenv(
        "INFO_LLM_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    info_llm_model_api_key: str = os.getenv("INFO_LLM_MODEL_API_KEY", "")

    writer_llm_model_name: str = os.getenv("WRITER_LLM_MODEL_NAME", "qwen-max-latest")
    writer_llm_model_base_url: str = os.getenv(
        "WRITER_LLM_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    writer_llm_model_api_key: str = os.getenv("WRITER_LLM_MODEL_API_KEY", "")

    user_agent: str = os.getenv("USER_AGENT", "UmamusumePrompt/1.0")

    # Prompt/templates
    prompt_dir: Path = ROOT_DIR / "umamusume_prompt" / "prompts"
    characters_json: Path = ROOT_DIR / "umamusume_characters.json"

    # Proxy settings
    http_proxy: str | None = os.getenv("HTTP_PROXY")
    https_proxy: str | None = os.getenv("HTTPS_PROXY")

    # Google Search settings
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")

    def validate_web_tools(self) -> None:
        missing = []
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY")
        if not self.google_cse_id:
            missing.append("GOOGLE_CSE_ID")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    def validate_info_llm(self) -> None:
        if not self.info_llm_model_api_key:
            raise EnvironmentError("Missing required environment variable: INFO_LLM_MODEL_API_KEY")

    def validate_writer_llm(self) -> None:
        if not self.writer_llm_model_api_key:
            raise EnvironmentError("Missing required environment variable: WRITER_LLM_MODEL_API_KEY")

    def proxy_url(self) -> str | None:
        if self.http_proxy:
            return self.http_proxy
        if self.https_proxy:
            return self.https_proxy
        return None


config = Config()
