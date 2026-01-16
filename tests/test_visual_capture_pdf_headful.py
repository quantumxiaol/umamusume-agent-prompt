import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.config import config
from umamusume_prompt.web.crawler import (
    crawl_biligame_page_visual,
    crawl_moegirl_page_visual,
)


async def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    target_url = os.getenv(
        "CRAWLER_BILIGAME_URL",
        # "https://wiki.biligame.com/umamusume/东海帝皇",
        "https://mzh.moegirl.org.cn/东海帝王",
    )
    use_proxy_env = os.getenv("CRAWLER_USE_PROXY")
    if use_proxy_env is None or use_proxy_env == "":
        use_proxy = bool(config.proxy_url())
    else:
        use_proxy = use_proxy_env not in ("0", "false", "False")
    capture_pdf = os.getenv("CRAWLER_CAPTURE_PDF", "1") not in ("0", "false", "False")
    pdf_from_png = os.getenv("CRAWLER_PDF_FROM_PNG", "0") not in ("0", "false", "False")
    print_scale = os.getenv("CRAWLER_PRINT_SCALE")
    print_scale_value = float(print_scale) if print_scale else None
    if use_proxy and not config.proxy_url():
        print("Warning: CRAWLER_USE_PROXY=1 but HTTP_PROXY/HTTPS_PROXY is not set.")

    output_dir = Path(os.getenv("CRAWLER_VISUAL_DIR", "results/test/visual"))
    output_dir.mkdir(parents=True, exist_ok=True)

    if "moegirl.org.cn" in urlparse(target_url).netloc:
        capture = await crawl_moegirl_page_visual(
            target_url,
            use_proxy=use_proxy,
            output_dir=output_dir,
            capture_pdf=capture_pdf,
            headless=False,
            pdf_from_png=pdf_from_png,
            print_scale=print_scale_value,
        )
    else:
        capture = await crawl_biligame_page_visual(
            target_url,
            use_proxy=use_proxy,
            output_dir=output_dir,
            capture_pdf=capture_pdf,
            headless=False,
            pdf_from_png=pdf_from_png,
            print_scale=print_scale_value,
        )

    results_dir = Path("results") / "test"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "visual_capture.json"
    output_path.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")

    pdf_path = capture.get("pdf_path")
    png_path = capture.get("png_path")
    if pdf_path and Path(pdf_path).exists():
        size = Path(pdf_path).stat().st_size
        print(f"PDF saved at {pdf_path} ({size} bytes)")
    else:
        print("No PDF saved.")
    if png_path and Path(png_path).exists():
        size = Path(png_path).stat().st_size
        print(f"PNG saved at {png_path} ({size} bytes)")


if __name__ == "__main__":
    asyncio.run(_run())
