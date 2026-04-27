import os
import xml.etree.ElementTree as ET

from engine.kicad_parser import infer_component_type
from engine.pcb_model import PCB, Component, Pad, TraceSegment


def parse_eagle_schematic_file(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    pcb = PCB(filename=os.path.basename(filepath))
    pcb.source_format = "eagle_schematic"
    pcb.add_layer("Schematic")

    parts = {part.attrib.get("name", ""): dict(part.attrib) for part in root.findall(".//part")}
    first_instances = {}
    for instance in root.findall(".//instance"):
        part_name = instance.attrib.get("part", "")
        if part_name and part_name not in first_instances:
            first_instances[part_name] = instance.attrib

    components = {}
    for part_name, part_meta in parts.items():
        instance = first_instances.get(part_name, {})
        x = _safe_float(instance.get("x"))
        y = _safe_float(instance.get("y"))
        value = part_meta.get("value") or part_meta.get("deviceset") or part_name
        footprint = _build_footprint_label(part_meta)
        component = Component(
            ref=part_name,
            value=value,
            x=x,
            y=y,
            layer="Schematic",
            comp_type=infer_component_type(part_name, value),
            footprint=footprint,
            rotation=_rotation_from_instance(instance.get("rot")),
        )
        components[part_name] = component
        pcb.add_component(component)

    net_wire_count = 0
    pinref_count = 0
    label_count = 0
    segment_count = 0

    for net in root.findall(".//net"):
        net_name = str(net.attrib.get("name") or "").strip() or "EAGLE_NET"
        pcb.ensure_net(net_name)
        for segment in net.findall("./segment"):
            segment_count += 1
            for child in list(segment):
                if child.tag == "pinref":
                    pinref_count += 1
                    _attach_pinref(components, pcb, net_name, child.attrib)
                elif child.tag == "wire":
                    net_wire_count += 1
                    _attach_wire(pcb, net_name, child.attrib)
                elif child.tag == "label":
                    label_count += 1

    pcb.merge_metadata(
        "parser",
        {
            "kind": "eagle_schematic",
            "part_count": len(parts),
            "instance_count": len(first_instances),
            "segment_count": segment_count,
            "pinref_count": pinref_count,
            "wire_count": net_wire_count,
            "label_count": label_count,
        },
    )
    pcb.merge_metadata(
        "schematic",
        {
            "active": True,
            "kind": "eagle_schematic",
            "part_count": len(parts),
            "instance_count": len(first_instances),
            "component_count": len(pcb.components),
            "net_count": len(pcb.nets),
            "wire_count": net_wire_count,
            "pinref_count": pinref_count,
            "label_count": label_count,
            "summary": (
                f"Eagle schematic import recognized {len(pcb.components)} components, "
                f"{len(pcb.nets)} nets, and {net_wire_count} wire segment(s)."
            ),
        },
    )
    pcb.estimate_board_bounds()
    return pcb


def _attach_pinref(components, pcb, net_name, attrs):
    component_ref = attrs.get("part", "")
    pin_name = str(attrs.get("pin", "")).strip() or "PIN"
    component = components.get(component_ref)
    if component is None:
        component = Component(
            ref=component_ref or "UNKNOWN",
            value=component_ref or "UNKNOWN",
            x=0.0,
            y=0.0,
            layer="Schematic",
            comp_type=infer_component_type(component_ref or "U?", component_ref or "UNKNOWN"),
        )
        components[component.ref] = component
        pcb.add_component(component)

    pad = next((item for item in component.pads if item.pad_name == pin_name), None)
    if pad is None:
        pad = Pad(
            component_ref=component.ref,
            pad_name=pin_name,
            net_name=net_name,
            x=component.x,
            y=component.y,
            layer="Schematic",
        )
        component.add_pad(pad)
    else:
        pad.net_name = net_name
        component.sync_nets_from_pads()

    pcb.add_net_connection(net_name, component.ref, pin_name)


def _attach_wire(pcb, net_name, attrs):
    x1 = _safe_float(attrs.get("x1"))
    y1 = _safe_float(attrs.get("y1"))
    x2 = _safe_float(attrs.get("x2"))
    y2 = _safe_float(attrs.get("y2"))
    width = _safe_float(attrs.get("width"), 0.1524)
    pcb.add_trace_segment(
        net_name,
        TraceSegment(
            net_name=net_name,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            width=width,
            layer="Schematic",
        ),
    )


def _rotation_from_instance(value):
    token = str(value or "").strip().upper()
    digits = "".join(ch for ch in token if ch.isdigit() or ch in ".-")
    if not digits:
        return 0.0
    try:
        return float(digits)
    except ValueError:
        return 0.0


def _build_footprint_label(part_meta):
    library = str(part_meta.get("library") or "").strip()
    deviceset = str(part_meta.get("deviceset") or "").strip()
    device = str(part_meta.get("device") or "").strip()
    pieces = [item for item in (library, deviceset, device) if item]
    return ":".join(pieces)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
