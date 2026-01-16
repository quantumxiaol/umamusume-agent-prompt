import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from umamusume_prompt.web.crawler import (
    crawl_moegirl_page,
    crawl_moegirl_page_llm,
    crawl_moegirl_page_pruned,
)


async def _run() -> None:
    target_url = os.getenv(
        "CRAWLER_MOEGIRL_URL",
        "https://mzh.moegirl.org.cn/东海帝王",
    )
    use_proxy = os.getenv("CRAWLER_USE_PROXY", "1") not in ("0", "false", "False")
    mode = os.getenv("CRAWLER_MODE", "structured").lower()
    if mode == "llm":
        content = await crawl_moegirl_page_llm(target_url, use_proxy=use_proxy)
        output_name = "moegirl_llm.json"
    elif mode == "pruned":
        content = await crawl_moegirl_page_pruned(target_url, use_proxy=use_proxy)
        output_name = "moegirl_pruned.txt"
    else:
        content = await crawl_moegirl_page(target_url, use_proxy=use_proxy)
        output_name = "moegirl.txt"
    output_dir = Path("results") / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    asyncio.run(_run())
