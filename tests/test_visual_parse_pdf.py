import json
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from umamusume_prompt.web.process import convert_docling, convert_markitdown


def _resolve_visual_path() -> Path:
    explicit = os.getenv("CRAWLER_VISUAL_PATH", "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path

    explicit_pdf = os.getenv("CRAWLER_PDF_PATH", "").strip()
    if explicit_pdf:
        path = Path(explicit_pdf)
        if path.exists():
            return path

    explicit_image = os.getenv("CRAWLER_IMAGE_PATH", "").strip()
    if explicit_image:
        path = Path(explicit_image)
        if path.exists():
            return path

    capture_json = Path("results") / "test" / "visual_capture.json"
    if capture_json.exists():
        data = json.loads(capture_json.read_text(encoding="utf-8"))
        for key in ("pdf_path", "png_path"):
            candidate = data.get(key, "")
            path = Path(candidate)
            if candidate and path.exists():
                return path

    visual_dir = Path(os.getenv("CRAWLER_VISUAL_DIR", "results/test/visual"))
    for ext in ("*.pdf", "*.png", "*.jpg", "*.jpeg"):
        for path in visual_dir.glob(ext):
            return path

    raise FileNotFoundError(
        "No visual file found. Set CRAWLER_VISUAL_PATH/CRAWLER_PDF_PATH/CRAWLER_IMAGE_PATH "
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
    visual_path = _resolve_visual_path()
    print(f"Using file: {visual_path}")

    content = convert_markitdown(visual_path, use_llm=False)
    _write_output("visual_markitdown.txt", content)

    # content = convert_markitdown(visual_path, use_llm=True)
    # _write_output("visual_markitdown_llm.txt", content)

    if visual_path.suffix.lower() == ".pdf":
        content = convert_docling(visual_path)
        _write_output("visual_docling.txt", content)
    else:
        print("Skipping Docling: only PDF is supported for this test.")


if __name__ == "__main__":
    _run()
