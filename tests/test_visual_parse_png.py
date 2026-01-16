import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.web.process import convert_markitdown


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


def _write_output(filename: str, content: str) -> None:
    results_dir = Path("results") / "test"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / filename
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(content)} chars to {output_path}")


def _run() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    load_dotenv(root_dir / ".env")

    image_path = _resolve_image_path()
    print(f"Using image: {image_path}")

    content = convert_markitdown(image_path, use_llm=False)
    _write_output("visual_markitdown_png.txt", content)

    content = convert_markitdown(image_path, use_llm=True)
    _write_output("visual_markitdown_png_llm.txt", content)


if __name__ == "__main__":
    _run()
