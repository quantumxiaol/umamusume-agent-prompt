import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.web.process import convert_docling


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


def _convert_png_to_pdf(image_path: Path, output_path: Path, *, max_pixels: int) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Pillow is required for PNG->PDF. Try: pip install pillow") from exc

    with Image.open(image_path) as image:
        width, height = image.size
        pixels = width * height
        if max_pixels and pixels > max_pixels:
            scale = (max_pixels / pixels) ** 0.5
            width = max(1, int(width * scale))
            height = max(1, int(height * scale))
            image = image.resize((width, height), Image.LANCZOS)
            print(f"Downscaled image to {width}x{height} to stay under {max_pixels} pixels")
        rgb = image.convert("RGB")
        rgb.save(output_path, format="PDF")


def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    image_path = _resolve_image_path()
    results_dir = Path("results") / "test"
    results_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = results_dir / "visual_png.pdf"
    max_pixels = int(os.getenv("CRAWLER_IMAGE_MAX_PIXELS", "160000000"))
    _convert_png_to_pdf(image_path, pdf_path, max_pixels=max_pixels)
    print(f"Saved PDF: {pdf_path}")

    content = convert_docling(pdf_path)
    output_path = results_dir / "visual_docling_png.txt"
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


if __name__ == "__main__":
    _run()
