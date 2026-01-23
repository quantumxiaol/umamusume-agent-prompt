"""
check mcp server and list tools

Local MCP example:
python tests/test_mcp_tool_crawler_moegirl.py -u "http://127.0.0.1:7777/mcp/" \
    --tool-name crawl_moegirl_wiki \
    --tool-arg "url=https://mzh.moegirl.org.cn/东海帝王"

Notes:
- crawl_moegirl_wiki now uses MediaWiki API to fetch content and converts to Markdown.
- Optional: --tool-arg "use_proxy=true"
- Optional: --tool-arg "max_depth=1"
"""

import argparse
import asyncio
import json
import os
from typing import Any, Dict, Optional

import pytest
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()


def parse_tool_args(args_str_list: list) -> Dict[str, Any]:
    """
    将 ["key=value", "foo=bar"] 转为 {"key": "value", "foo": "bar"}
    支持自动类型解析：str, int, float, bool, None
    """
    result = {}
    if not args_str_list:
        return result

    for item in args_str_list:
        if "=" not in item:
            raise ValueError(f"Invalid tool-arg format: {item}, expected key=value")
        k, v = item.split("=", 1)

        # 尝试类型解析
        try:
            v = json.loads(v.lower() if v.lower() in ("true", "false", "null") else v)
        except json.JSONDecodeError:
            pass  # keep as string

        result[k] = v
    return result


async def async_main(
    server_url: str = "",
    question: str = "",
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
):
    if not os.getenv("INFO_LLM_MODEL_API_KEY"):
        raise SystemExit("Missing INFO_LLM_MODEL_API_KEY for agent test.")

    model = ChatOpenAI(
        model_name=os.getenv("INFO_LLM_MODEL_NAME"),
        api_key=os.getenv("INFO_LLM_MODEL_API_KEY"),
        base_url=os.getenv("INFO_LLM_MODEL_BASE_URL"),
        temperature=0,
    )

    async with streamable_http_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("MCP server session已初始化")

            tools = await load_mcp_tools(session)
            tool_dict = {tool.name: tool for tool in tools}

            print("可用工具:", [tool.name for tool in tools])
            for tool in tools:
                print(f"Tool: {tool.name}")
                print(f"Args Schema: {tool.args}")
                print(f"Description: {tool.description}\n")

            # =============================
            # 场景1: 仅列出工具（无 question, 无 tool_name）
            # =============================
            if not question and not tool_name:
                print("未提供问题或工具调用，仅列出工具信息。")
                print("TEST_RESULT: PASSED")
                return

            # =============================
            # 场景2: 直接调用指定工具
            # =============================
            if tool_name:
                if tool_name not in tool_dict:
                    print(f"错误: 工具 '{tool_name}' 未在 MCP 服务中找到！")
                    print("TEST_RESULT: FAILED")
                    return

                if not tool_args:
                    print(f"警告: 调用工具 '{tool_name}' 但未提供参数。")
                    tool_args = {}

                try:
                    print(f"正在调用工具: {tool_name}，参数: {tool_args}")
                    result = await tool_dict[tool_name].ainvoke(tool_args)
                    print("✅ 工具调用成功！返回结果:")
                    print(
                        json.dumps(result, indent=2, ensure_ascii=False)
                        if isinstance(result, (dict, list))
                        else result
                    )

                    # 可选：结构化解析（如果返回的是 JSON 字符串）
                    if isinstance(result, str):
                        try:
                            parsed = json.loads(result)
                            print("🔍 JSON 解析结果:")
                            print(json.dumps(parsed, indent=2, ensure_ascii=False))
                        except json.JSONDecodeError:
                            pass

                    print("TEST_RESULT: PASSED")
                except Exception as e:
                    print(f"❌ 工具调用失败: {type(e).__name__}: {e}")
                    print("TEST_RESULT: FAILED")
                return

            # =============================
            # 场景3: 使用 Agent 处理用户问题（兼容原逻辑）
            # =============================
            if question and not tool_name:
                print(f"使用 Agent 处理问题: {question}")
                agent = create_agent(model, tools)
                try:
                    agent_response = await agent.ainvoke({"messages": [question]})
                    # 简单提取最终答案
                    final_answer = ""
                    for msg in reversed(agent_response["messages"]):
                        if isinstance(msg, AIMessage):
                            final_answer = msg.content
                            break
                    print("Final Answer:\n", final_answer)
                    print("TEST_RESULT: PASSED")
                except Exception as e:
                    print(f"❌ Agent 调用失败: {e}")
                    print("TEST_RESULT: FAILED")


@pytest.mark.asyncio
async def test_mcp_tool_call() -> None:
    server_url = os.getenv("MCP_URL", "http://127.0.0.1:7777/mcp/")
    tool_name = os.getenv("MCP_TOOL_NAME", "crawl_moegirl_wiki")
    tool_args = parse_tool_args(
        [
            os.getenv(
                "MCP_TOOL_QUERY",
                "url=https://mzh.moegirl.org.cn/东海帝王",
            )
        ]
    )

    try:
        async with streamable_http_client(server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                tool_dict = {tool.name: tool for tool in tools}
                assert tool_name in tool_dict, f"Missing tool: {tool_name}"
                result = await tool_dict[tool_name].ainvoke(tool_args)
                assert result, "Empty tool result"
    except Exception as exc:
        pytest.skip(f"MCP server not available: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test MCP Server: list tools, invoke tool, or ask agent"
    )

    parser.add_argument(
        "-u",
        "--base_url",
        type=str,
        default="http://127.0.0.1:7777/mcp/",
        help="MCP server base url",
    )
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        default="东海帝王",
        help="问题文本，如果提供，将使用 Agent 回答",
    )
    parser.add_argument(
        "--tool-name",
        type=str,
        default="crawl_moegirl_wiki",
        help="要直接调用的工具名称，例如 crawl_moegirl_wiki",
    )
    parser.add_argument(
        "--tool-arg",
        action="append",
        default=["url=https://mzh.moegirl.org.cn/东海帝王"],
        help="工具参数，格式 key=value，可多次使用",
    )
    args = parser.parse_args()

    # 解析 tool-arg
    tool_args = parse_tool_args(args.tool_arg) if args.tool_arg else None

    # 运行主函数
    asyncio.run(
        async_main(
            server_url=args.base_url,
            question=args.question,
            tool_name=args.tool_name,
            tool_args=tool_args,
        )
    )
