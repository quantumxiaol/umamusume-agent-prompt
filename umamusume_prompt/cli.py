from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

import httpx

from umamusume_prompt.characters import load_characters, resolve_character
from umamusume_prompt.config import config
from umamusume_prompt.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Umamusume role prompts")
    parser.add_argument(
        "--character",
        action="append",
        help="Character name (CN or EN). Can be provided multiple times.",
    )
    parser.add_argument(
        "--characters-json",
        default=str(config.characters_json),
        help="Path to umamusume_characters.json",
    )
    parser.add_argument(
        "--mcp-url",
        default="http://127.0.0.1:7777/mcp/",
        help="Web MCP server URL",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Output directory for collected info and prompts",
    )
    parser.add_argument(
        "--wait-mcp",
        type=int,
        default=60,
        help="Seconds to wait for MCP server readiness (default: 60, 0 to disable)",
    )
    parser.add_argument(
        "--wait-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds when waiting for MCP (default: 2.0)",
    )
    return parser.parse_args()


def _mcp_ready(mcp_url: str) -> bool:
    try:
        resp = httpx.get(mcp_url, timeout=3.0)
        if resp.status_code in {200, 307, 404, 405}:
            return True
        return resp.status_code < 500
    except httpx.RequestError:
        return False


def _wait_for_mcp(mcp_url: str, timeout_s: int, interval_s: float) -> None:
    if timeout_s <= 0:
        return
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _mcp_ready(mcp_url):
            print("[ok] MCP server is ready.")
            return
        print("[wait] MCP not ready yet, retrying...")
        time.sleep(interval_s)
    raise SystemExit(
        f"MCP server not ready after {timeout_s}s. "
        "Please start it first: python mcpserver.py --http -p 7777"
    )


async def _run(args: argparse.Namespace) -> None:
    if not args.character:
        raise SystemExit("Please provide at least one --character.")

    _wait_for_mcp(args.mcp_url, args.wait_mcp, args.wait_interval)

    mapping = load_characters(Path(args.characters_json))
    output_dir = Path(args.output)

    for name in args.character:
        cn_name, en_name, found = resolve_character(name, mapping)
        if not found:
            raise SystemExit(
                f"Character '{name}' not found in {args.characters_json}. "
                "Please add it to the mapping first."
            )
        web_path, prompt_path = await run_pipeline(
            args.mcp_url, cn_name, en_name, output_dir
        )
        print(f"[ok] {cn_name} ({en_name}) -> {web_path} | {prompt_path}")


def main() -> None:
    args = parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
