from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    root_dir = Path(__file__).resolve().parent
    load_dotenv(root_dir / ".env")

    parser = argparse.ArgumentParser(description="Download Docling models.")
    parser.add_argument(
        "--output-dir",
        default=os.getenv("DOCLING_ARTIFACTS_PATH", "modelweights/DocLing"),
        help="Target directory for Docling model artifacts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files already exist.",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress while downloading.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from docling.utils.model_downloader import download_models
    except ImportError as exc:
        raise SystemExit(
            "docling is not installed. Try: pip install docling"
        ) from exc

    download_models(
        output_dir=output_dir,
        force=args.force,
        progress=args.progress,
    )

    print(f"Docling models downloaded to: {output_dir}")
    print("Ensure DOCLING_ARTIFACTS_PATH points to this directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
