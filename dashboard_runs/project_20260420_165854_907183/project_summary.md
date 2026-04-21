# SILICORE PROJECT SUMMARY

- Total Boards: 2
- Average Score: 13.05 / 100
- Best Score: 20.0 / 100
- Worst Score: 6.1 / 100

## Project Insight

**Project comparison complete**

The strongest board is fixtures_thermal_hotspot_board.kicad_pcb at 20.0 / 100, while the weakest board is fixtures_high_speed_pair_bad.kicad_pcb at 6.1 / 100. The current score spread across the project is 13.9 points. The most recurring issue area across the project is power integrity.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Review Readiness

- Output format: project review packet
- Includes: ranked boards, project insight summary, and per-board finding traceability
- Best use: revision meetings, program reviews, and cross-board engineering prioritization

## Ranked Boards

### #1 — fixtures_thermal_hotspot_board.kicad_pcb
- Score: 20.0 / 100
- Total Risks: 18
- Total Penalty: 80.0
- Summary: This board shows high design risk. The main risk concentration is in power integrity. The highest-priority issue is Physics estimate suggests VIN is running high current density (214.3 A/mm²). The current design snapshot includes 3 components and 3 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
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

### #2 — fixtures_high_speed_pair_bad.kicad_pcb
- Score: 6.1 / 100
- Total Risks: 44
- Total Penalty: 224.0
- Summary: This board shows elevated design risk. The main risk concentration is in signal integrity. The highest-priority issue is Geometry-derived high-voltage spacing between pad and pad is below creepage target (0.700). The current design snapshot includes 3 components and 5 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
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
