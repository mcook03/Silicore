def suggest_fix(risk):
    if not isinstance(risk, dict):
        return {
            "fix": "Manual review required",
            "priority": "medium"
        }

    rule_id = str(risk.get("rule_id", "") or "").lower()
    category = str(risk.get("category", "") or "").lower()
    severity = str(risk.get("severity", "medium") or "medium").lower()
    message = str(risk.get("message", "") or "").lower()
    metrics = risk.get("metrics", {}) or {}

    priority = _priority_from_severity(severity)

    if rule_id == "decoupling":
        threshold = metrics.get("threshold")
        if threshold is not None:
            return {
                "fix": f"Place a 0.1uF decoupling capacitor close to the IC power pin, ideally within the configured threshold of {threshold}.",
                "priority": priority
            }
        return {
            "fix": "Place a 0.1uF decoupling capacitor close to the IC power pin and connect it directly to the relevant power and ground nets.",
            "priority": priority
        }

    if rule_id == "power_distribution":
        distance = metrics.get("distance")
        if distance is not None:
            return {
                "fix": f"Move the regulator closer to the load or reduce the power path length from its current distance of {distance}. Also consider wider copper or a lower-impedance distribution path.",
                "priority": priority
            }
        return {
            "fix": "Move the regulator closer to the load or improve the power delivery path with wider copper and fewer high-impedance transitions.",
            "priority": priority
        }

    if rule_id == "power_rail":
        if "excessive routed length" in message:
            length_value = metrics.get("trace_length")
            if length_value is not None:
                return {
                    "fix": f"Shorten the power route and improve placement to reduce the current routed length of {length_value}.",
                    "priority": priority
                }
            return {
                "fix": "Shorten the power routing path by improving placement and simplifying distribution topology.",
                "priority": priority
            }

        if "narrow trace width" in message:
            width_value = metrics.get("trace_width")
            minimum_expected = metrics.get("minimum_expected")
            if width_value is not None and minimum_expected is not None:
                return {
                    "fix": f"Increase the power trace width from {width_value} to at least {minimum_expected} or more, depending on current demand.",
                    "priority": priority
                }
            return {
                "fix": "Increase the power trace width to reduce resistance, voltage drop, and heating.",
                "priority": priority
            }

        if "many vias" in message:
            via_count = metrics.get("via_count")
            threshold = metrics.get("threshold")
            if via_count is not None and threshold is not None:
                return {
                    "fix": f"Reduce via transitions on this power net. It currently uses {via_count} vias versus a threshold of {threshold}.",
                    "priority": priority
                }
            return {
                "fix": "Reduce unnecessary via transitions on the power path to lower impedance.",
                "priority": priority
            }

        if "too few connections" in message:
            return {
                "fix": "Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.",
                "priority": priority
            }

        return {
            "fix": "Review the power rail routing, width, and topology to reduce impedance and improve delivery.",
            "priority": priority
        }

    if rule_id == "trace_quality":
        if "very narrow trace" in message or "narrow trace" in message:
            min_trace_width = metrics.get("min_trace_width")
            threshold = metrics.get("threshold")
            if min_trace_width is not None and threshold is not None:
                return {
                    "fix": f"Increase the narrow trace width from {min_trace_width} to at least {threshold}, subject to board-space and fabrication constraints.",
                    "priority": priority
                }
            return {
                "fix": "Increase trace width and review the route against fabrication limits and current-carrying needs.",
                "priority": priority
            }

        if "long total routed trace length" in message:
            trace_length = metrics.get("trace_length")
            threshold = metrics.get("threshold")
            if trace_length is not None and threshold is not None:
                return {
                    "fix": f"Reduce total routed trace length from {trace_length} toward or below {threshold} by tightening placement and simplifying the route.",
                    "priority": priority
                }
            return {
                "fix": "Reduce total routed trace length by improving placement and removing unnecessary detours.",
                "priority": priority
            }

        return {
            "fix": "Review trace geometry, width, and route complexity to improve signal quality and manufacturability.",
            "priority": priority
        }

    if rule_id == "spacing":
        distance = metrics.get("distance")
        threshold = metrics.get("threshold")
        if distance is not None and threshold is not None:
            return {
                "fix": f"Increase spacing between the affected components from {distance} to at least {threshold}.",
                "priority": priority
            }
        return {
            "fix": "Increase spacing between the affected components to improve routing clearance and manufacturability.",
            "priority": priority
        }

    if rule_id == "signal_path":
        distance = metrics.get("distance")
        threshold = metrics.get("threshold")
        if distance is not None and threshold is not None:
            return {
                "fix": f"Reduce the signal path length from {distance} to at or below {threshold} by improving placement or rerouting.",
                "priority": priority
            }
        return {
            "fix": "Reduce signal path length by placing communicating components closer together or simplifying routing.",
            "priority": priority
        }

    if rule_id == "net_length":
        distance = metrics.get("distance")
        threshold = metrics.get("threshold")
        if distance is not None and threshold is not None:
            return {
                "fix": f"Shorten the net path from {distance} toward {threshold} or below by improving placement or route topology.",
                "priority": priority
            }
        return {
            "fix": "Shorten the net path and reduce unnecessary routing detours.",
            "priority": priority
        }

    if rule_id == "ground_reference":
        return {
            "fix": "Ensure the component has a valid ground reference and a clear low-impedance return path to the board ground network.",
            "priority": priority
        }

    if rule_id == "return_path":
        return {
            "fix": "Route the signal closer to a continuous ground reference and reduce gaps, layer transitions, or broken return paths.",
            "priority": priority
        }

    if rule_id == "power_connectivity":
        return {
            "fix": "Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.",
            "priority": priority
        }

    if rule_id == "density":
        return {
            "fix": "Spread components more evenly in the crowded region to reduce congestion and make routing and assembly easier.",
            "priority": priority
        }

    if rule_id == "thermal":
        return {
            "fix": "Increase spacing between hot components or add more copper area, thermal relief, or airflow-aware placement to reduce hotspot risk.",
            "priority": priority
        }

    if category == "power_integrity":
        return {
            "fix": "Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.",
            "priority": priority
        }

    if category == "signal_integrity":
        return {
            "fix": "Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.",
            "priority": priority
        }

    if category == "layout":
        return {
            "fix": "Adjust component placement to improve spacing, routing access, and overall board organization.",
            "priority": priority
        }

    if category == "manufacturing":
        return {
            "fix": "Review the board against fabrication limits and increase trace widths or spacing where necessary.",
            "priority": priority
        }

    if category == "thermal":
        return {
            "fix": "Improve thermal distribution with better spacing, copper spreading, or thermal-aware placement.",
            "priority": priority
        }

    if category == "emi_return_path":
        return {
            "fix": "Improve grounding and return-path continuity to reduce reference instability and EMI risk.",
            "priority": priority
        }

    return {
        "fix": risk.get("recommendation", "Manual review required"),
        "priority": priority
    }


def _priority_from_severity(severity):
    severity = str(severity or "").lower()

    if severity == "critical":
        return "critical"
    if severity == "high":
        return "high"
    if severity == "medium":
        return "medium"
    return "low"