# SILICORE ENGINEERING REPORT

- File: high_voltage_spacing_board.kicad_pcb
- Score: 5.7 / 100
- Total Risks: 38
- Total Penalty: 304.0

## Executive Summary

**Board needs focused engineering review**

This board shows elevated design risk. The main risk concentration is in safety high voltage. The highest-priority issue is Geometry-derived high-voltage spacing between trace and trace is below creepage target (0.000). The current design snapshot includes 3 components and 4 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: engineering review packet
- Includes: score rationale, finding traceability, recommendations, and saved analysis context
- Best use: design reviews, management updates, supplier communication, and internal signoff

## Top Issues

1. **CRITICAL** — safety_high_voltage — Geometry-derived high-voltage spacing between trace and trace is below creepage target (0.000)
   - Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
2. **CRITICAL** — safety_high_voltage — Geometry-derived high-voltage spacing between trace and trace is below creepage target (1.993)
   - Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
3. **CRITICAL** — safety_high_voltage — Geometry-derived high-voltage spacing between trace and trace is below creepage target (1.800)
   - Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.

## Board Summary

- Component Count: 3
- Net Count: 4
- Risk Count: 38
- Sample Components: J1, U1, U2

## Severity Penalties

- medium: 4.4
- critical: 20.4
- high: 5.4
- low: 0.2

## Category Penalties

- assembly_testability: 1.2
- safety_high_voltage: 20.4
- manufacturing: 1.8
- power_integrity: 4.0
- emi_return_path: 1.0
- reliability: 0.4
- thermal: 0.8
- signal_integrity: 0.6
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
- Message: Critical or debug-oriented net CTRL has no visible test point
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
- Components: U1, U2
- Nets: CTRL
- Metrics: {"has_testpoint": false}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and pad is below creepage target (0.700)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: J1, J1
- Nets: HV+, HV-
- Metrics: {"creepage": 0.7, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.280)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: J1
- Nets: HV+, HV-
- Metrics: {"creepage": 1.28, "threshold": 2.5}

### HIGH — manufacturing
- Message: Geometry-derived copper clearance between pad and trace falls below target (0.000)
- Recommendation: Increase copper-to-copper spacing or reshape the nearby region to restore manufacturable and electrically safe clearance.
- Root Cause: Design rule below fabrication limits
- Impact: Reduced yield or board failure risk
- Confidence: 0.92
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.18
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Reduced yield or board failure risk
- Trust Confidence: 92.0 / 100
- Suggested Fix: Review the board against fabrication limits and increase trace widths or spacing where necessary.
- Fix Priority: high
- Components: J1
- Nets: HV-, HV+
- Metrics: {"clearance": 0.0, "threshold": 0.18}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (0.000)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: J1
- Nets: HV-, HV+
- Metrics: {"creepage": 0.0, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and pad is below creepage target (0.700)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1, U1
- Nets: HV+, HV-
- Metrics: {"creepage": 0.7, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and pad is below creepage target (1.094)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1, U1
- Nets: HV+, CTRL
- Metrics: {"creepage": 1.0938, "threshold": 2.5}

### HIGH — manufacturing
- Message: Geometry-derived copper clearance between pad and trace falls below target (0.000)
- Recommendation: Increase copper-to-copper spacing or reshape the nearby region to restore manufacturable and electrically safe clearance.
- Root Cause: Design rule below fabrication limits
- Impact: Reduced yield or board failure risk
- Confidence: 0.92
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.18
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Reduced yield or board failure risk
- Trust Confidence: 92.0 / 100
- Suggested Fix: Review the board against fabrication limits and increase trace widths or spacing where necessary.
- Fix Priority: high
- Components: U1
- Nets: HV+, HV-
- Metrics: {"clearance": 0.0, "threshold": 0.18}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (0.000)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: HV+, HV-
- Metrics: {"creepage": 0.0, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.564)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: HV+, CTRL
- Metrics: {"creepage": 1.5635, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and pad is below creepage target (1.094)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1, U1
- Nets: HV-, CTRL
- Metrics: {"creepage": 1.0938, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.130)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: HV-, HV+
- Metrics: {"creepage": 1.13, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.370)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: HV-, CTRL
- Metrics: {"creepage": 1.37, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.524)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: CTRL, HV+
- Metrics: {"creepage": 1.5235, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between pad and trace is below creepage target (1.330)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Components: U1
- Nets: CTRL, HV-
- Metrics: {"creepage": 1.33, "threshold": 2.5}

### HIGH — manufacturing
- Message: Geometry-derived copper clearance between trace and trace falls below target (0.000)
- Recommendation: Increase copper-to-copper spacing or reshape the nearby region to restore manufacturable and electrically safe clearance.
- Root Cause: Design rule below fabrication limits
- Impact: Reduced yield or board failure risk
- Confidence: 0.92
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.18
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Reduced yield or board failure risk
- Trust Confidence: 92.0 / 100
- Suggested Fix: Review the board against fabrication limits and increase trace widths or spacing where necessary.
- Fix Priority: high
- Nets: HV+, HV-
- Metrics: {"clearance": 0.0, "threshold": 0.18}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between trace and trace is below creepage target (0.000)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Nets: HV+, HV-
- Metrics: {"creepage": 0.0, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between trace and trace is below creepage target (1.993)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Nets: HV+, CTRL
- Metrics: {"creepage": 1.9933, "threshold": 2.5}

### CRITICAL — safety_high_voltage
- Message: Geometry-derived high-voltage spacing between trace and trace is below creepage target (1.800)
- Recommendation: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 90.0 / 100
- Suggested Fix: Increase the routed spacing, add slots/barriers, or rework the high-voltage region to meet creepage intent.
- Fix Priority: critical
- Nets: HV-, CTRL
- Metrics: {"creepage": 1.8, "threshold": 2.5}

### MEDIUM — power_integrity
- Message: U1 (driver) has no nearby decoupling capacitor
- Recommendation: Place a decoupling capacitor close to the device power pin and on the relevant supply net.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 90.0 / 100
- Suggested Fix: Place a 0.1uF decoupling capacitor close to the IC power pin, ideally within the configured threshold of 4.0.
- Fix Priority: medium
- Components: U1
- Metrics: {"nearest_cap_distance": null, "threshold": 4.0}

### MEDIUM — power_integrity
- Message: U2 (mcu) has no nearby decoupling capacitor
- Recommendation: Place a decoupling capacitor close to the device power pin and on the relevant supply net.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.9
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 90.0 / 100
- Suggested Fix: Place a 0.1uF decoupling capacitor close to the IC power pin, ideally within the configured threshold of 4.0.
- Fix Priority: medium
- Components: U2
- Metrics: {"nearest_cap_distance": null, "threshold": 4.0}

### HIGH — power_integrity
- Message: U1 appears to lack enough local decoupling support
- Recommendation: Add or reposition local bypass capacitors close to the device supply pins with short return paths.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.87
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 10
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 87.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Components: U1
- Nets: HV-, CTRL, HV+
- Metrics: {"local_caps_found": 0, "min_local_caps": 1, "nearest_local_cap_distance": null}

### MEDIUM — power_integrity
- Message: U1 may be missing nearby bulk capacitance support
- Recommendation: Place appropriate bulk capacitance near the converter or regulator input/output path to reduce transients and rail collapse risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Components: U1
- Nets: HV-, CTRL, HV+
- Metrics: {"bulk_caps_found": 0, "bulk_distance_threshold": 12.0}

### HIGH — power_integrity
- Message: U2 appears to lack enough local decoupling support
- Recommendation: Add or reposition local bypass capacitors close to the device supply pins with short return paths.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.87
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 87.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Components: U2
- Nets: GND, CTRL
- Metrics: {"local_caps_found": 0, "min_local_caps": 1, "nearest_local_cap_distance": null}

### MEDIUM — emi_return_path
- Message: U1 is connected to a critical net but no ground reference was identified
- Recommendation: Verify that this component has an appropriate nearby ground reference or return path for the connected critical net.
- Root Cause: Missing or poor return path
- Impact: Increased EMI and unstable signal reference
- Confidence: 0.7
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 6
- Engineering Impact: Increased EMI and unstable signal reference
- Trust Confidence: 70.0 / 100
- Suggested Fix: Ensure the component has a valid ground reference and a clear low-impedance return path to the board ground network.
- Fix Priority: medium
- Components: U1
- Nets: HV+, HV-, CTRL
- Metrics: {"critical_net_keywords": ["CLK", "CS", "CTRL", "MISO", "MOSI", "SCL", "SDA"], "ground_net_keywords": ["GND", "GROUND", "PGND"]}

### HIGH — power_integrity
- Message: J1 is not connected to a valid power rail
- Recommendation: Connect the component to the intended power net and confirm that its pad-to-net assignments are present in the board data.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.
- Fix Priority: high
- Components: J1
- Nets: HV-, HV+
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["HV-", "HV+"], "has_power": false, "has_ground": false}

### HIGH — power_integrity
- Message: U1 is not connected to a valid power rail
- Recommendation: Connect the component to the intended power net and confirm that its pad-to-net assignments are present in the board data.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 66 / 100
- Evidence Count: 9
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Connect the affected component to the intended power rail and verify that the configured power-net definitions match the board design.
- Fix Priority: high
- Components: U1
- Nets: HV-, CTRL, HV+
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["HV-", "CTRL", "HV+"], "has_power": false, "has_ground": false}

### MEDIUM — power_integrity
- Message: U2 has ground but no visible power rail
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
- Components: U2
- Nets: GND, CTRL
- Metrics: {"required_power_nets": ["VIN", "VCC", "VBAT", "5V", "3V3", "VDD"], "required_ground_nets": ["GND", "GROUND", "PGND"], "observed_component_nets": ["GND", "CTRL"], "has_power": false, "has_ground": true}

### MEDIUM — reliability
- Message: Ground net GND has limited visible connectivity (1 connections)
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
- Metrics: {"ground_connections": 1, "threshold": 4}

### HIGH — emi_return_path
- Message: U1 is connected to critical net(s) CTRL but has no direct ground-reference net
- Recommendation: Review this signal path and ensure it has a nearby continuous ground reference and a clean return path.
- Root Cause: Missing or poor return path
- Impact: Increased EMI and unstable signal reference
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 100 / 100
- Evidence Count: 8
- Engineering Impact: Increased EMI and unstable signal reference
- Trust Confidence: 82.0 / 100
- Suggested Fix: Route the signal closer to a continuous ground reference and reduce gaps, layer transitions, or broken return paths.
- Fix Priority: high
- Components: U1
- Nets: CTRL
- Metrics: {"critical_nets": ["CTRL"], "required_ground_nets": ["GND", "GROUND", "PGND"], "ground_present": true}

### CRITICAL — safety_high_voltage
- Message: High-voltage pad on U1:HV+ is close to U1:CTRL
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
- Components: U1, U1
- Nets: HV+, CTRL
- Metrics: {"clearance": 2.19, "min_clearance": 2.5}

### CRITICAL — safety_high_voltage
- Message: High-voltage pad on U1:HV- is close to U1:CTRL
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
- Components: U1, U1
- Nets: HV-, CTRL
- Metrics: {"clearance": 2.19, "min_clearance": 2.5}

### MEDIUM — thermal
- Message: U1 appears to have limited nearby thermal via support (0)
- Recommendation: Add thermal vias or improve heat escape near this power-dissipating component.
- Root Cause: Thermal concentration or poor heat spreading
- Impact: Hotspots, reduced reliability, or thermal stress
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=1
- Traceability: 100 / 100
- Evidence Count: 10
- Engineering Impact: Hotspots, reduced reliability, or thermal stress
- Trust Confidence: 80.0 / 100
- Suggested Fix: Improve thermal distribution with better spacing, copper spreading, or thermal-aware placement.
- Fix Priority: medium
- Components: U1
- Nets: CTRL, HV+, HV-
- Metrics: {"nearby_thermal_vias": 0, "threshold": 1, "radius": 4.0}

### MEDIUM — thermal
- Message: U1 connects to relatively narrow copper for heat spreading (0.24)
- Recommendation: Increase local copper width or area around this component to improve heat spreading.
- Root Cause: Thermal concentration or poor heat spreading
- Impact: Hotspots, reduced reliability, or thermal stress
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=0.5
- Traceability: 100 / 100
- Evidence Count: 9
- Engineering Impact: Hotspots, reduced reliability, or thermal stress
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve thermal distribution with better spacing, copper spreading, or thermal-aware placement.
- Fix Priority: medium
- Components: U1
- Nets: CTRL, HV+, HV-
- Metrics: {"max_connected_width": 0.24, "threshold": 0.5}

### HIGH — signal_integrity
- Message: Physics estimate suggests CTRL is off target impedance (66.2 ohms vs 50.0 ohms)
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
- Nets: CTRL
- Metrics: {"estimated_impedance_ohms": 66.2, "target_impedance_ohms": 50.0, "mismatch_pct": 32.4, "delay_ps": 123.6, "via_inductance_nh": 0.0}

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
