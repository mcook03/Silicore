# SILICORE PROJECT SUMMARY

- Total Boards: 5
- Average Score: 13.2 / 100
- Best Score: 42.0 / 100
- Worst Score: 0.0 / 100

## Project Insight

**Project comparison complete**

The strongest board is thermal_hotspot_board.kicad_pcb at 42.0 / 100, while the weakest board is high_speed_pair_bad.kicad_pcb at 0.0 / 100. The current score spread across the project is 42.0 points. The most recurring issue area across the project is power integrity.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: project review packet
- Includes: ranked boards, project insight summary, and per-board finding traceability
- Best use: revision meetings, program reviews, and cross-board engineering prioritization

## Ranked Boards

### #1 — thermal_hotspot_board.kicad_pcb
- Score: 42.0 / 100
- Total Risks: 14
- Total Penalty: 58.0
- Summary: This board shows elevated design risk. The main risk concentration is in power integrity. The highest-priority issue is Power net VIN uses a narrow trace width (0.20). The current design snapshot includes 3 components and 3 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Traceability: 86 / 100
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Traceability: 86 / 100
    - Confidence: 81.0 / 100
  - Finding: U1 (linear_reg) has no nearby decoupling capacitor
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=4.0
    - Traceability: 94 / 100
    - Confidence: 90.0 / 100

### #2 — high_voltage_spacing_board.kicad_pcb
- Score: 18.0 / 100
- Total Risks: 15
- Total Penalty: 82.0
- Summary: This board shows high design risk. The main risk concentration is in power integrity. The highest-priority issue is High-voltage pad on U1:HV+ is close to U1:CTRL. The current design snapshot includes 3 components and 4 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Traceability: 86 / 100
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Traceability: 86 / 100
    - Confidence: 81.0 / 100
  - Finding: Critical or debug-oriented net CTRL has no visible test point
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Traceability: 100 / 100
    - Confidence: 72.0 / 100

### #3 — mixed_signal_noise_board.kicad_pcb
- Score: 4.0 / 100
- Total Risks: 22
- Total Penalty: 96.0
- Summary: This board shows elevated design risk. The main risk concentration is in power integrity. The highest-priority issue is U2 may have poor power delivery because nearest regulator U1 is 24.08 units away. The current design snapshot includes 4 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Traceability: 86 / 100
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Traceability: 86 / 100
    - Confidence: 81.0 / 100
  - Finding: Control net SENSOR_OUT has no visible pull resistor component
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Traceability: 100 / 100
    - Confidence: 72.0 / 100

### #4 — assembly_testability_board.kicad_pcb
- Score: 2.0 / 100
- Total Risks: 24
- Total Penalty: 98.0
- Summary: This board shows high design risk. The main risk concentration is in manufacturing. The highest-priority issue is Power net VCC uses a narrow trace width (0.16). The current design snapshot includes 4 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Traceability: 86 / 100
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Traceability: 86 / 100
    - Confidence: 81.0 / 100
  - Finding: Critical or debug-oriented net SWDIO has no visible test point
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Traceability: 100 / 100
    - Confidence: 72.0 / 100

### #5 — high_speed_pair_bad.kicad_pcb
- Score: 0.0 / 100
- Total Risks: 33
- Total Penalty: 152.0
- Summary: This board shows high design risk. The main risk concentration is in signal integrity. The highest-priority issue is High-voltage pad on J1:VBUS is close to J1:USB_DP. The current design snapshot includes 3 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Traceability: 86 / 100
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Traceability: 86 / 100
    - Confidence: 81.0 / 100
  - Finding: Critical or debug-oriented net USB_DP has no visible test point
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Traceability: 100 / 100
    - Confidence: 72.0 / 100
