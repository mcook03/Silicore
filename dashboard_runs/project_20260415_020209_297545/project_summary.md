# SILICORE PROJECT SUMMARY

- Total Boards: 3
- Average Score: 0.4 / 10
- Best Score: 1.2 / 10
- Worst Score: 0.0 / 10

## Project Insight

**Project comparison complete**

The strongest board is risky_board_fixed_gnd.txt at 1.2 / 10, while the weakest board is sensor_board_v2.txt at 0.0 / 10. The current score spread across the project is 1.2 points. The most recurring issue area across the project is emi return path.

## Parser Capability

- Current production-ready inputs: `.kicad_pcb`, `.txt`
- Planned next-stage inputs: Altium-style board imports, Gerber-derived review flows

## Ranked Boards

### #1 — risky_board_fixed_gnd.txt
- Score: 1.2 / 10
- Total Risks: 20
- Total Penalty: 8.8
- Summary: This board shows high design risk. The main risk concentration is in emi return path. The highest-priority issue is U1 and C1 are too close (1.41 units). The current design snapshot includes 8 components and 4 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Confidence: 81.0 / 100
  - Finding: Critical or debug-oriented net CLK has no visible test point
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Confidence: 72.0 / 100

### #2 — power_board_v2.txt
- Score: 0.0 / 10
- Total Risks: 25
- Total Penalty: 11.0
- Summary: This board shows high design risk. The main risk concentration is in emi return path. The highest-priority issue is J1 and LED1 are too close (1.41 units). The current design snapshot includes 10 components and 4 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Confidence: 81.0 / 100
  - Finding: U1 has no assigned net, so its ground reference cannot be verified
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Confidence: 75.0 / 100

### #3 — sensor_board_v2.txt
- Score: 0.0 / 10
- Total Risks: 26
- Total Penalty: 12.0
- Summary: This board shows high design risk. The main risk concentration is in emi return path. The highest-priority issue is J1 and LED1 are too close (2.83 units). The current design snapshot includes 9 components and 4 nets. The board is likely functional at a prototype level, but the highlighted issues should be addressed before stronger production confidence.
  - Finding: Board has limited visible fiducial strategy for assembly alignment
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=2
    - Confidence: 76.0 / 100
  - Finding: Ground test-point coverage appears limited for bring-up and probing
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: threshold=1
    - Confidence: 81.0 / 100
  - Finding: Critical or debug-oriented net SDA has no visible test point
    - Trigger: A rule-based design condition triggered this finding.
    - Observed: No measured value preserved.
    - Confidence: 72.0 / 100
