import configparser
import os

from engine.kicad_parser import parse_kicad_file
from engine.kicad_schematic_parser import parse_kicad_schematic_file
from engine.pcb_model import PCB


def parse_kicad_project_file(filepath):
    parser = configparser.ConfigParser()
    with open(filepath, "r", encoding="utf-8") as file:
        raw_text = file.read()
    parser.read_string(_normalize_project_text(raw_text))

    base_dir = os.path.dirname(filepath)
    stem = os.path.splitext(os.path.basename(filepath))[0]
    companion_pcb = os.path.join(base_dir, f"{stem}.kicad_pcb")
    companion_schematic = os.path.join(base_dir, f"{stem}.kicad_sch")

    source = None
    companion_kind = "project_only"
    if os.path.exists(companion_pcb):
        source = parse_kicad_file(companion_pcb)
        companion_kind = "pcb"
    elif os.path.exists(companion_schematic):
        source = parse_kicad_schematic_file(companion_schematic)
        companion_kind = "schematic"
    else:
        source = PCB(filename=os.path.basename(filepath))
        source.source_format = "kicad_project"

    source.filename = os.path.basename(filepath)
    source.source_format = "kicad_project"

    root = dict(parser.items("__root__")) if parser.has_section("__root__") else {}
    general = dict(parser.items("general")) if parser.has_section("general") else {}
    pcbnew = dict(parser.items("pcbnew")) if parser.has_section("pcbnew") else {}
    copper_layers = _safe_int(pcbnew.get("copperlayercount"), default=0)
    board_thickness = _safe_float(pcbnew.get("boardthickness"), default=0.0)

    source.merge_metadata(
        "project",
        {
            "active": True,
            "companion_kind": companion_kind,
            "companion_pcb": companion_pcb if os.path.exists(companion_pcb) else None,
            "companion_schematic": companion_schematic if os.path.exists(companion_schematic) else None,
            "copper_layer_count": copper_layers,
            "board_thickness_mm": board_thickness,
            "last_client": root.get("last_client", parser.defaults().get("last_client", "")),
            "root": root,
            "general": general,
            "pcbnew": pcbnew,
            "summary": _project_summary(companion_kind, copper_layers, board_thickness),
        },
    )
    source.merge_metadata(
        "parser",
        {
            "kind": "kicad_project",
            "companion_kind": companion_kind,
        },
    )
    return source


def _project_summary(companion_kind, copper_layers, board_thickness):
    if companion_kind == "pcb":
        return (
            f"KiCad project settings resolved to a companion PCB with {copper_layers or 'unknown'} "
            f"copper layer(s) and {board_thickness or 'unknown'} mm board thickness."
        )
    if companion_kind == "schematic":
        return "KiCad project settings resolved to a companion schematic for connectivity-aware analysis."
    return "KiCad project settings were imported, but no companion PCB or schematic file was found."


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_project_text(raw_text):
    lines = raw_text.splitlines()
    normalized = []
    in_preamble = True
    for line in lines:
        stripped = line.strip()
        if in_preamble and stripped.startswith("[") and stripped.endswith("]"):
            in_preamble = False
        if in_preamble:
            normalized.append(f"DEFAULT_{len(normalized)}={stripped}" if "=" not in stripped else stripped)
        else:
            normalized.append(line)
    if not any(line.strip().startswith("[") and line.strip().endswith("]") for line in normalized):
        normalized.insert(0, "[general]")
    else:
        normalized.insert(0, "[__root__]")
    return "\n".join(normalized)
