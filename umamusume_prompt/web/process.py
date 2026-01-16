from __future__ import annotations

import os
import tempfile
from pathlib import Path

from umamusume_prompt.config import config

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
_LLM_IMAGE_MAX_BYTES = 18_000_000
_LLM_IMAGE_MAX_DIM = 2048


def _coerce_path(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in _IMAGE_EXTENSIONS


def _prepare_llm_image_path(path: Path) -> Path:
    if not _is_image(path):
        return path
    if path.stat().st_size <= _LLM_IMAGE_MAX_BYTES:
        return path

    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "Pillow is required to downscale images for LLM. Try: pip install pillow"
        ) from exc

    with Image.open(path) as image:
        image = image.convert("RGB")
        width, height = image.size
        scale = min(1.0, _LLM_IMAGE_MAX_DIM / max(width, height))
        if scale < 1.0:
            image = image.resize(
                (int(width * scale), int(height * scale)), Image.LANCZOS
            )

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_path = Path(temp_file.name)
        temp_file.close()
        image.save(temp_path, format="JPEG", quality=85, optimize=True)

    if temp_path.stat().st_size <= _LLM_IMAGE_MAX_BYTES:
        return temp_path

    with Image.open(temp_path) as image:
        for quality in (75, 65, 55):
            image.save(temp_path, format="JPEG", quality=quality, optimize=True)
            if temp_path.stat().st_size <= _LLM_IMAGE_MAX_BYTES:
                return temp_path

    raise ValueError(
        "Image is too large for LLM after downscaling. Try a smaller screenshot "
        "or lower capture resolution."
    )


def convert_markitdown(path: str | Path, *, use_llm: bool = False) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise ImportError(
            "markitdown is not installed. Try: pip install 'markitdown[all]'"
        ) from exc

    file_path = _coerce_path(path)

    if use_llm:
        if not config.info_llm_model_api_key:
            raise EnvironmentError("Missing required environment variable: INFO_LLM_MODEL_API_KEY")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai is not installed. Try: pip install openai"
            ) from exc
        client = OpenAI(
            api_key=config.info_llm_model_api_key,
            base_url=config.info_llm_model_base_url,
        )
        llm_path = _prepare_llm_image_path(file_path)
        model_name = (
            config.info_llm_vision_model_name
            if _is_image(file_path) and config.info_llm_vision_model_name
            else config.info_llm_model_name
        )
        md = MarkItDown(llm_client=client, llm_model=model_name)
    else:
        md = MarkItDown(enable_plugins=False)

    result = md.convert(str(llm_path if use_llm else file_path))
    return result.text_content or ""


def convert_docling(path: str | Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise ImportError(
            "docling is not installed. Try: pip install docling"
        ) from exc

    file_path = _coerce_path(path)
    artifacts_path = os.getenv("DOCLING_ARTIFACTS_PATH", "")
    converter = None
    if artifacts_path and file_path.suffix.lower() == ".pdf":
        artifacts_root = Path(artifacts_path)
        if not artifacts_root.exists():
            raise FileNotFoundError(
                "Docling artifacts path does not exist. Set DOCLING_ARTIFACTS_PATH "
                f"to a valid directory (current: {artifacts_root})."
            )
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    if converter is None:
        converter = DocumentConverter()
    result = converter.convert(str(file_path))
    return result.document.export_to_markdown()
