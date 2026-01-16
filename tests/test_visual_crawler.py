import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from umamusume_prompt.web.crawler import (
    crawl_biligame_page_visual_docling,
    crawl_biligame_page_visual_markitdown,
)


async def _run() -> None:
    target_url = os.getenv(
        "CRAWLER_BILIGAME_URL",
        # "https://wiki.biligame.com/umamusume/东海帝皇",
        "https://mzh.moegirl.org.cn/东海帝王",
    )
    use_proxy = os.getenv("CRAWLER_USE_PROXY", "0") not in ("0", "false", "False")
    capture_pdf = os.getenv("CRAWLER_CAPTURE_PDF", "1") not in ("0", "false", "False")

    output_dir = Path(os.getenv("CRAWLER_VISUAL_DIR", "results/test/visual"))
    output_dir.mkdir(parents=True, exist_ok=True)

    results_dir = Path("results") / "test"
    results_dir.mkdir(parents=True, exist_ok=True)

    content = await crawl_biligame_page_visual_markitdown(
        target_url,
        use_proxy=use_proxy,
        use_llm=False,
        output_dir=output_dir,
        capture_pdf=capture_pdf,
    )
    output_path = results_dir / "biligame_visual_markitdown.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")

    content = await crawl_biligame_page_visual_markitdown(
        target_url,
        use_proxy=use_proxy,
        use_llm=True,
        output_dir=output_dir,
        capture_pdf=capture_pdf,
    )
    output_path = results_dir / "biligame_visual_markitdown_llm.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")

    content = await crawl_biligame_page_visual_docling(
        target_url,
        use_proxy=use_proxy,
        output_dir=output_dir,
        capture_pdf=capture_pdf,
    )
    output_path = results_dir / "biligame_visual_docling.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    asyncio.run(_run())
