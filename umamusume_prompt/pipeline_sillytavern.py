from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Tuple

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from umamusume_prompt.config import config
from umamusume_prompt.pipeline import collect_web_info


def _load_prompt(name: str) -> str:
    prompt_path = config.prompt_dir / name
    return prompt_path.read_text(encoding="utf-8")


def _safe_dir_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")
    if cleaned:
        return cleaned
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"character_{digest}"


def _build_writer_model() -> ChatOpenAI:
    return ChatOpenAI(
        model_name=config.writer_llm_model_name,
        api_key=config.writer_llm_model_api_key,
        base_url=config.writer_llm_model_base_url,
    )


async def build_sillytavern_character(
    web_info: str, character_cn: str, character_en: str
) -> str:
    config.validate_writer_llm()
    print("[stage2] building SillyTavern character.")
    base_info = _load_prompt("umamusume_base_info.md")
    prompt = _load_prompt("build_SillyTavern_character.md").format(
        character_cn=character_cn,
        character_en=character_en,
        base_info=base_info,
        web_info=web_info,
    )
    model = _build_writer_model()
    response = await model.ainvoke([HumanMessage(content=prompt)])
    print("[stage2] SillyTavern character generated.")
    return response.content


async def run_pipeline_sillytavern(
    mcp_url: str, character_cn: str, character_en: str, output_dir: Path
) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    character_dir = output_dir / _safe_dir_name(character_en or character_cn)
    character_dir.mkdir(parents=True, exist_ok=True)

    print(f"[run] character: {character_cn} ({character_en})")
    web_info, tool_info = await collect_web_info(mcp_url, character_cn, character_en)
    web_path = character_dir / "web_info.md"
    web_path.write_text(web_info, encoding="utf-8")
    print(f"[run] saved web info: {web_path}")

    tool_path = character_dir / "tool_calls.json"
    tool_path.write_text(
        json.dumps(tool_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[run] saved tool calls: {tool_path}")

    role_prompt = await build_sillytavern_character(
        web_info, character_cn, character_en
    )
    prompt_path = character_dir / "role_prompt.md"
    prompt_path.write_text(role_prompt, encoding="utf-8")
    print(f"[run] saved role prompt: {prompt_path}")

    return web_path, prompt_path
