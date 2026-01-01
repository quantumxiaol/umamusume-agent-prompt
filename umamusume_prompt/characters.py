from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


def load_characters(json_path: Path) -> Dict[str, str]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("characters json must be an object mapping cn to en")
    return {str(k): str(v) for k, v in data.items() if k and v}


def resolve_character(name: str, mapping: Dict[str, str]) -> Tuple[str, str, bool]:
    if name in mapping:
        return name, mapping[name], True
    name_lower = name.lower()
    for cn, en in mapping.items():
        if en.lower() == name_lower:
            return cn, en, True
    return name, name, False
