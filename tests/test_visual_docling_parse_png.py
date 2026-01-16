import os
import sys
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.web.process import convert_docling
from umamusume_prompt.web.smart_split import smart_image_to_pdf


def _resolve_image_path() -> Path:
    explicit = os.getenv("CRAWLER_IMAGE_PATH", "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path

    explicit_visual = os.getenv("CRAWLER_VISUAL_PATH", "").strip()
    if explicit_visual:
        path = Path(explicit_visual)
        if path.exists():
            return path

    visual_dir = Path(os.getenv("CRAWLER_VISUAL_DIR", "results/test/visual"))
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for path in visual_dir.glob(ext):
            return path

    raise FileNotFoundError(
        "No image found. Set CRAWLER_IMAGE_PATH/CRAWLER_VISUAL_PATH "
        "or run tests/test_visual_capture_pdf.py first."
    )


def _split_png_to_pdf(
    image_path: Path,
    output_path: Path,
    *,
    max_page_height_ratio: float,
    overlap: int,
) -> None:
    ok = smart_image_to_pdf(
        image_path,
        output_path,
        max_page_height_ratio=max_page_height_ratio,
        overlap=overlap,
    )
    if not ok:
        raise RuntimeError(f"Failed to split PNG into PDF: {image_path}")


def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    image_path = _resolve_image_path()
    pdf_path = image_path.with_name(f"{image_path.stem}_split.pdf")
    max_page_height_ratio = float(os.getenv("CRAWLER_PNG_PAGE_HEIGHT_RATIO", "1.5"))
    overlap = int(os.getenv("CRAWLER_PNG_PAGE_OVERLAP", "0"))
    _split_png_to_pdf(
        image_path,
        pdf_path,
        max_page_height_ratio=max_page_height_ratio,
        overlap=overlap,
    )
    print(f"Saved PDF: {pdf_path}")

    content = convert_docling(pdf_path, use_ocr=True)
    results_dir = Path("results") / "test"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "visual_docling_png.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    _run()
