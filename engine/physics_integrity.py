from math import log, sqrt

from engine.net_utils import is_critical_signal_net, is_power_net
from engine.risk import make_risk


COPPER_RESISTIVITY_OHM_M = 1.724e-8
SPEED_OF_LIGHT_MM_PER_PS = 0.299792458


def _safe_upper_list(values):
    return [str(value).strip().upper() for value in (values or []) if str(value).strip()]


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _effective_dielectric_constant(er, width_mm, height_mm):
    width_mm = max(_safe_float(width_mm, 0.0), 1e-6)
    height_mm = max(_safe_float(height_mm, 0.0), 1e-6)
    ratio = width_mm / height_mm
    base = (er + 1.0) / 2.0
    fringe = (er - 1.0) / 2.0
    correction = 1.0 / sqrt(1.0 + 12.0 / max(ratio, 1e-6))
    if ratio < 1.0:
        correction += 0.04 * ((1.0 - ratio) ** 2)
    return base + (fringe * correction)


def _microstrip_impedance(width_mm, height_mm, thickness_mm, er):
    width_mm = max(_safe_float(width_mm, 0.0), 1e-6)
    height_mm = max(_safe_float(height_mm, 0.0), 1e-6)
    thickness_mm = max(_safe_float(thickness_mm, 0.0), 1e-6)
    er = max(_safe_float(er, 4.2), 1.01)

    width_eff = width_mm + (
        (thickness_mm / 3.14159) * (1.0 + log(max((4.0 * 3.14159 * width_mm) / thickness_mm, 1.0001)))
    )
    ratio = width_eff / height_mm
    er_eff = _effective_dielectric_constant(er, width_eff, height_mm)

    if ratio <= 1.0:
        impedance = (60.0 / sqrt(er_eff)) * log((8.0 / ratio) + (ratio / 4.0))
    else:
        impedance = (120.0 * 3.14159) / (
            sqrt(er_eff) * (ratio + 1.393 + (0.667 * log(max(ratio + 1.444, 1.0001))))
        )
    return max(round(impedance, 2), 1.0), round(er_eff, 3)


def _trace_resistance_ohms(length_mm, width_mm, copper_thickness_mm):
    length_m = max(_safe_float(length_mm, 0.0), 0.0) / 1000.0
    area_m2 = max(_safe_float(width_mm, 0.0), 1e-6) * max(_safe_float(copper_thickness_mm, 0.0), 1e-6) * 1e-6
    return (COPPER_RESISTIVITY_OHM_M * length_m) / area_m2


def _via_inductance_nh(via_count, board_thickness_mm, drill_mm):
    via_count = max(int(via_count or 0), 0)
    if via_count <= 0:
        return 0.0
    board_thickness_mm = max(_safe_float(board_thickness_mm, 1.6), 0.1)
    drill_mm = max(_safe_float(drill_mm, 0.25), 0.05)
    per_via = 5.08 * board_thickness_mm * (log(max((4.0 * board_thickness_mm) / drill_mm, 1.0001)) + 1.0)
    return round(per_via * via_count, 2)


def _estimated_current_for_net(net_name, config):
    net_name = str(net_name or "").strip().upper()
    current_map = (config.get("physics", {}) or {}).get("current_estimate_map", {}) or {}
    for key, value in current_map.items():
        if str(key).strip().upper() in net_name:
            return _safe_float(value, 0.25)
    if any(keyword in net_name for keyword in ["VBUS", "VIN", "BATT", "PACK", "12V", "24V", "MOTOR"]):
        return 1.5
    if any(keyword in net_name for keyword in ["VCC", "VDD", "3V3", "5V"]):
        return 0.8
    return 0.25


def analyze_board_physics(pcb, config):
    config = config or {}
    physics = config.get("physics", {}) or {}
    signal_config = config.get("signal", {}) or {}
    power_config = config.get("power", {}) or {}

    dielectric_er = _safe_float(physics.get("dielectric_er", 4.2), 4.2)
    dielectric_height_mm = _safe_float(physics.get("dielectric_height_mm", 0.18), 0.18)
    copper_thickness_mm = _safe_float(physics.get("copper_thickness_mm", 0.035), 0.035)
    board_thickness_mm = _safe_float(physics.get("board_thickness_mm", 1.6), 1.6)
    target_impedance_ohms = _safe_float(physics.get("target_impedance_ohms", 50.0), 50.0)
    target_diff_impedance_ohms = _safe_float(physics.get("target_diff_impedance_ohms", 90.0), 90.0)
    impedance_tolerance_pct = _safe_float(physics.get("impedance_tolerance_pct", 12.0), 12.0)
    max_voltage_drop_mv = _safe_float(physics.get("max_voltage_drop_mv", 75.0), 75.0)
    max_current_density = _safe_float(physics.get("max_current_density_a_per_mm2", 12.0), 12.0)
    reference_rise_time_ps = _safe_float(physics.get("reference_rise_time_ps", 500.0), 500.0)

    critical_keywords = _safe_upper_list(signal_config.get("critical_nets", [])) + ["USB", "ETH", "PCIE", "DDR", "CLK", "DP", "DN"]
    power_keywords = _safe_upper_list(power_config.get("required_power_nets", [])) + ["VIN", "VBUS", "BATT", "PACK", "12V", "24V", "3V3", "5V", "VDD"]

    signal_models = []
    power_models = []
    risks = []

    for net_name, net in getattr(pcb, "nets", {}).items():
        upper_net = str(net_name or "").strip().upper()
        if not upper_net:
            continue

        total_length_mm = _safe_float(getattr(net, "total_trace_length", 0.0), 0.0)
        if total_length_mm <= 0:
            continue

        min_width_mm = getattr(net, "min_trace_width", None)
        max_width_mm = getattr(net, "max_trace_width", None)
        avg_width_mm = None
        if min_width_mm is not None and max_width_mm is not None:
            avg_width_mm = (_safe_float(min_width_mm) + _safe_float(max_width_mm)) / 2.0
        elif min_width_mm is not None:
            avg_width_mm = _safe_float(min_width_mm)
        elif max_width_mm is not None:
            avg_width_mm = _safe_float(max_width_mm)
        if not avg_width_mm or avg_width_mm <= 0:
            continue

        if is_critical_signal_net(upper_net, critical_keywords):
            impedance_ohms, er_eff = _microstrip_impedance(avg_width_mm, dielectric_height_mm, copper_thickness_mm, dielectric_er)
            target_ohms = target_diff_impedance_ohms if any(token in upper_net for token in ["DP", "DN", "USB", "ETH", "PCIE"]) else target_impedance_ohms
            mismatch_pct = round(abs(impedance_ohms - target_ohms) / max(target_ohms, 1e-6) * 100.0, 1)
            velocity = SPEED_OF_LIGHT_MM_PER_PS / sqrt(max(er_eff, 1.0001))
            delay_ps = round(total_length_mm / max(velocity, 1e-6), 1)
            electrical_ratio = round(delay_ps / max(reference_rise_time_ps, 1.0), 2)
            via_inductance_nh = _via_inductance_nh(getattr(net, "via_count", 0), board_thickness_mm, 0.25)

            signal_models.append(
                {
                    "net_name": upper_net,
                    "length_mm": round(total_length_mm, 2),
                    "average_width_mm": round(avg_width_mm, 3),
                    "impedance_ohms": impedance_ohms,
                    "target_ohms": round(target_ohms, 1),
                    "mismatch_pct": mismatch_pct,
                    "delay_ps": delay_ps,
                    "electrical_ratio": electrical_ratio,
                    "via_inductance_nh": via_inductance_nh,
                }
            )

            if mismatch_pct > impedance_tolerance_pct:
                risks.append(
                    make_risk(
                        rule_id="physics_signal_integrity",
                        category="signal_integrity",
                        severity="high" if mismatch_pct > (impedance_tolerance_pct * 1.5) else "medium",
                        message=f"Physics estimate suggests {upper_net} is off target impedance ({impedance_ohms:.1f} ohms vs {target_ohms:.1f} ohms)",
                        recommendation="Adjust trace geometry, reference height, or stackup assumptions to bring the line closer to its impedance target.",
                        nets=[upper_net],
                        metrics={
                            "estimated_impedance_ohms": impedance_ohms,
                            "target_impedance_ohms": round(target_ohms, 1),
                            "mismatch_pct": mismatch_pct,
                            "delay_ps": delay_ps,
                            "via_inductance_nh": via_inductance_nh,
                        },
                        confidence=0.84,
                        short_title="Physics-based impedance mismatch",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="signal_integrity",
                        why_it_matters="A characteristic impedance shift can create reflection, eye closure, and timing margin loss on fast nets.",
                        trigger_condition="A first-principles microstrip estimate exceeded the configured impedance tolerance.",
                        threshold_label=f"Maximum impedance mismatch {impedance_tolerance_pct:.1f}%",
                        observed_label=f"Observed mismatch {mismatch_pct:.1f}% at {impedance_ohms:.1f} ohms",
                    )
                )

        if is_power_net(upper_net, power_keywords):
            estimated_current_a = _estimated_current_for_net(upper_net, config)
            trace_resistance = _trace_resistance_ohms(total_length_mm, avg_width_mm, copper_thickness_mm)
            voltage_drop_mv = round((estimated_current_a * trace_resistance) * 1000.0, 2)
            copper_area_mm2 = max(avg_width_mm * copper_thickness_mm, 1e-6)
            current_density = round(estimated_current_a / copper_area_mm2, 2)
            power_loss_mw = round((estimated_current_a ** 2) * trace_resistance * 1000.0, 2)

            power_models.append(
                {
                    "net_name": upper_net,
                    "length_mm": round(total_length_mm, 2),
                    "average_width_mm": round(avg_width_mm, 3),
                    "estimated_current_a": round(estimated_current_a, 3),
                    "resistance_ohms": round(trace_resistance, 4),
                    "voltage_drop_mv": voltage_drop_mv,
                    "current_density_a_per_mm2": current_density,
                    "power_loss_mw": power_loss_mw,
                }
            )

            if voltage_drop_mv > max_voltage_drop_mv:
                risks.append(
                    make_risk(
                        rule_id="physics_power_integrity",
                        category="power_integrity",
                        severity="high" if voltage_drop_mv > (max_voltage_drop_mv * 1.5) else "medium",
                        message=f"Physics estimate suggests {upper_net} may incur high IR drop ({voltage_drop_mv:.1f} mV)",
                        recommendation="Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.",
                        nets=[upper_net],
                        metrics={
                            "voltage_drop_mv": voltage_drop_mv,
                            "estimated_current_a": round(estimated_current_a, 3),
                            "resistance_ohms": round(trace_resistance, 4),
                            "threshold_mv": max_voltage_drop_mv,
                        },
                        confidence=0.82,
                        short_title="Physics-based IR drop risk",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="power_integrity",
                        why_it_matters="Excess IR drop can destabilize rails under load and erode noise margin at the point of use.",
                        trigger_condition="A first-principles resistance and load estimate exceeded the configured voltage-drop limit.",
                        threshold_label=f"Maximum voltage drop {max_voltage_drop_mv:.1f} mV",
                        observed_label=f"Observed estimated drop {voltage_drop_mv:.1f} mV",
                    )
                )

            if current_density > max_current_density:
                risks.append(
                    make_risk(
                        rule_id="physics_power_density",
                        category="power_integrity",
                        severity="high",
                        message=f"Physics estimate suggests {upper_net} is running high current density ({current_density:.1f} A/mm²)",
                        recommendation="Increase copper cross-section or redistribute load current so the conductor stays in a safer density band.",
                        nets=[upper_net],
                        metrics={
                            "current_density_a_per_mm2": current_density,
                            "estimated_current_a": round(estimated_current_a, 3),
                            "cross_section_mm2": round(copper_area_mm2, 5),
                            "threshold": max_current_density,
                        },
                        confidence=0.8,
                        short_title="Physics-based current-density risk",
                        fix_priority="high",
                        estimated_impact="high",
                        design_domain="power_integrity",
                        why_it_matters="High current density raises heating, drop, and long-term reliability stress in power paths.",
                        trigger_condition="A first-principles current-density estimate exceeded the configured conductor limit.",
                        threshold_label=f"Maximum current density {max_current_density:.1f} A/mm²",
                        observed_label=f"Observed current density {current_density:.1f} A/mm²",
                    )
                )

    signal_models.sort(key=lambda item: (-item["mismatch_pct"], -item["delay_ps"], item["net_name"]))
    power_models.sort(key=lambda item: (-item["voltage_drop_mv"], -item["current_density_a_per_mm2"], item["net_name"]))

    return {
        "enabled": True,
        "assumptions": {
            "dielectric_er": dielectric_er,
            "dielectric_height_mm": dielectric_height_mm,
            "copper_thickness_mm": copper_thickness_mm,
            "board_thickness_mm": board_thickness_mm,
            "target_impedance_ohms": target_impedance_ohms,
            "target_diff_impedance_ohms": target_diff_impedance_ohms,
            "reference_rise_time_ps": reference_rise_time_ps,
            "max_voltage_drop_mv": max_voltage_drop_mv,
            "max_current_density_a_per_mm2": max_current_density,
        },
        "signal_models": signal_models[:8],
        "power_models": power_models[:8],
        "summary": {
            "signal_nets_modeled": len(signal_models),
            "power_nets_modeled": len(power_models),
            "worst_impedance_mismatch_pct": signal_models[0]["mismatch_pct"] if signal_models else 0.0,
            "worst_voltage_drop_mv": power_models[0]["voltage_drop_mv"] if power_models else 0.0,
        },
        "risks": risks,
    }
