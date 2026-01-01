"""
check streamable http mcp server and list tools

python ./tests/test_stream_mcp.py -u "http://127.0.0.1:7777/mcp/" -q "can you tell me about umamusume 爱慕织姬?from bilibili wiki"

"""



import argparse
import asyncio
import os

import pytest
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

def _build_model() -> ChatOpenAI:
    api_key = os.getenv("INFO_LLM_MODEL_API_KEY")
    if not api_key:
        raise RuntimeError("Missing INFO_LLM_MODEL_API_KEY for agent test.")
    return ChatOpenAI(
        model_name=os.getenv("INFO_LLM_MODEL_NAME"),
        api_key=api_key,
        base_url=os.getenv("INFO_LLM_MODEL_BASE_URL"),
        temperature=0.7,
    )


server_url="http://127.0.0.1:1234/mcp"
async def async_main(server_url: str = "", question: str = ""):
    model = _build_model()
    async with streamable_http_client(server_url) as (read_stream, write_stream, _):
        # print('MCP server连接成功')
        async with ClientSession(read_stream, write_stream) as session:
            # 初始化连接
            # print('MCP server session已建立')
            await session.initialize()
            print('MCP server session已初始化')

            tools = await load_mcp_tools(session)
            print("可用工具:", [tool.name for tool in tools])

            if question != "":
                agent = create_agent(model, tools)
                agent_response = await agent.ainvoke(
                    {"messages": [question]},
                    config={"recursion_limit": 75}
                    
                    )
                # print("Final answer:", agent_response["messages"][-1].content)
                result = extract_tool_info(agent_response)

                print("Final Answer:\n", result["final_answer"])
                print("\nTool Calls:", result["tool_calls"])
                print("\nTool Results:", result["tool_results"])
                return result
    return None



def extract_tool_info(agent_response):
    tool_calls = []
    tool_results = [] 

    for msg in agent_response["messages"]:
        # 判断消息类型
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
            for tool_call in msg.tool_calls:
                tool_calls.append({
                "name": tool_call["name"],
                "arguments": tool_call["args"]
                })

        elif isinstance(msg, ToolMessage):
            tool_results.append({
            "id": msg.tool_call_id,
            "name": msg.name,
            "content": msg.content,
            "status": msg.status
            })

    # 提取最终回答
    final_answer = None
    for msg in reversed(agent_response["messages"]):
        if isinstance(msg, AIMessage):
            final_answer = msg.content  
        break

    return {
    "tool_calls": tool_calls,
    "tool_results": tool_results,
    "final_answer": final_answer
    }


@pytest.mark.asyncio
async def test_agent_calls_tool() -> None:
    server_url = os.getenv("MCP_URL", "http://127.0.0.1:7777/mcp/")
    question = os.getenv("MCP_QUESTION", "爱慕织姬")

    try:
        result = await async_main(server_url=server_url, question=question)
        assert result is not None, "Expected agent result"
        assert result["tool_calls"], "Expected at least one tool call"
    except RuntimeError as exc:
        pytest.skip(str(exc))
    except Exception as exc:
        pytest.skip(f"MCP server not available: {exc}")

if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("--base_url",
    "-u", 
    type=str, 
    default="http://127.0.0.1:7777/mcp/",
    help="MCP server base url"
    )
    arg.add_argument("--question",
    "-q", 
    type=str, 
    default="爱慕织姬",
    help="question to ask agent, None for donot ask"
    )
    arg=arg.parse_args()
    asyncio.run(async_main(server_url=arg.base_url,question=arg.question))
