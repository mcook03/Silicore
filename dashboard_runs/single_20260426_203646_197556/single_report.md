# SILICORE ENGINEERING REPORT

- File: ossc_board.kicad_pcb
- Score: 5.2 / 100
- Total Risks: 189
- Total Penalty: 940.0

## Executive Summary

**Board needs focused engineering review**

This board shows elevated design risk. The main risk concentration is in power integrity. The highest-priority issue is Fast or noisy net /TVP_BOARD1/CLK27 changes layers without nearby return-path stitching support. The current design snapshot includes 0 components and 211 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: engineering review packet
- Includes: score rationale, finding traceability, recommendations, and saved analysis context
- Best use: design reviews, management updates, supplier communication, and internal signoff

## Top Issues

1. **HIGH** — emi_emc — Fast or noisy net /TVP_BOARD1/CLK27 changes layers without nearby return-path stitching support
   - Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
2. **HIGH** — signal_integrity — Physics estimate suggests /FPGA1/HDMITX_PCLK is off target impedance (63.1 ohms vs 50.0 ohms)
   - Recommendation: Adjust trace geometry, reference height, or stackup assumptions to bring the line closer to its impedance target.
3. **HIGH** — signal_integrity — Physics estimate suggests /HDMITX1/TMDS_CLK+ is off target impedance (61.7 ohms vs 50.0 ohms)
   - Recommendation: Adjust trace geometry, reference height, or stackup assumptions to bring the line closer to its impedance target.

## Board Summary

- Component Count: 0
- Net Count: 211
- Risk Count: 189
- Sample Components: 

## Severity Penalties

- medium: 38.8
- high: 55.2

## Category Penalties

- assembly_testability: 7.2
- power_integrity: 59.8
- emi_emc: 4.4
- reliability: 0.4
- signal_integrity: 19.4
- stackup_return_path: 2.4
- system_interaction: 0.4

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
- Message: Critical or debug-oriented net /FPGA1/DCLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/DCLK
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/HDMITX_PCLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/HDMITX_PCLK
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/SCL has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/SCL
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/SDA has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/SDA
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/SD_CLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/SD_CLK
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/NCSO has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/NCSO
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /HDMITX1/DDC_SCL has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /HDMITX1/DDC_SCL
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /HDMITX1/DDC_SDA has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /HDMITX1/DDC_SDA
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /HDMITX1/TMDS_CLK+ has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /HDMITX1/TMDS_CLK+
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /HDMITX1/TMDS_CLK- has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /HDMITX1/TMDS_CLK-
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net NET-(U17A-SCL) has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: NET-(U17A-SCL)
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net NET-(U17A-SDA) has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: NET-(U17A-SDA)
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /TVP_BOARD1/PCLK has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /TVP_BOARD1/PCLK
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /TVP_BOARD1/CLK27 has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /TVP_BOARD1/CLK27
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/LCD_CS_N has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/LCD_CS_N
- Metrics: {"has_testpoint": false}

### MEDIUM — assembly_testability
- Message: Critical or debug-oriented net /FPGA1/RESET_N has no visible test point
- Recommendation: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 5
- Engineering Impact: Unknown system impact
- Trust Confidence: 72.0 / 100
- Suggested Fix: Expose this net through a test point, header, or accessible debug pad to improve bring-up and manufacturing test coverage.
- Fix Priority: medium
- Nets: /FPGA1/RESET_N
- Metrics: {"has_testpoint": false}

### HIGH — power_integrity
- Message: High-current net /FPGA1/VCCA bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCA
- Metrics: {"min_width": 0.2, "recommended_width": 0.7, "trace_length": 105.27}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCA shows a strong width neck-down that may concentrate current density
- Recommendation: Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"width_ratio": 2.5, "min_width": 0.2, "max_width": 0.5}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCA relies on many transitions through a narrow path
- Recommendation: Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 74.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"via_count": 8, "max_bottleneck_vias": 3, "min_width": 0.2}

### HIGH — power_integrity
- Message: High-current net /FPGA1/VCCD_PLL bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"min_width": 0.22, "recommended_width": 0.7, "trace_length": 93.09}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCD_PLL relies on many transitions through a narrow path
- Recommendation: Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 74.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"via_count": 5, "max_bottleneck_vias": 3, "min_width": 0.22}

### HIGH — power_integrity
- Message: High-current net /FPGA1/VCCINT bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCINT
- Metrics: {"min_width": 0.2, "recommended_width": 0.7, "trace_length": 129.45}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCINT shows a strong width neck-down that may concentrate current density
- Recommendation: Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"width_ratio": 2.5, "min_width": 0.2, "max_width": 0.5}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCINT relies on many transitions through a narrow path
- Recommendation: Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 74.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"via_count": 12, "max_bottleneck_vias": 3, "min_width": 0.2}

### HIGH — power_integrity
- Message: High-current net /HDMITX1/AVCC3V3 bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"min_width": 0.2, "recommended_width": 0.7, "trace_length": 146.67}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/AVCC3V3 shows a strong width neck-down that may concentrate current density
- Recommendation: Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"width_ratio": 2.5, "min_width": 0.2, "max_width": 0.5}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/AVCC3V3 relies on many transitions through a narrow path
- Recommendation: Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 74.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"via_count": 10, "max_bottleneck_vias": 3, "min_width": 0.2}

### HIGH — power_integrity
- Message: High-current net /FPGA1/VCCIO bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCIO
- Metrics: {"min_width": 0.2, "recommended_width": 0.7, "trace_length": 580.75}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCIO shows a strong width neck-down that may concentrate current density
- Recommendation: Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"width_ratio": 5.0, "min_width": 0.2, "max_width": 1.0}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCIO relies on many transitions through a narrow path
- Recommendation: Reduce unnecessary layer changes in the high-current route or add stronger parallel current-return support across the transitions.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 74.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"via_count": 32, "max_bottleneck_vias": 3, "min_width": 0.2}

### HIGH — power_integrity
- Message: High-current net /HDMITX1/5V bottlenecks through a narrow copper section
- Recommendation: Widen the narrow neck-down, shorten the high-current route, or add parallel copper/plane support to reduce current-density and voltage-drop pressure.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /HDMITX1/5V
- Metrics: {"min_width": 0.25, "recommended_width": 0.7, "trace_length": 249.45}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/5V shows a strong width neck-down that may concentrate current density
- Recommendation: Keep high-current copper width more consistent through the load path and avoid abrupt neck-down transitions near sources, loads, or connectors.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.79
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 79.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/5V
- Metrics: {"width_ratio": 4.0, "min_width": 0.25, "max_width": 1.0}

### HIGH — emi_emc
- Message: Fast or noisy net /FPGA1/SCL changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Nets: /FPGA1/SCL
- Metrics: {"unsupported_vias": 1, "return_via_radius": 3.0, "trace_length": 227.07}

### HIGH — emi_emc
- Message: Fast or noisy net /FPGA1/SDA changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Nets: /FPGA1/SDA
- Metrics: {"unsupported_vias": 2, "return_via_radius": 3.0, "trace_length": 214.48}

### MEDIUM — emi_emc
- Message: Switching or power net /FPGA1/VCCA forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"trace_length": 105.27, "max_loop_length": 45.0, "via_count": 8}

### MEDIUM — emi_emc
- Message: Switching or power net /FPGA1/VCCD_PLL forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"trace_length": 93.09, "max_loop_length": 45.0, "via_count": 5}

### MEDIUM — emi_emc
- Message: Switching or power net /FPGA1/VCCINT forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"trace_length": 129.45, "max_loop_length": 45.0, "via_count": 12}

### HIGH — emi_emc
- Message: Fast or noisy net /FPGA1/NCSO changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Nets: /FPGA1/NCSO
- Metrics: {"unsupported_vias": 1, "return_via_radius": 3.0, "trace_length": 18.1}

### MEDIUM — emi_emc
- Message: Switching or power net /HDMITX1/AVCC3V3 forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"trace_length": 146.67, "max_loop_length": 45.0, "via_count": 10}

### MEDIUM — emi_emc
- Message: Switching or power net /FPGA1/VCCIO forms a long exposed loop path
- Recommendation: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Tighten the converter current loop, shorten the route, and keep the return path adjacent to reduce loop area and EMI.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"trace_length": 580.75, "max_loop_length": 45.0, "via_count": 32}

### HIGH — emi_emc
- Message: Fast or noisy net /TVP_BOARD1/CLK27 changes layers without nearby return-path stitching support
- Recommendation: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 7
- Engineering Impact: Unknown system impact
- Trust Confidence: 82.0 / 100
- Suggested Fix: Add nearby ground stitching vias or keep the route on a better contained reference path to reduce return-current disruption.
- Fix Priority: high
- Nets: /TVP_BOARD1/CLK27
- Metrics: {"unsupported_vias": 1, "return_via_radius": 3.0, "trace_length": 56.32}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCA uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"trace_length": 105.27, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCA uses many vias (8)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"via_count": 8, "threshold": 4}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCD_PLL uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"trace_length": 93.09, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCD_PLL uses many vias (5)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"via_count": 5, "threshold": 4}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCINT uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"trace_length": 129.45, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCINT uses many vias (12)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"via_count": 12, "threshold": 4}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/AVCC3V3 uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"trace_length": 146.67, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/AVCC3V3 uses many vias (10)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"via_count": 10, "threshold": 4}

### HIGH — power_integrity
- Message: High-current net /FPGA1/VCCIO contains a strong width bottleneck (0.20 to 1.00)
- Recommendation: Widen the narrow neck-down, shorten the constricted region, or rework the path to reduce resistive and thermal stress.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 83.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCIO
- Metrics: {"min_width": 0.2, "max_width": 1.0, "ratio": 5.0, "threshold": 2.5}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCIO uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"trace_length": 580.75, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /FPGA1/VCCIO uses many vias (32)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"via_count": 32, "threshold": 4}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/DVDD1V8 uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"trace_length": 65.93, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/DVDD1V8 uses many vias (6)
- Recommendation: Reduce via count or use stronger parallel current return paths on this power route.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.72
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=4
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 72.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"via_count": 6, "threshold": 4}

### HIGH — power_integrity
- Message: High-current net /TVP_BOARD1/DVDD contains a strong width bottleneck (0.25 to 0.70)
- Recommendation: Widen the narrow neck-down, shorten the constricted region, or rework the path to reduce resistive and thermal stress.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 83.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /TVP_BOARD1/DVDD
- Metrics: {"min_width": 0.25, "max_width": 0.7, "ratio": 2.8, "threshold": 2.5}

### HIGH — power_integrity
- Message: High-current net /HDMITX1/5V contains a strong width bottleneck (0.25 to 1.00)
- Recommendation: Widen the narrow neck-down, shorten the constricted region, or rework the path to reduce resistive and thermal stress.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 83.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /HDMITX1/5V
- Metrics: {"min_width": 0.25, "max_width": 1.0, "ratio": 4.0, "threshold": 2.5}

### MEDIUM — power_integrity
- Message: High-current net /HDMITX1/5V uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /HDMITX1/5V
- Metrics: {"trace_length": 249.45, "threshold": 40.0}

### HIGH — power_integrity
- Message: High-current net /TVP_BOARD1/DVDD2V5 contains a strong width bottleneck (0.22 to 0.70)
- Recommendation: Widen the narrow neck-down, shorten the constricted region, or rework the path to reduce resistive and thermal stress.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.83
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2.5
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 83.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /TVP_BOARD1/DVDD2V5
- Metrics: {"min_width": 0.22, "max_width": 0.7, "ratio": 3.18, "threshold": 2.5}

### MEDIUM — power_integrity
- Message: High-current net /TVP_BOARD1/DVDD2V5 uses a long routed path
- Recommendation: Shorten the power path and tighten the source-to-load loop to reduce parasitic resistance and inductance.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.76
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=40.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 76.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /TVP_BOARD1/DVDD2V5
- Metrics: {"trace_length": 44.31, "threshold": 40.0}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCA has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCA has excessive routed length (105.27 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 105.27.
- Fix Priority: high
- Nets: /FPGA1/VCCA
- Metrics: {"trace_length": 105.27, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCA uses a narrow trace width (0.20)
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
- Suggested Fix: Increase the power trace width from 0.2 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /FPGA1/VCCA
- Metrics: {"trace_width": 0.2, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCA uses many vias (8) which may increase impedance
- Recommendation: Reduce unnecessary via transitions on critical power nets where possible.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce via transitions on this power net. It currently uses 8 vias versus a threshold of 5.
- Fix Priority: medium
- Nets: /FPGA1/VCCA
- Metrics: {"via_count": 8, "threshold": 5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCD_PLL has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCD_PLL has excessive routed length (93.09 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 93.09.
- Fix Priority: high
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"trace_length": 93.09, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCD_PLL uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCINT has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCINT has excessive routed length (129.45 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 129.45.
- Fix Priority: high
- Nets: /FPGA1/VCCINT
- Metrics: {"trace_length": 129.45, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCINT uses a narrow trace width (0.20)
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
- Suggested Fix: Increase the power trace width from 0.2 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /FPGA1/VCCINT
- Metrics: {"trace_width": 0.2, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCINT uses many vias (12) which may increase impedance
- Recommendation: Reduce unnecessary via transitions on critical power nets where possible.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce via transitions on this power net. It currently uses 12 vias versus a threshold of 5.
- Fix Priority: medium
- Nets: /FPGA1/VCCINT
- Metrics: {"via_count": 12, "threshold": 5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/AVCC1V8 has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC1V8
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /HDMITX1/AVCC1V8 uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /HDMITX1/AVCC1V8
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/AVCC3V3 has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /HDMITX1/AVCC3V3 has excessive routed length (146.67 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 146.67.
- Fix Priority: high
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"trace_length": 146.67, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /HDMITX1/AVCC3V3 uses a narrow trace width (0.20)
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
- Suggested Fix: Increase the power trace width from 0.2 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"trace_width": 0.2, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/AVCC3V3 uses many vias (10) which may increase impedance
- Recommendation: Reduce unnecessary via transitions on critical power nets where possible.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce via transitions on this power net. It currently uses 10 vias versus a threshold of 5.
- Fix Priority: medium
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"via_count": 10, "threshold": 5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCIO has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCIO has excessive routed length (580.75 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 580.75.
- Fix Priority: high
- Nets: /FPGA1/VCCIO
- Metrics: {"trace_length": 580.75, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /FPGA1/VCCIO uses a narrow trace width (0.20)
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
- Suggested Fix: Increase the power trace width from 0.2 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /FPGA1/VCCIO
- Metrics: {"trace_width": 0.2, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /FPGA1/VCCIO uses many vias (32) which may increase impedance
- Recommendation: Reduce unnecessary via transitions on critical power nets where possible.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce via transitions on this power net. It currently uses 32 vias versus a threshold of 5.
- Fix Priority: medium
- Nets: /FPGA1/VCCIO
- Metrics: {"via_count": 32, "threshold": 5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/DVDD1V8 has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /HDMITX1/DVDD1V8 has excessive routed length (65.93 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 65.93.
- Fix Priority: high
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"trace_length": 65.93, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /HDMITX1/DVDD1V8 uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/DVDD1V8 uses many vias (6) which may increase impedance
- Recommendation: Reduce unnecessary via transitions on critical power nets where possible.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.78
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=5
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 78.0 / 100
- Suggested Fix: Reduce via transitions on this power net. It currently uses 6 vias versus a threshold of 5.
- Fix Priority: medium
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"via_count": 6, "threshold": 5}

### MEDIUM — power_integrity
- Message: Power net /TVP_BOARD1/AVDD has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /TVP_BOARD1/AVDD
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /TVP_BOARD1/AVDD uses a narrow trace width (0.40)
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
- Suggested Fix: Increase the power trace width from 0.4 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /TVP_BOARD1/AVDD
- Metrics: {"trace_width": 0.4, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(Y1-VDD) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(Y1-VDD)
- Metrics: {"connections": 0, "minimum_expected": 2}

### MEDIUM — power_integrity
- Message: Power net NET-(U3-PVCC1) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U3-PVCC1)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U3-PVCC1) uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U3-PVCC1)
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /TVP_BOARD1/DVDD has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /TVP_BOARD1/DVDD
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /TVP_BOARD1/DVDD uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /TVP_BOARD1/DVDD
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U3-PVCC2) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U3-PVCC2)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U3-PVCC2) uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U3-PVCC2)
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINL2) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINL2)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINL2) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINL2)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINR2) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINR2)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINR2) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINR2)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINR3) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINR3)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINR3) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINR3)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINL4) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINL4)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINL4) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINL4)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINL3) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINL3)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINL3) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINL3)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net NET-(U8-VINR4) has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: NET-(U8-VINR4)
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net NET-(U8-VINR4) uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: NET-(U8-VINR4)
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /TVP_BOARD1/AVDD_F has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /TVP_BOARD1/AVDD_F
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /TVP_BOARD1/AVDD_F uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /TVP_BOARD1/AVDD_F
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/5V has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /HDMITX1/5V
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /HDMITX1/5V has excessive routed length (249.45 units)
- Recommendation: Reduce power path length or improve distribution topology to lower impedance and voltage drop risk.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.86
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=50.0
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 86.0 / 100
- Suggested Fix: Shorten the power route and improve placement to reduce the current routed length of 249.45.
- Fix Priority: high
- Nets: /HDMITX1/5V
- Metrics: {"trace_length": 249.45, "threshold": 50.0}

### HIGH — power_integrity
- Message: Power net /HDMITX1/5V uses a narrow trace width (0.25)
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
- Suggested Fix: Increase the power trace width from 0.25 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /HDMITX1/5V
- Metrics: {"trace_width": 0.25, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /HDMITX1/5V_FUSED has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /HDMITX1/5V_FUSED
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /HDMITX1/5V_FUSED uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /HDMITX1/5V_FUSED
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — power_integrity
- Message: Power net /TVP_BOARD1/DVDD2V5 has too few connections (0)
- Recommendation: Check whether the power net is properly distributed to all intended loads.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.8
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 80.0 / 100
- Suggested Fix: Verify that all intended loads are actually connected to this power net and confirm the rail is distributed across the required pins and devices.
- Fix Priority: medium
- Nets: /TVP_BOARD1/DVDD2V5
- Metrics: {"connections": 0, "minimum_expected": 2}

### HIGH — power_integrity
- Message: Power net /TVP_BOARD1/DVDD2V5 uses a narrow trace width (0.22)
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
- Suggested Fix: Increase the power trace width from 0.22 to at least 0.5 or more, depending on current demand.
- Fix Priority: high
- Nets: /TVP_BOARD1/DVDD2V5
- Metrics: {"trace_width": 0.22, "minimum_expected": 0.5}

### MEDIUM — reliability
- Message: Ground net GND has limited visible connectivity (0 connections)
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
- Metrics: {"ground_connections": 0, "threshold": 4}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/HDMITX_PCLK appears to contain a dangling or stub-like route (12.74 units)
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
- Nets: /FPGA1/HDMITX_PCLK
- Metrics: {"trace_length": 12.74, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/SCL uses many via transitions (5)
- Recommendation: Reduce layer transitions on sensitive nets where possible to improve continuity and reduce impedance discontinuities.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 84.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: medium
- Nets: /FPGA1/SCL
- Metrics: {"via_count": 5, "threshold": 2}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/SCL appears to contain a dangling or stub-like route (227.07 units)
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
- Nets: /FPGA1/SCL
- Metrics: {"trace_length": 227.07, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/SDA uses many via transitions (5)
- Recommendation: Reduce layer transitions on sensitive nets where possible to improve continuity and reduce impedance discontinuities.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: threshold=2
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 84.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: medium
- Nets: /FPGA1/SDA
- Metrics: {"via_count": 5, "threshold": 2}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/SDA appears to contain a dangling or stub-like route (214.48 units)
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
- Nets: /FPGA1/SDA
- Metrics: {"trace_length": 214.48, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/SD_CLK appears to contain a dangling or stub-like route (17.31 units)
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
- Nets: /FPGA1/SD_CLK
- Metrics: {"trace_length": 17.31, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/NCSO appears to contain a dangling or stub-like route (18.10 units)
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
- Nets: /FPGA1/NCSO
- Metrics: {"trace_length": 18.1, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /HDMITX1/DDC_SCL appears to contain a dangling or stub-like route (30.54 units)
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
- Nets: /HDMITX1/DDC_SCL
- Metrics: {"trace_length": 30.54, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /HDMITX1/DDC_SDA appears to contain a dangling or stub-like route (31.95 units)
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
- Nets: /HDMITX1/DDC_SDA
- Metrics: {"trace_length": 31.95, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /TVP_BOARD1/PCLK appears to contain a dangling or stub-like route (29.05 units)
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
- Nets: /TVP_BOARD1/PCLK
- Metrics: {"trace_length": 29.05, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /TVP_BOARD1/CLK27 appears to contain a dangling or stub-like route (56.32 units)
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
- Nets: /TVP_BOARD1/CLK27
- Metrics: {"trace_length": 56.32, "threshold": 12.0, "connection_count": 0}

### MEDIUM — signal_integrity
- Message: Critical net /FPGA1/LCD_CS_N appears to contain a dangling or stub-like route (38.60 units)
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
- Nets: /FPGA1/LCD_CS_N
- Metrics: {"trace_length": 38.6, "threshold": 12.0, "connection_count": 0}

### HIGH — signal_integrity
- Message: Critical nets /FPGA1/SCL and /FPGA1/SDA run closely in parallel on B.Cu
- Recommendation: Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: /FPGA1/SCL, /FPGA1/SDA
- Metrics: {"parallel_similarity": 1.0, "spacing": 1.07, "spacing_threshold": 2.5}

### HIGH — signal_integrity
- Message: Critical nets /FPGA1/SCL and /TVP_BOARD1/CLK27 run closely in parallel on B.Cu
- Recommendation: Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: /FPGA1/SCL, /TVP_BOARD1/CLK27
- Metrics: {"parallel_similarity": 1.0, "spacing": 2.1, "spacing_threshold": 2.5}

### HIGH — signal_integrity
- Message: Critical nets /FPGA1/SDA and /TVP_BOARD1/CLK27 run closely in parallel on B.Cu
- Recommendation: Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: /FPGA1/SDA, /TVP_BOARD1/CLK27
- Metrics: {"parallel_similarity": 1.0, "spacing": 1.1, "spacing_threshold": 2.5}

### HIGH — signal_integrity
- Message: Critical nets /HDMITX1/DDC_SCL and /HDMITX1/DDC_SDA run closely in parallel on F.Cu
- Recommendation: Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: /HDMITX1/DDC_SCL, /HDMITX1/DDC_SDA
- Metrics: {"parallel_similarity": 1.0, "spacing": 0.8, "spacing_threshold": 2.5}

### HIGH — signal_integrity
- Message: Critical nets /TVP_BOARD1/CLK27 and /FPGA1/LCD_CS_N run closely in parallel on F.Cu
- Recommendation: Increase spacing, shorten parallel run length, or adjust layer strategy to reduce crosstalk risk.
- Root Cause: Signal path geometry or routing issue
- Impact: Timing errors or signal degradation
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Timing errors or signal degradation
- Trust Confidence: 82.0 / 100
- Suggested Fix: Reduce path length, simplify routing, and keep critical signals on cleaner and more direct routes.
- Fix Priority: high
- Nets: /TVP_BOARD1/CLK27, /FPGA1/LCD_CS_N
- Metrics: {"parallel_similarity": 1.0, "spacing": 1.08, "spacing_threshold": 2.5}

### HIGH — stackup_return_path
- Message: Critical net /FPGA1/SCL changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Nets: /FPGA1/SCL
- Metrics: {"unsupported_vias": 1, "signal_via_ground_radius": 3.5}

### HIGH — stackup_return_path
- Message: Critical net /FPGA1/SDA changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Nets: /FPGA1/SDA
- Metrics: {"unsupported_vias": 2, "signal_via_ground_radius": 3.5}

### HIGH — stackup_return_path
- Message: Critical net /FPGA1/SD_CLK changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Nets: /FPGA1/SD_CLK
- Metrics: {"unsupported_vias": 1, "signal_via_ground_radius": 3.5}

### HIGH — stackup_return_path
- Message: Critical net /TVP_BOARD1/CLK27 changes layers without nearby ground-return stitching
- Recommendation: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.84
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 6
- Engineering Impact: Unknown system impact
- Trust Confidence: 84.0 / 100
- Suggested Fix: Place ground stitching vias near sensitive transitions so return current does not need to detour around the layer change.
- Fix Priority: high
- Nets: /TVP_BOARD1/CLK27
- Metrics: {"unsupported_vias": 1, "signal_via_ground_radius": 3.5}

### MEDIUM — signal_integrity
- Message: Net /FPGA1/SCL has a long total routed trace length (227.07 units)
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
- Suggested Fix: Reduce total routed trace length from 227.06713019622825 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /FPGA1/SCL
- Metrics: {"trace_length": 227.06713019622825, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net /FPGA1/SDA has a long total routed trace length (214.48 units)
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
- Suggested Fix: Reduce total routed trace length from 214.48181627386109 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /FPGA1/SDA
- Metrics: {"trace_length": 214.48181627386109, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net /TVP_BOARD1/RGB1_B has a long total routed trace length (61.21 units)
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
- Suggested Fix: Reduce total routed trace length from 61.206955558648296 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /TVP_BOARD1/RGB1_B
- Metrics: {"trace_length": 61.206955558648296, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net /TVP_BOARD1/RGB1_S has a long total routed trace length (105.11 units)
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
- Suggested Fix: Reduce total routed trace length from 105.10726687326984 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /TVP_BOARD1/RGB1_S
- Metrics: {"trace_length": 105.10726687326984, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net /FPGA1/BTN0 has a long total routed trace length (61.44 units)
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
- Suggested Fix: Reduce total routed trace length from 61.43571464446867 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /FPGA1/BTN0
- Metrics: {"trace_length": 61.43571464446867, "threshold": 60.0}

### MEDIUM — signal_integrity
- Message: Net /FPGA1/RESET_N has a long total routed trace length (133.71 units)
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
- Suggested Fix: Reduce total routed trace length from 133.7123645985902 toward or below 60.0 by tightening placement and simplifying the route.
- Fix Priority: medium
- Nets: /FPGA1/RESET_N
- Metrics: {"trace_length": 133.7123645985902, "threshold": 60.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/DCLK is off target impedance (61.7 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/DCLK
- Metrics: {"estimated_impedance_ohms": 61.68, "target_impedance_ohms": 50.0, "mismatch_pct": 23.4, "delay_ps": 69.8, "via_inductance_nh": 34.48}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/HDMITX_PCLK is off target impedance (63.1 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/HDMITX_PCLK
- Metrics: {"estimated_impedance_ohms": 63.11, "target_impedance_ohms": 50.0, "mismatch_pct": 26.2, "delay_ps": 74.8, "via_inductance_nh": 0.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/SCL is off target impedance (61.7 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/SCL
- Metrics: {"estimated_impedance_ohms": 61.68, "target_impedance_ohms": 50.0, "mismatch_pct": 23.4, "delay_ps": 1336.6, "via_inductance_nh": 172.42}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/SDA is off target impedance (61.7 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/SDA
- Metrics: {"estimated_impedance_ohms": 61.68, "target_impedance_ohms": 50.0, "mismatch_pct": 23.4, "delay_ps": 1262.5, "via_inductance_nh": 172.42}

### MEDIUM — signal_integrity
- Message: Physics estimate suggests /FPGA1/SD_CLK is off target impedance (57.8 ohms vs 50.0 ohms)
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
- Fix Priority: medium
- Nets: /FPGA1/SD_CLK
- Metrics: {"estimated_impedance_ohms": 57.79, "target_impedance_ohms": 50.0, "mismatch_pct": 15.6, "delay_ps": 102.4, "via_inductance_nh": 34.48}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCA may incur high IR drop (118.5 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCA
- Metrics: {"voltage_drop_mv": 118.52, "estimated_current_a": 0.8, "resistance_ohms": 0.1482, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCA is running high current density (65.3 A/mm²)
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
- Nets: /FPGA1/VCCA
- Metrics: {"current_density_a_per_mm2": 65.31, "estimated_current_a": 0.8, "cross_section_mm2": 0.01225, "threshold": 12.0}

### MEDIUM — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCD_PLL may incur high IR drop (101.9 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: medium
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"voltage_drop_mv": 101.9, "estimated_current_a": 0.8, "resistance_ohms": 0.1274, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCD_PLL is running high current density (63.5 A/mm²)
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
- Nets: /FPGA1/VCCD_PLL
- Metrics: {"current_density_a_per_mm2": 63.49, "estimated_current_a": 0.8, "cross_section_mm2": 0.0126, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCINT may incur high IR drop (145.8 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCINT
- Metrics: {"voltage_drop_mv": 145.75, "estimated_current_a": 0.8, "resistance_ohms": 0.1822, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCINT is running high current density (65.3 A/mm²)
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
- Nets: /FPGA1/VCCINT
- Metrics: {"current_density_a_per_mm2": 65.31, "estimated_current_a": 0.8, "cross_section_mm2": 0.01225, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/NCSO is off target impedance (63.1 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/NCSO
- Metrics: {"estimated_impedance_ohms": 63.11, "target_impedance_ohms": 50.0, "mismatch_pct": 26.2, "delay_ps": 106.4, "via_inductance_nh": 34.48}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/AVCC1V8 is running high current density (61.0 A/mm²)
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
- Nets: /HDMITX1/AVCC1V8
- Metrics: {"current_density_a_per_mm2": 60.95, "estimated_current_a": 0.8, "cross_section_mm2": 0.01313, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/AVCC3V3 may incur high IR drop (165.1 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"voltage_drop_mv": 165.13, "estimated_current_a": 0.8, "resistance_ohms": 0.2064, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/AVCC3V3 is running high current density (65.3 A/mm²)
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
- Nets: /HDMITX1/AVCC3V3
- Metrics: {"current_density_a_per_mm2": 65.31, "estimated_current_a": 0.8, "cross_section_mm2": 0.01225, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCIO may incur high IR drop (381.4 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /FPGA1/VCCIO
- Metrics: {"voltage_drop_mv": 381.41, "estimated_current_a": 0.8, "resistance_ohms": 0.4768, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /FPGA1/VCCIO is running high current density (38.1 A/mm²)
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
- Nets: /FPGA1/VCCIO
- Metrics: {"current_density_a_per_mm2": 38.1, "estimated_current_a": 0.8, "cross_section_mm2": 0.021, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /HDMITX1/DDC_SCL is off target impedance (59.0 ohms vs 50.0 ohms)
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
- Nets: /HDMITX1/DDC_SCL
- Metrics: {"estimated_impedance_ohms": 59.03, "target_impedance_ohms": 50.0, "mismatch_pct": 18.1, "delay_ps": 180.3, "via_inductance_nh": 34.48}

### HIGH — signal_integrity
- Message: Physics estimate suggests /HDMITX1/DDC_SDA is off target impedance (59.0 ohms vs 50.0 ohms)
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
- Nets: /HDMITX1/DDC_SDA
- Metrics: {"estimated_impedance_ohms": 59.03, "target_impedance_ohms": 50.0, "mismatch_pct": 18.1, "delay_ps": 188.6, "via_inductance_nh": 34.48}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/DVDD1V8 is running high current density (61.0 A/mm²)
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
- Nets: /HDMITX1/DVDD1V8
- Metrics: {"current_density_a_per_mm2": 60.95, "estimated_current_a": 0.8, "cross_section_mm2": 0.01313, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /HDMITX1/TMDS_CLK+ is off target impedance (61.7 ohms vs 50.0 ohms)
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
- Nets: /HDMITX1/TMDS_CLK+
- Metrics: {"estimated_impedance_ohms": 61.68, "target_impedance_ohms": 50.0, "mismatch_pct": 23.4, "delay_ps": 63.9, "via_inductance_nh": 0.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /HDMITX1/TMDS_CLK- is off target impedance (61.7 ohms vs 50.0 ohms)
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
- Nets: /HDMITX1/TMDS_CLK-
- Metrics: {"estimated_impedance_ohms": 61.68, "target_impedance_ohms": 50.0, "mismatch_pct": 23.4, "delay_ps": 64.1, "via_inductance_nh": 0.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /TVP_BOARD1/AVDD is running high current density (50.8 A/mm²)
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
- Nets: /TVP_BOARD1/AVDD
- Metrics: {"current_density_a_per_mm2": 50.79, "estimated_current_a": 0.8, "cross_section_mm2": 0.01575, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(Y1-VDD) is running high current density (45.7 A/mm²)
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
- Nets: NET-(Y1-VDD)
- Metrics: {"current_density_a_per_mm2": 45.71, "estimated_current_a": 0.8, "cross_section_mm2": 0.0175, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests NET-(U17A-SCL) is off target impedance (60.3 ohms vs 50.0 ohms)
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
- Nets: NET-(U17A-SCL)
- Metrics: {"estimated_impedance_ohms": 60.32, "target_impedance_ohms": 50.0, "mismatch_pct": 20.6, "delay_ps": 55.6, "via_inductance_nh": 34.48}

### HIGH — signal_integrity
- Message: Physics estimate suggests NET-(U17A-SDA) is off target impedance (60.3 ohms vs 50.0 ohms)
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
- Nets: NET-(U17A-SDA)
- Metrics: {"estimated_impedance_ohms": 60.32, "target_impedance_ohms": 50.0, "mismatch_pct": 20.6, "delay_ps": 41.6, "via_inductance_nh": 34.48}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U3-PVCC1) is running high current density (91.4 A/mm²)
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
- Nets: NET-(U3-PVCC1)
- Metrics: {"current_density_a_per_mm2": 91.43, "estimated_current_a": 0.8, "cross_section_mm2": 0.00875, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /TVP_BOARD1/DVDD is running high current density (48.1 A/mm²)
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
- Nets: /TVP_BOARD1/DVDD
- Metrics: {"current_density_a_per_mm2": 48.12, "estimated_current_a": 0.8, "cross_section_mm2": 0.01663, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U3-PVCC2) is running high current density (91.4 A/mm²)
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
- Nets: NET-(U3-PVCC2)
- Metrics: {"current_density_a_per_mm2": 91.43, "estimated_current_a": 0.8, "cross_section_mm2": 0.00875, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests /TVP_BOARD1/PCLK is off target impedance (63.1 ohms vs 50.0 ohms)
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
- Nets: /TVP_BOARD1/PCLK
- Metrics: {"estimated_impedance_ohms": 63.11, "target_impedance_ohms": 50.0, "mismatch_pct": 26.2, "delay_ps": 170.7, "via_inductance_nh": 0.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINL2) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINL2)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINR2) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINR2)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINR3) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINR3)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINL4) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINL4)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINL3) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINL3)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests NET-(U8-VINR4) is running high current density (194.8 A/mm²)
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
- Nets: NET-(U8-VINR4)
- Metrics: {"current_density_a_per_mm2": 194.81, "estimated_current_a": 1.5, "cross_section_mm2": 0.0077, "threshold": 12.0}

### MEDIUM — signal_integrity
- Message: Physics estimate suggests /TVP_BOARD1/CLK27 is off target impedance (57.8 ohms vs 50.0 ohms)
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
- Fix Priority: medium
- Nets: /TVP_BOARD1/CLK27
- Metrics: {"estimated_impedance_ohms": 57.79, "target_impedance_ohms": 50.0, "mismatch_pct": 15.6, "delay_ps": 333.0, "via_inductance_nh": 68.97}

### HIGH — signal_integrity
- Message: Physics estimate suggests /FPGA1/LCD_CS_N is off target impedance (60.3 ohms vs 50.0 ohms)
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
- Nets: /FPGA1/LCD_CS_N
- Metrics: {"estimated_impedance_ohms": 60.32, "target_impedance_ohms": 50.0, "mismatch_pct": 20.6, "delay_ps": 227.5, "via_inductance_nh": 34.48}

### HIGH — power_integrity
- Message: Physics estimate suggests /TVP_BOARD1/AVDD_F is running high current density (63.5 A/mm²)
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
- Nets: /TVP_BOARD1/AVDD_F
- Metrics: {"current_density_a_per_mm2": 63.49, "estimated_current_a": 0.8, "cross_section_mm2": 0.0126, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/5V may incur high IR drop (196.6 mV)
- Recommendation: Reduce path length, widen copper, or split the load path so voltage drop and transient impedance come down.
- Root Cause: Power delivery path impedance or placement issue
- Impact: Voltage drop, instability, or noise
- Confidence: 0.82
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 94 / 100
- Evidence Count: 8
- Engineering Impact: Voltage drop, instability, or noise
- Trust Confidence: 82.0 / 100
- Suggested Fix: Improve regulator-to-load placement, shorten power paths, widen traces, and reduce unnecessary vias.
- Fix Priority: high
- Nets: /HDMITX1/5V
- Metrics: {"voltage_drop_mv": 196.6, "estimated_current_a": 1.0, "resistance_ohms": 0.1966, "threshold_mv": 75.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/5V is running high current density (45.7 A/mm²)
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
- Nets: /HDMITX1/5V
- Metrics: {"current_density_a_per_mm2": 45.71, "estimated_current_a": 1.0, "cross_section_mm2": 0.02188, "threshold": 12.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /HDMITX1/5V_FUSED is running high current density (109.9 A/mm²)
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
- Nets: /HDMITX1/5V_FUSED
- Metrics: {"current_density_a_per_mm2": 109.89, "estimated_current_a": 1.0, "cross_section_mm2": 0.0091, "threshold": 12.0}

### HIGH — signal_integrity
- Message: Physics estimate suggests NET-(U10-HOLDN) is off target impedance (49.6 ohms vs 90.0 ohms)
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
- Nets: NET-(U10-HOLDN)
- Metrics: {"estimated_impedance_ohms": 49.65, "target_impedance_ohms": 90.0, "mismatch_pct": 44.8, "delay_ps": 14.0, "via_inductance_nh": 0.0}

### HIGH — power_integrity
- Message: Physics estimate suggests /TVP_BOARD1/DVDD2V5 is running high current density (49.7 A/mm²)
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
- Nets: /TVP_BOARD1/DVDD2V5
- Metrics: {"current_density_a_per_mm2": 49.69, "estimated_current_a": 0.8, "cross_section_mm2": 0.0161, "threshold": 12.0}

### MEDIUM — system_interaction
- Message: Power and analog subsystems coexist and may need tighter isolation review.
- Recommendation: Inspect regulator, switching, and analog-reference placement to verify noise containment.
- Root Cause: General design issue
- Impact: Unknown system impact
- Confidence: 0.74
- Trigger Condition: A rule-based design condition triggered this finding.
- Observed vs Threshold: No measured value preserved.
- Traceability: 40 / 100
- Evidence Count: 0
- Engineering Impact: Unknown system impact
- Trust Confidence: 74.0 / 100
- Suggested Fix: Inspect regulator, switching, and analog-reference placement to verify noise containment.
- Fix Priority: medium
