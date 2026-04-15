from collections import Counter


REFERENCE_LAYER_HINTS = {"gnd", "ground", "gnd1", "gnd2", "power", "pwr", "plane"}


def derive_stackup_summary(pcb, board_type="general"):
    layers = list(getattr(pcb, "declared_layers", []) or list(getattr(pcb, "layers", []) or []))
    trace_layers = [str(getattr(trace, "layer", "") or "") for trace in (getattr(pcb, "traces", []) or []) if getattr(trace, "layer", None)]
    if not layers:
        layers = sorted(set(trace_layers)) or ["F.Cu", "B.Cu"]

    layer_counts = Counter(trace_layers)
    copper_layers = [layer for layer in layers if ".Cu" in layer or "layer" in layer.lower()]
    signal_layers = [layer for layer in copper_layers if not any(hint in layer.lower() for hint in REFERENCE_LAYER_HINTS)]
    reference_layers = [layer for layer in copper_layers if any(hint in layer.lower() for hint in REFERENCE_LAYER_HINTS)]
    if not reference_layers and len(copper_layers) >= 2:
        reference_layers = [copper_layers[1]]

    style = "two_layer" if len(copper_layers) <= 2 else "multilayer"
    reference_coverage = round(min(100.0, (len(reference_layers) / max(len(copper_layers), 1)) * 100.0), 1)

    concerns = []
    if style == "two_layer":
        concerns.append("Two-layer stackup limits return-path containment on fast or sensitive nets.")
    if not reference_layers:
        concerns.append("No dedicated reference layer was inferred from the current board data.")
    if board_type in {"high_speed", "mixed_signal"} and reference_coverage < 35:
        concerns.append("Reference-plane coverage looks light for this board class.")

    return {
        "layer_count": len(layers),
        "copper_layers": copper_layers,
        "signal_layers": signal_layers,
        "reference_layers": reference_layers,
        "style": style,
        "reference_coverage_pct": reference_coverage,
        "dominant_signal_layer": max(layer_counts, key=layer_counts.get) if layer_counts else (signal_layers[0] if signal_layers else "F.Cu"),
        "concerns": concerns,
    }
