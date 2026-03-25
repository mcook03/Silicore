# Silicore Report

## Generated Output

```
SILICORE ENGINEERING REPORT
========================================

EXECUTIVE SUMMARY
----------------------------------------
Overall Risk Score: 4.4 / 10
Total Risks: 3
Critical/High Risks: 2
Most Affected Categories: power_integrity (3)
Top Priority Fixes:
- Narrow power trace
- Weak power distribution path
- Missing nearby decoupling

BOARD OVERVIEW
----------------------------------------
Source Format: kicad_pcb
Total Components: 2
Total Nets: 2
Total Traces: 2
Total Vias: 0
Board Size Estimate: 70.0 x 2.0
Layers: F.Cu

RISK SUMMARY
----------------------------------------
Critical: 0
High: 2
Medium: 1
Low: 0

RISKS BY CATEGORY
----------------------------------------
power_integrity: 3

TOP PRIORITY ISSUES
----------------------------------------
- [HIGH] Power net VIN uses a narrow trace width (0.15)
  Why It Matters: Narrow power traces can overheat and create avoidable IR drop under load.
  Recommendation: Increase power trace width to reduce resistance, heating, and voltage drop.
- [HIGH] U2 may have poor power delivery because nearest regulator U1 is 70.00 units away
  Recommendation: Move the regulator closer to the load or improve the power delivery path with lower-impedance routing.
- [MEDIUM] U2 (mcu) has no nearby decoupling capacitor
  Recommendation: Place a decoupling capacitor close to the device power pin and on the relevant supply net.

DETAILED FINDINGS
----------------------------------------

[POWER_INTEGRITY]
- (HIGH) Power net VIN uses a narrow trace width (0.15)
  Title: Narrow power trace
  Nets: VIN
  Confidence: 0.9
  Fix Priority: high
  Estimated Impact: high
  Design Domain: power
  Why It Matters: Narrow power traces can overheat and create avoidable IR drop under load.
  Recommendation: Increase power trace width to reduce resistance, heating, and voltage drop.
  Suggested Actions:
    - Increase trace width on the critical power segment.
    - Check expected current draw for this rail.
    - Consider copper pours for heavier current paths.
  Metrics: {'min_trace_width': 0.15, 'required_min_trace_width': 0.25}
- (HIGH) U2 may have poor power delivery because nearest regulator U1 is 70.00 units away
  Title: Weak power distribution path
  Components: U2, U1
  Confidence: 0.88
  Fix Priority: high
  Estimated Impact: high
  Design Domain: power
  Recommendation: Move the regulator closer to the load or improve the power delivery path with lower-impedance routing.
  Metrics: {'distance': 70.0, 'threshold': 15.0}
- (MEDIUM) U2 (mcu) has no nearby decoupling capacitor
  Title: Missing nearby decoupling
  Components: U2
  Confidence: 0.9
  Fix Priority: high
  Estimated Impact: high
  Design Domain: power
  Recommendation: Place a decoupling capacitor close to the device power pin and on the relevant supply net.
  Metrics: {'nearest_cap_distance': None, 'threshold': 6.0}

END OF REPORT
```