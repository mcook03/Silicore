import os
import re

from engine.pcb_model import PCB, Component, OutlineSegment, Pad
from engine.kicad_parser import infer_component_type


def parse_kicad_module_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    pcb = PCB(filename=os.path.basename(filepath))
    pcb.source_format = "kicad_footprint"

    module_match = re.search(r'\((?:module|footprint)\s+([^\s\)]+)', content)
    layer_match = re.search(r'\(layer\s+([^\s\)"]+|"[^"]+")\)', content)
    ref_match = re.search(r'\(fp_text\s+reference\s+([^\s\)"]+|"[^"]+")', content)
    value_match = re.search(r'\(fp_text\s+value\s+([^\s\)"]+|"[^"]+")', content)

    module_name = _clean_token(module_match.group(1)) if module_match else os.path.splitext(os.path.basename(filepath))[0]
    layer = _clean_token(layer_match.group(1)) if layer_match else "F.Cu"
    ref = _clean_token(ref_match.group(1)) if ref_match else "REF**"
    value = _clean_token(value_match.group(1)) if value_match else module_name

    component = Component(
        ref=ref,
        value=value,
        x=0.0,
        y=0.0,
        layer=layer,
        comp_type=infer_component_type(ref, value),
        footprint=module_name,
        rotation=0.0,
    )

    pad_pattern = re.compile(
        r'\(pad\s+"?([^"\s]+)"?\s+\S+\s+\S+\s+'
        r'\(at\s+([-\d\.]+)\s+([-\d\.]+)(?:\s+[-\d\.]+)?\)\s+'
        r'\(size\s+([-\d\.]+)\s+([-\d\.]+)\)\s+'
        r'\(layers\s+([^)]+)\)',
        re.DOTALL,
    )
    for match in pad_pattern.finditer(content):
        pad_name = match.group(1)
        pad_x = float(match.group(2))
        pad_y = float(match.group(3))
        size_x = float(match.group(4))
        size_y = float(match.group(5))
        pad_layers = match.group(6).replace('"', "").split()
        component.add_pad(
            Pad(
                component_ref=ref,
                pad_name=pad_name,
                net_name=None,
                x=pad_x,
                y=pad_y,
                layer=",".join(pad_layers),
                size_x=size_x,
                size_y=size_y,
            )
        )

    line_pattern = re.compile(
        r'\(fp_line\s+\(start\s+([-\d\.]+)\s+([-\d\.]+)\)\s+\(end\s+([-\d\.]+)\s+([-\d\.]+)\)\s+\(layer\s+([^\s\)"]+|"[^"]+")\)'
    )
    for match in line_pattern.finditer(content):
        outline_layer = _clean_token(match.group(5))
        pcb.add_outline_segment(
            OutlineSegment(
                x1=match.group(1),
                y1=match.group(2),
                x2=match.group(3),
                y2=match.group(4),
                layer=outline_layer,
                kind="line",
            )
        )

    pcb.add_component(component)
    pcb.merge_metadata(
        "footprint",
        {
            "active": True,
            "module_name": module_name,
            "reference_template": ref,
            "value_template": value,
            "pad_count": len(component.pads),
            "outline_count": len(pcb.outline_segments),
            "summary": (
                f"KiCad footprint import recognized {len(component.pads)} pad(s) and "
                f"{len(pcb.outline_segments)} outline segment(s) for {module_name}."
            ),
        },
    )
    pcb.merge_metadata(
        "parser",
        {
            "kind": "kicad_footprint",
            "pad_count": len(component.pads),
        },
    )
    pcb.estimate_board_bounds()
    return pcb


def _clean_token(value):
    return str(value or "").strip().strip('"')
