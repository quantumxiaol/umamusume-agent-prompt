import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.config import config
from umamusume_prompt.web.crawler import crawl_moegirl_page_visual_markitdown


async def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    target_url = os.getenv(
        "CRAWLER_BILIGAME_URL",
        "https://mzh.moegirl.org.cn/东海帝王",
    )
    use_proxy_env = os.getenv("CRAWLER_USE_PROXY")
    if use_proxy_env is None or use_proxy_env == "":
        proxy_flag = bool(config.proxy_url())
    else:
        proxy_flag = use_proxy_env not in ("0", "false", "False")

    print_scale = os.getenv("CRAWLER_PRINT_SCALE")
    print_scale_value = float(print_scale) if print_scale else None

    headless_env = os.getenv("CRAWLER_HEADLESS")
    if headless_env is None or headless_env == "":
        headless = False
    else:
        headless = headless_env not in ("0", "false", "False")

    output_dir = Path(os.getenv("CRAWLER_VISUAL_DIR", "results/test/visual"))
    output_dir.mkdir(parents=True, exist_ok=True)

    content = await crawl_moegirl_page_visual_markitdown(
        target_url,
        use_proxy=proxy_flag,
        print_scale=print_scale_value,
        output_dir=output_dir,
        headless=headless,
    )
    output_dir = Path("results") / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "moegirl_visual_markitdown.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    asyncio.run(_run())
