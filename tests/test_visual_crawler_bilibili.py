import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.web.crawler import crawl_biligame_page_visual_markitdown


async def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    target_url = os.getenv(
        "CRAWLER_BILIGAME_URL",
        "https://wiki.biligame.com/umamusume/东海帝皇",
    )
    use_proxy = os.getenv("CRAWLER_USE_PROXY")
    if use_proxy is None:
        proxy_flag = None
    else:
        proxy_flag = use_proxy not in ("0", "false", "False")

    content = await crawl_biligame_page_visual_markitdown(
        target_url, use_proxy=proxy_flag
    )
    output_dir = Path("results") / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "biligame_visual_markitdown.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    asyncio.run(_run())
