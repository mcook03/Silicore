# Silicore Report

## Generated Output

```
SILICORE ENGINEERING REPORT
========================================

EXECUTIVE SUMMARY
----------------------------------------
Overall Risk Score: 8.5 / 10
Total Risks: 1
Critical/High Risks: 1
Most Affected Categories: layout (1)
Top Priority Fixes:
- Insufficient component spacing

BOARD OVERVIEW
----------------------------------------
Source Format: kicad_pcb
Total Components: 3
Total Nets: 2
Total Traces: 2
Total Vias: 0
Board Size Estimate: 15.0 x 4.0
Layers: F.Cu

RISK SUMMARY
----------------------------------------
Critical: 0
High: 1
Medium: 0
Low: 0

RISKS BY CATEGORY
----------------------------------------
layout: 1

TOP PRIORITY ISSUES
----------------------------------------
- [HIGH] U2 and C1 are too close (2.83 units)
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.

DETAILED FINDINGS
----------------------------------------

[LAYOUT]
- (HIGH) U2 and C1 are too close (2.83 units)
  Title: Insufficient component spacing
  Components: U2, C1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.83, 'threshold': 5.0}

END OF REPORT

REVISION COMPARISON
========================================

SUMMARY
----------------------------------------
Old Score: 4.4
New Score: 8.5
Score Change: +4.10
Resolved Risks: 3
New Risks: 1
Improved Persisting Risks: 0
Worsened Persisting Risks: 0
Unchanged Persisting Risks: 0

RESOLVED RISKS
----------------------------------------
- Power net VIN uses a narrow trace width (0.15)
- U2 (mcu) has no nearby decoupling capacitor
- U2 may have poor power delivery because nearest regulator U1 is 70.00 units away

NEW RISKS
----------------------------------------
- U2 and C1 are too close (2.83 units)

IMPROVED PERSISTING RISKS
----------------------------------------
None

WORSENED PERSISTING RISKS
----------------------------------------
None

UNCHANGED PERSISTING RISKS
----------------------------------------
None

END REVISION COMPARISON
```