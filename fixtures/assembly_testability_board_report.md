# SILICORE ENGINEERING REPORT

- File: assembly_testability_board.kicad_pcb
- Score: 8.8 / 100
- Total Risks: 30
- Total Penalty: 130.0

## Executive Summary

**Board needs focused engineering review**

This board shows moderate design risk. The main risk concentration is in power integrity. The highest-priority issue is Physics estimate suggests SWCLK is off target impedance (78.7 ohms vs 50.0 ohms). The current design snapshot includes 4 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: engineering review packet
- Includes: score rationale, finding traceability, recommendations, and saved analysis context
- Best use: design reviews, management updates, supplier communication, and internal signoff

## Top Issues

1. **HIGH** — signal_integrity — Physics estimate suggests SWCLK is off target impedance (78.7 ohms vs 50.0 ohms)
   - Recommendation: Adjust trace geometry, reference height, or stackup assumptions to bring the line closer to its impedance target.
2. **HIGH** — power_integrity — Physics estimate suggests VCC is running high current density (142.9 A/mm²)
   - Recommendation: Increase copper cross-section or redistribute load current so the conductor stays in a safer density band.
3. **HIGH** — power_integrity — High-current net SWDIO bottlenecks through a narrow copper section
   - Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.

## Board Summary

- Component Count: 4
- Net Count: 5
- Risk Count: 30
- Sample Components: U1, J1, C1, R1

## Severity Penalties

- medium: 9.2
- high: 3.6
- low: 0.2

## Category Penalties

- assembly_testability: 2.0
- component_design: 0.4
- power_integrity: 4.2
- manufacturing: 3.2
- signal_integrity: 2.6
- stackup_return_path: 0.4
- system_interaction: 0.2

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
- Message: Critical or debug-oriented net SWDIO has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: U1
- Nets: SWDIO
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net SWCLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: U1
- Nets: SWCLK
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net UART_TX has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Components: U1, J1, R1
- Nets: UART_TX
- Metrics: {"has_testpoint": false}

### MEDIUM — component_design
- Message: High-speed net SWCLK has a long route with no visible series or termination resistor
- Recommendation: Review whether this interface requires termination or series damping based on edge rate and topology.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=18.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this interface requires termination or series damping based on edge rate and topology.
- Fix Priority: medium
- Components: U1
- Nets: SWCLK
- Metrics: {"trace_length": 28.28, "threshold": 18.0, "has_resistor": false}

### HIGH — power_integrity
- Message: High-current net SWDIO bottlenecks through a narrow copper section
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
- Components: U1
- Nets: SWDIO
- Metrics: {"min_width": 0.1, "recommended_width": 0.7, "trace_length": 31.05}

### HIGH — power_integrity
- Message: High-current net SWCLK bottlenecks through a narrow copper section
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
- Components: U1
- Nets: SWCLK
- Metrics: {"min_width": 0.1, "recommended_width": 0.7, "trace_length": 28.28}

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
- Components: U1, C1
- Metrics: {"nearest_cap_distance": 6.32, "threshold": 4.0}

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
- Nets: VCC, UART_TX, SWCLK, GND
- Metrics: {"local_caps_found": 0, "min_local_caps": 1, "nearest_local_cap_distance": null}

### MEDIUM — manufacturing
- Message: Net GND uses a trace width below the fab-oriented limit (0.14)
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
- Nets: GND
- Metrics: {"trace_width": 0.14, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net SWDIO uses a trace width below the fab-oriented limit (0.10)
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
- Nets: SWDIO
- Metrics: {"trace_width": 0.1, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net SWCLK uses a trace width below the fab-oriented limit (0.10)
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
- Nets: SWCLK
- Metrics: {"trace_width": 0.1, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net UART_TX uses a trace width below the fab-oriented limit (0.12)
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
- Nets: UART_TX
- Metrics: {"trace_width": 0.12, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net UART_TX uses a trace width below the fab-oriented limit (0.12)
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
- Nets: UART_TX
- Metrics: {"trace_width": 0.12, "threshold": 0.15}

### MEDIUM — signal_integrity
- Message: Net UART_TX has a long path between U1 and J1 (37.95 units)
- Recommendation: Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=37.95, threshold=25.0
- Traceability: 66 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Shorten the net path from 37.95 toward 25.0 or below by improving placement or route topology.
- Fix Priority: medium
- Components: U1, J1
- Nets: UART_TX
- Metrics: {"distance": 37.95, "threshold": 25.0, "is_critical_net": false}

### MEDIUM — signal_integrity
- Message: Net UART_TX has a long path between J1 and R1 (34.18 units)
- Recommendation: Reduce routing distance, improve placement, or treat the net as timing-sensitive if appropriate.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=34.18, threshold=25.0
- Traceability: 66 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 78.0 / 100
- Suggested Fix: Shorten the net path from 34.18 toward 25.0 or below by improving placement or route topology.
- Fix Priority: medium
- Components: J1, R1
- Nets: UART_TX
- Metrics: {"distance": 34.18, "threshold": 25.0, "is_critical_net": false}

### MEDIUM — power_integrity
- Message: J1 has ground but no visible power rail
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
- Components: J1
- Nets: UART_TX, GND
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["UART_TX", "GND"], "has_power": false, "has_ground": true}

### MEDIUM — power_integrity
- Message: R1 has ground but no visible power rail
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
- Components: R1
- Nets: UART_TX, GND
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["UART_TX", "GND"], "has_power": false, "has_ground": true}

### HIGH — power_integrity
- Message: Power net VCC uses a narrow trace width (0.16)
- Recommendation: Increase power trace width to reduce resistance, heating, and voltage drop.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the power trace width from 0.16 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: VCC
- Metrics: {"trace_width": 0.16, "minimum_expected": 0.5}

### MEDIUM — signal_integrity
- Message: Critical net SWCLK appears to contain a dangling or stub-like route (28.28 units)
- Recommendation: Remove unused stubs or terminate the route at the intended load to reduce reflection risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=12.0
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 72.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: medium
- Nets: SWCLK
- Metrics: {"trace_length": 28.28, "threshold": 12.0, "connection_count": 1}

### MEDIUM — signal_integrity
- Message: Net UART_TX has a long signal path between U1 and J1 (37.95 units)
- Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=37.95, threshold=25.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce the signal path length from 37.95 to at or below 25.0 by improving placement or rerouting.
- Fix Priority: medium
- Components: U1, J1
- Nets: UART_TX
- Metrics: {"distance": 37.95, "threshold": 25.0}

### MEDIUM — signal_integrity
- Message: Net UART_TX has a long signal path between J1 and R1 (34.18 units)
- Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: distance=34.18, threshold=25.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce the signal path length from 34.18 to at or below 25.0 by improving placement or rerouting.
- Fix Priority: medium
- Components: J1, R1
- Nets: UART_TX
- Metrics: {"distance": 34.18, "threshold": 25.0}

### MEDIUM — stackup_return_path
- Message: Critical net SWCLK is long for a two-layer style stackup
- Recommendation: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=28.0
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 70.0 / 100
- Suggested Fix: Review whether this board class needs a stronger reference-plane strategy or a stackup with better return-path support.
- Fix Priority: medium
- Components: U1
- Nets: SWCLK
- Metrics: {"trace_length": 28.28, "threshold": 28.0, "copper_layers": 1}

### MEDIUM — manufacturing
- Message: Net SWDIO contains a very narrow trace (0.10)
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
- Suggested Fix: Increase the narrow trace width from 0.1 to at least 0.15, subject to board-space and fabrication constraints.
- Fix Priority: medium
- Nets: SWDIO
- Metrics: {"min_trace_width": 0.1, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net SWCLK contains a very narrow trace (0.10)
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
- Suggested Fix: Increase the narrow trace width from 0.1 to at least 0.15, subject to board-space and fabrication constraints.
- Fix Priority: medium
- Nets: SWCLK
- Metrics: {"min_trace_width": 0.1, "threshold": 0.15}

### MEDIUM — manufacturing
- Message: Net UART_TX contains a very narrow trace (0.12)
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
- Nets: UART_TX
- Metrics: {"min_trace_width": 0.12, "threshold": 0.15}

### HIGH — power_integrity
- Message: Physics estimate suggests VCC is running high current density (142.9 A/mm²)
- Recommendation: Increase copper cross-section or redistribute load current so the conductor stays in a safer density band.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=12.0
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: VCC
- Metrics: {"current_density_a_per_mm2": 142.86, "estimated_current_a": 0.8, "cross_section_mm2": 0.0056, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests SWCLK is off target impedance (78.7 ohms vs 50.0 ohms)
- Recommendation: Adjust trace geometry, reference height, or stackup assumptions to bring the line closer to its impedance target.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 9
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 84.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: SWCLK
- Metrics: {"estimated_impedance_ohms": 78.73, "target_impedance_ohms": 50.0, "mismatch_pct": 57.5, "delay_ps": 163.7, "via_inductance_nh": 0.0}

### LOW — system_interaction
- Message: Digital control logic is present without a clearly classified debug or test subsystem.
- Recommendation: Confirm bring-up access through debug headers, test pads, or programming entry points.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.66
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 40 / 100
- Evidence Count: 0
- Engineering Impact: Unknown system impact
- Trust Confidence: 66.0 / 100
- Suggested Fix: Confirm bring-up access through debug headers, test pads, or programming entry points.
- Fix Priority: low
