# SILICORE ENGINEERING REPORT

- File: high_speed_pair_bad.kicad_pcb
- Score: 7.0 / 100
- Total Risks: 35
- Total Penalty: 164.0

## Executive Summary

**Board needs focused engineering review**

This board shows moderate design risk. The main risk concentration is in signal integrity. The highest-priority issue is High-voltage pad on J1:VBUS is close to J1:USB_DP. The current design snapshot includes 3 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: engineering review packet
- Includes: score rationale, finding traceability, recommendations, and saved analysis context
- Best use: design reviews, management updates, supplier communication, and internal signoff

## Top Issues

1. **CRITICAL** — safety_high_voltage — High-voltage pad on J1:VBUS is close to J1:USB_DP
   - Recommendation: Increase conductor spacing or introduce isolation features that meet the intended voltage-class clearance target.
2. **HIGH** — emi_emc — Fast or noisy net USB_DP changes layers without nearby return-path stitching support
   - Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
3. **HIGH** — emi_emc — Fast or noisy net USB_DN changes layers without nearby return-path stitching support
   - Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.

## Board Summary

- Component Count: 3
- Net Count: 5
- Risk Count: 35
- Sample Components: J1, U1, Y1

## Severity Penalties

- medium: 10.4
- high: 4.8
- critical: 1.2

## Category Penalties

- assembly_testability: 2.0
- signal_integrity: 3.4
- component_design: 0.8
- power_integrity: 3.2
- high_speed: 0.6
- emi_emc: 1.6
- manufacturing: 0.8
- reliability: 0.8
- safety_high_voltage: 1.2
- stackup_return_path: 2.0

## Detailed Findings

### MEDIUM — assembly_testability
- Message: Board has limited visible fiducial strategy for assembly alignment
- Recommendation: Add global fiducials to improve assembly registration and inspection consistency.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2
- Traceability: 86 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 76.0 / 100
- Suggested Fix: Add global fiducials to improve assembly registration and inspection consistency.
- Fix Priority: medium
- Metrics: {"fiducials": 0, "threshold": 2}

### MEDIUM — assembly_testability
- Message: Ground test-point coverage appears limited for bring-up and probing
- Recommendation: Add at least one accessible ground test point so probing and scope reference setup are easier during bring-up.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.81
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=1
- Traceability: 86 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 81.0 / 100
- Suggested Fix: Add at least one accessible ground test point so probing and scope reference setup are easier during bring-up.
- Fix Priority: medium
- Metrics: {"ground_test_points": 0, "threshold": 1}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net USB_DP has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net USB_DN has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net CLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: U1, Y1
- Nets: CLK
- Metrics: {"has_testpoint": false}

### HIGH — signal_integrity
- Message: Clock source Y1 is far from controller U1 (19.80 units)
- Recommendation: Move the crystal or oscillator closer to the controller clock pins and keep the timing loop compact and isolated.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=19.8, threshold=12.0
- Traceability: 100 / 100
- Evidence Count: 10
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 84.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Components: Y1, U1
- Nets: CLK, GND
- Metrics: {"distance": 19.8, "threshold": 12.0, "shares_clock_net": true}

### MEDIUM — component_design
- Message: High-speed net USB_DN has a long route with no visible series or termination resistor
- Recommendation: Review whether this interface requires termination or series damping based on edge rate and topology.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=18.0
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this interface requires termination or series damping based on edge rate and topology.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"trace_length": 118.2, "threshold": 18.0, "has_resistor": false}

### MEDIUM — component_design
- Message: High-speed net USB_DP has a long route with no visible series or termination resistor
- Recommendation: Review whether this interface requires termination or series damping based on edge rate and topology.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=18.0
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this interface requires termination or series damping based on edge rate and topology.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"trace_length": 84.67, "threshold": 18.0, "has_resistor": false}

### HIGH — power_integrity
- Message: High-current net VBUS bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Components: J1
- Nets: VBUS
- Metrics: {"min_width": 0.25, "recommended_width": 0.7, "trace_length": 84.02}

### MEDIUM — power_integrity
- Message: U1 (mcu) has no nearby decoupling capacitor
- Recommendation: Place a decoupling capacitor close to the device power pin and on the relevant supply net.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4.0
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 90.0 / 100
- Suggested Fix: Place a 0.1uF decoupling capacitor close to the IC power pin, ideally within the configured threshold of 4.0.
- Fix Priority: medium
- Components: U1, J1
- Metrics: {"nearest_cap_distance": 84.02, "threshold": 4.0}

### HIGH — power_integrity
- Message: U1 appears to lack enough local decoupling support
- Recommendation: Add or reposition local bypass capacitors close to the device supply pins with short return paths.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.87
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 11
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 87.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Components: U1
- Nets: CLK, USB_DN, GND, USB_DP
- Metrics: {"local_caps_found": 0, "min_local_caps": 1, "nearest_local_cap_distance": null}

### HIGH — high_speed
- Message: Differential pair USB has a length mismatch of 33.53 units
- Recommendation: Length-match the positive and negative pair routes more closely to reduce skew.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5.0
- Traceability: 94 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Length-match the positive and negative pair routes more closely to reduce skew.
- Fix Priority: high
- Nets: USB_DP, USB_DN
- Metrics: {"positive_length": 84.67, "negative_length": 118.2, "length_mismatch": 33.53, "threshold": 5.0}

### MEDIUM — emi_emc
- Message: Switching or power net VBUS forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Components: J1
- Nets: VBUS
- Metrics: {"trace_length": 84.02, "max_loop_length": 45.0, "via_count": 0}

### HIGH — emi_emc
- Message: Fast or noisy net USB_DP changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"unsupported_vias": 2, "return_via_radius": 3.0, "trace_length": 84.67}

### HIGH — emi_emc
- Message: Fast or noisy net USB_DN changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"unsupported_vias": 2, "return_via_radius": 3.0, "trace_length": 118.2}

### MEDIUM — manufacturing
- Message: Net CLK uses a trace width below the fab-oriented limit (0.12)
- Recommendation: Increase the trace width or confirm that the chosen board house can reliably build this geometry.
- Root Cause: Design rule below fabrication limits
- Impact: Reduced yield or board failure risk
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.15
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Reduced yield or board failure risk
- Trust Confidence: 90.0 / 100
- Suggested Fix: Review the board against fabrication limits and increase trace widths or spacing where necessary.
- Fix Priority: medium
- Nets: CLK
- Metrics: {"trace_width": 0.12, "threshold": 0.15}

### MEDIUM — signal_integrity
- Message: Net USB_DP has a long path between J1 and U1 (84.02 units)
- Recommendation: Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=84.02, threshold=25.0
- Traceability: 66 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Shorten the net path from 84.02 toward 25.0 or below by improving placement or route topology.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"distance": 84.02, "threshold": 25.0, "is_critical_net": false}

### MEDIUM — signal_integrity
- Message: Net USB_DN has a long path between J1 and U1 (84.02 units)
- Recommendation: Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=84.02, threshold=25.0
- Traceability: 66 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Shorten the net path from 84.02 toward 25.0 or below by improving placement or route topology.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"distance": 84.02, "threshold": 25.0, "is_critical_net": false}

### MEDIUM — power_integrity
- Message: J1 has ground but no visible power rail
- Recommendation: Verify that the component is connected to the intended supply net as well as ground.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 10
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 70.0 / 100
- Suggested Fix: Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.
- Fix Priority: medium
- Components: J1
- Nets: USB_DN, GND, VBUS, USB_DP
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["USB_DN", "GND", "VBUS", "USB_DP"], "has_power": false, "has_ground": true}

### MEDIUM — power_integrity
- Message: U1 has ground but no visible power rail
- Recommendation: Verify that the component is connected to the intended supply net as well as ground.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 10
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 70.0 / 100
- Suggested Fix: Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.
- Fix Priority: medium
- Components: U1
- Nets: CLK, USB_DN, GND, USB_DP
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["CLK", "USB_DN", "GND", "USB_DP"], "has_power": false, "has_ground": true}

### MEDIUM — power_integrity
- Message: Y1 has ground but no visible power rail
- Recommendation: Verify that the component is connected to the intended supply net as well as ground.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 70.0 / 100
- Suggested Fix: Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.
- Fix Priority: medium
- Components: Y1
- Nets: CLK, GND
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["CLK", "GND"], "has_power": false, "has_ground": true}

### MEDIUM — power_integrity
- Message: High-current net VBUS uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 100 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Components: J1
- Nets: VBUS
- Metrics: {"trace_length": 84.02, "threshold": 40.0}

### MEDIUM — reliability
- Message: Ground strategy looks light on stitching support for net GND (0 vias)
- Recommendation: Add more stitching or reference vias to strengthen grounding continuity and return-current robustness.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add more stitching or reference vias to strengthen grounding continuity and return-current robustness.
- Fix Priority: medium
- Nets: GND
- Metrics: {"ground_via_count": 0, "threshold": 2, "board_layers": 2}

### MEDIUM — reliability
- Message: Ground net GND has limited visible connectivity (3 connections)
- Recommendation: Review grounding strategy and ensure intended loads and returns are visibly tied into the board ground structure.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Review grounding strategy and ensure intended loads and returns are visibly tied into the board ground structure.
- Fix Priority: medium
- Nets: GND
- Metrics: {"ground_connections": 3, "threshold": 4}

### CRITICAL — safety_high_voltage
- Message: High-voltage pad on J1:VBUS is close to J1:USB_DP
- Recommendation: Increase conductor spacing or introduce isolation features that meet the intended voltage-class clearance target.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 83.0 / 100
- Suggested Fix: Increase conductor spacing or introduce isolation features that meet the intended voltage-class clearance target.
- Fix Priority: critical
- Components: J1, J1
- Nets: VBUS, USB_DP
- Metrics: {"clearance": 1.8, "min_clearance": 2.5}

### MEDIUM — signal_integrity
- Message: Net USB_DP has a long signal path between J1 and U1 (84.02 units)
- Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=84.02, threshold=25.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce the signal path length from 84.02 to at or below 25.0 by improving placement or rerouting.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"distance": 84.02, "threshold": 25.0}

### MEDIUM — signal_integrity
- Message: Net USB_DN has a long signal path between J1 and U1 (84.02 units)
- Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=84.02, threshold=25.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce the signal path length from 84.02 to at or below 25.0 by improving placement or rerouting.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"distance": 84.02, "threshold": 25.0}

### MEDIUM — stackup_return_path
- Message: Critical net USB_DP is long for a two-layer style stackup
- Recommendation: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=28.0
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"trace_length": 84.67, "threshold": 28.0, "copper_layers": 2}

### HIGH — stackup_return_path
- Message: Critical net USB_DP changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Components: J1, U1
- Nets: USB_DP
- Metrics: {"unsupported_vias": 2, "signal_via_ground_radius": 3.5}

### MEDIUM — stackup_return_path
- Message: Critical net USB_DN is long for a two-layer style stackup
- Recommendation: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=28.0
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Fix Priority: medium
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"trace_length": 118.2, "threshold": 28.0, "copper_layers": 2}

### HIGH — stackup_return_path
- Message: Critical net USB_DN changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Components: J1, U1
- Nets: USB_DN
- Metrics: {"unsupported_vias": 2, "signal_via_ground_radius": 3.5}

### MEDIUM — signal_integrity
- Message: Net VBUS has a long total routed trace length (84.02 units)
- Recommendation: Review routing topology and shorten critical signal traces where practical.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=60.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce total routed trace length from 84.02380615040002 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: VBUS
- Metrics: {"trace_length": 84.02380615040002, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net USB_DP has a long total routed trace length (84.67 units)
- Recommendation: Review routing topology and shorten critical signal traces where practical.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=60.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce total routed trace length from 84.67372197262105 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: USB_DP
- Metrics: {"trace_length": 84.67372197262105, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net USB_DN has a long total routed trace length (118.20 units)
- Recommendation: Review routing topology and shorten critical signal traces where practical.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=60.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce total routed trace length from 118.2 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: USB_DN
- Metrics: {"trace_length": 118.2, "threshold": 60.0}

### MEDIUM — manufacturing
- Message: Net CLK contains a very narrow trace (0.12)
- Recommendation: Review manufacturability limits and increase trace width if the design rules require it.
- Root Cause: Design rule below fabrication limits
- Impact: Reduced yield or board failure risk
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.15
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Reduced yield or board failure risk
- Trust Confidence: 83.0 / 100
- Suggested Fix: Increase the narrow trace width from 0.12 to at least 0.15, subject to board-space and fabrication constraints.
- Fix Priority: medium
- Nets: CLK
- Metrics: {"min_trace_width": 0.12, "threshold": 0.15}
