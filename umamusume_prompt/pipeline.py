from __future__ import annotations

import hashlib
from pathlib import Path
import json
from typing import Tuple, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from umamusume_prompt.config import config


def _load_prompt(name: str) -> str:
    prompt_path = config.prompt_dir / name
    return prompt_path.read_text(encoding="utf-8")


def _safe_dir_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")
    if cleaned:
        return cleaned
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"character_{digest}"


def _build_info_model() -> ChatOpenAI:
    return ChatOpenAI(
        model_name=config.info_llm_model_name,
        api_key=config.info_llm_model_api_key,
        base_url=config.info_llm_model_base_url,
    )


def _build_writer_model() -> ChatOpenAI:
    return ChatOpenAI(
        model_name=config.writer_llm_model_name,
        api_key=config.writer_llm_model_api_key,
        base_url=config.writer_llm_model_base_url,
    )


def _extract_tool_info(agent_response: dict) -> Dict[str, Any]:
    tool_calls: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []

    for msg in agent_response.get("messages", []):
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tool_call in msg.tool_calls:
                tool_calls.append(
                    {
                        "name": tool_call.get("name"),
                        "arguments": tool_call.get("args"),
                    }
                )
        elif isinstance(msg, ToolMessage):
            tool_results.append(
                {
                    "id": msg.tool_call_id,
                    "name": msg.name,
                    "content": msg.content,
                    "status": getattr(msg, "status", None),
                }
            )

    final_answer = None
    for msg in reversed(agent_response.get("messages", [])):
        if isinstance(msg, AIMessage):
            final_answer = msg.content
            break

    return {
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "final_answer": final_answer,
    }


async def collect_web_info(
    mcp_url: str, character_cn: str, character_en: str
) -> Tuple[str, Dict[str, Any]]:
    config.validate_info_llm()
    print(f"[stage1] collecting web info via MCP: {mcp_url}")
    prompt = _load_prompt("collect_web.md").format(
        character_cn=character_cn, character_en=character_en
    )

    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            tool_names = ", ".join(tool.name for tool in tools)
            print(f"[stage1] MCP tools: {tool_names}")
            agent = create_agent(_build_info_model(), tools)
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=prompt)]},
                config={"recursion_limit": 60},
            )
            web_info = result["messages"][-1].content
            tool_info = _extract_tool_info(result)
            print("[stage1] web info collected.")
            return web_info, tool_info


async def build_role_prompt(
    web_info: str, character_cn: str, character_en: str
) -> str:
    config.validate_writer_llm()
    print("[stage2] building role prompt.")
    base_info = _load_prompt("umamusume_base_info.md")
    prompt = _load_prompt("build_prompt.md").format(
        character_cn=character_cn,
        character_en=character_en,
        base_info=base_info,
        web_info=web_info,
    )
    model = _build_writer_model()
    response = await model.ainvoke([HumanMessage(content=prompt)])
    print("[stage2] role prompt generated.")
    return response.content


async def run_pipeline(
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

    role_prompt = await build_role_prompt(web_info, character_cn, character_en)
    prompt_path = character_dir / "role_prompt.md"
    prompt_path.write_text(role_prompt, encoding="utf-8")
    print(f"[run] saved role prompt: {prompt_path}")

    return web_path, prompt_path
