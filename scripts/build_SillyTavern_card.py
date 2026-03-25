from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, PngImagePlugin


SECTION_KEY_PREFIXES = {
    "description": "description",
    "personality": "personality",
    "scenario": "scenario",
    "first message": "first_mes",
    "example messages": "mes_example",
}
REQUIRED_SECTION_KEYS = (
    "description",
    "personality",
    "scenario",
    "first_mes",
    "mes_example",
)


def _safe_dir_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")
    return cleaned or "unknown"


def _section_key_from_heading(heading: str) -> str | None:
    lowered = heading.strip().lower()
    for prefix, key in SECTION_KEY_PREFIXES.items():
        if lowered.startswith(prefix):
            return key
    return None


def _clean_section_body(body: str) -> str:
    lines = [line for line in body.splitlines() if line.strip() != "---"]
    return "\n".join(lines).strip()


def parse_role_prompt_sections(role_prompt_path: Path) -> Dict[str, str]:
    text = role_prompt_path.read_text(encoding="utf-8")
    heading_matches = list(re.finditer(r"^###\s+(.+?)\s*$", text, flags=re.MULTILINE))
    sections: Dict[str, str] = {}

    for idx, match in enumerate(heading_matches):
        key = _section_key_from_heading(match.group(1))
        if not key:
            continue
        start = match.end()
        end = heading_matches[idx + 1].start() if idx + 1 < len(heading_matches) else len(text)
        body = _clean_section_body(text[start:end])
        if body:
            sections[key] = body

    missing = [key for key in REQUIRED_SECTION_KEYS if key not in sections]
    if missing:
        raise ValueError(
            f"Missing sections in {role_prompt_path}: {', '.join(missing)}"
        )
    return sections


def load_character_mapping(characters_json: Path) -> Dict[str, Tuple[str, str]]:
    mapping_raw = json.loads(characters_json.read_text(encoding="utf-8"))
    safe_to_names: Dict[str, Tuple[str, str]] = {}
    for cn_name, en_name in mapping_raw.items():
        safe_to_names[_safe_dir_name(en_name)] = (cn_name, en_name)
        safe_to_names[_safe_dir_name(cn_name)] = (cn_name, en_name)
    return safe_to_names


def index_image_dirs(images_root: Path) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    for child in images_root.iterdir():
        if child.is_dir():
            index[_safe_dir_name(child.name)] = child
    return index


def pick_avatar_png(image_dir: Path) -> Path:
    png_files = sorted(
        [path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() == ".png"]
    )
    if not png_files:
        raise FileNotFoundError(f"No PNG files found in {image_dir}")

    jsf_prefix = [path for path in png_files if path.stem.lower().startswith("jsf")]
    if jsf_prefix:
        return jsf_prefix[0]

    jsf_contains = [path for path in png_files if "jsf" in path.stem.lower()]
    if jsf_contains:
        return jsf_contains[0]

    return png_files[0]


def build_card_payload(
    *,
    name_cn: str,
    sections: Dict[str, str],
    creator: str,
    tags: list[str],
    role_prompt_path: Path,
) -> Dict[str, object]:
    return {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": name_cn,
            "description": sections["description"],
            "personality": sections["personality"],
            "scenario": sections["scenario"],
            "first_mes": sections["first_mes"],
            "mes_example": sections["mes_example"],
            "creator_notes": f"Generated from {role_prompt_path.as_posix()}",
            "system_prompt": "",
            "post_history_instructions": "",
            "alternate_greetings": [],
            "character_version": "1.0",
            "tags": tags,
            "creator": creator,
        },
    }


def write_png_card(src_png: Path, out_png: Path, card_json_text: str) -> None:
    b64_payload = base64.b64encode(card_json_text.encode("utf-8")).decode("utf-8")
    with Image.open(src_png) as image:
        pnginfo = PngImagePlugin.PngInfo()
        for key, value in image.info.items():
            if key.lower() == "chara":
                continue
            if isinstance(value, str):
                pnginfo.add_text(key, value)
        pnginfo.add_text("chara", b64_payload)
        save_kwargs = {}
        if "icc_profile" in image.info:
            save_kwargs["icc_profile"] = image.info["icc_profile"]
        image.save(out_png, format="PNG", pnginfo=pnginfo, **save_kwargs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build SillyTavern Character Card V2 files from results_SillyTavern."
    )
    parser.add_argument(
        "--results-root",
        default="results_SillyTavern",
        help="Root directory that contains per-character role_prompt.md outputs.",
    )
    parser.add_argument(
        "--images-root",
        default="results_images",
        help="Root directory that contains downloaded character image folders.",
    )
    parser.add_argument(
        "--characters-json",
        default="umamusume_characters.json",
        help="Character mapping JSON path (CN -> EN).",
    )
    parser.add_argument(
        "--character",
        action="append",
        help="Only build specified character directory names (e.g. Admire_Vega).",
    )
    parser.add_argument(
        "--creator",
        default="umamusume-agent-prompt",
        help="Creator field written into card data.",
    )
    parser.add_argument(
        "--tags",
        default="赛马娘,UmaMusume,SillyTavern,CCV2",
        help="Comma-separated tags for card data.",
    )
    parser.add_argument(
        "--json-name",
        default="character_card_v2.json",
        help="Output JSON filename inside each character directory.",
    )
    parser.add_argument(
        "--png-name",
        default="character_card_v2.png",
        help="Output PNG filename inside each character directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    results_root = Path(args.results_root)
    images_root = Path(args.images_root)
    characters_json = Path(args.characters_json)
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    if not results_root.exists():
        raise SystemExit(f"results root not found: {results_root}")
    if not images_root.exists():
        raise SystemExit(f"images root not found: {images_root}")
    if not characters_json.exists():
        raise SystemExit(f"characters json not found: {characters_json}")

    safe_to_names = load_character_mapping(characters_json)
    image_dir_index = index_image_dirs(images_root)

    target_dirs = sorted(
        [
            child
            for child in results_root.iterdir()
            if child.is_dir() and (child / "role_prompt.md").exists()
        ]
    )
    if args.character:
        expected = {_safe_dir_name(value) for value in args.character}
        target_dirs = [path for path in target_dirs if _safe_dir_name(path.name) in expected]

    if not target_dirs:
        raise SystemExit("No target character directories found.")

    for character_dir in target_dirs:
        safe_key = _safe_dir_name(character_dir.name)
        role_prompt_path = character_dir / "role_prompt.md"
        sections = parse_role_prompt_sections(role_prompt_path)

        cn_name, _en_name = safe_to_names.get(
            safe_key, (character_dir.name.replace("_", " "), character_dir.name.replace("_", " "))
        )

        image_dir = image_dir_index.get(safe_key)
        if image_dir is None:
            raise FileNotFoundError(
                f"Cannot find matching image directory for {character_dir.name} under {images_root}"
            )
        avatar_png = pick_avatar_png(image_dir)

        card_payload = build_card_payload(
            name_cn=cn_name,
            sections=sections,
            creator=args.creator,
            tags=tags,
            role_prompt_path=role_prompt_path,
        )
        card_json_text = json.dumps(card_payload, ensure_ascii=False, indent=2)

        out_json = character_dir / args.json_name
        out_png = character_dir / args.png_name
        out_json.write_text(card_json_text, encoding="utf-8")
        write_png_card(avatar_png, out_png, card_json_text)
        print(f"[ok] {character_dir.name} -> {out_json} | {out_png} (avatar: {avatar_png.name})")


if __name__ == "__main__":
    main()
