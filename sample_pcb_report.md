# Silicore Report

## Generated Output

```
SILICORE ENGINEERING REPORT
========================================

EXECUTIVE SUMMARY
----------------------------------------
Overall Risk Score: 0.0 / 10
Total Risks: 20
Critical/High Risks: 15
Most Affected Categories: layout (14), signal_integrity (4), thermal (1)
Top Priority Fixes:
- Potential thermal hotspot
- Weak power distribution path
- Insufficient component spacing
- Insufficient component spacing
- Insufficient component spacing

BOARD OVERVIEW
----------------------------------------
Source Format: simple_text
Total Components: 11
Total Nets: 4
Total Traces: 0
Total Vias: 0
Board Size Estimate: 62.0 x 72.0
Layers: Top

RISK SUMMARY
----------------------------------------
Critical: 0
High: 15
Medium: 5
Low: 0

RISKS BY CATEGORY
----------------------------------------
layout: 14
power_integrity: 1
signal_integrity: 4
thermal: 1

TOP PRIORITY ISSUES
----------------------------------------
- [HIGH] U2 and Q1 may create a thermal hotspot (2.83 units)
  Recommendation: Increase spacing, improve copper area, or add thermal relief to reduce localized heating.
- [HIGH] U1 may have poor power delivery because nearest regulator U2 is 70.71 units away
  Recommendation: Move the regulator closer to the load or improve the power delivery path with lower-impedance routing.
- [HIGH] U1 and C1 are too close (1.00 units)
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
- [HIGH] U1 and D1 are too close (1.00 units)
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
- [HIGH] U1 and L1 are too close (2.24 units)
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.

DETAILED FINDINGS
----------------------------------------

[LAYOUT]
- (HIGH) U1 and C1 are too close (1.00 units)
  Title: Insufficient component spacing
  Components: U1, C1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 1.0, 'threshold': 5.0}
- (HIGH) U1 and D1 are too close (1.00 units)
  Title: Insufficient component spacing
  Components: U1, D1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 1.0, 'threshold': 5.0}
- (HIGH) U1 and L1 are too close (2.24 units)
  Title: Insufficient component spacing
  Components: U1, L1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.24, 'threshold': 5.0}
- (HIGH) U1 and LED1 are too close (3.61 units)
  Title: Insufficient component spacing
  Components: U1, LED1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 3.61, 'threshold': 5.0}
- (HIGH) U2 and Q1 are too close (2.83 units)
  Title: Insufficient component spacing
  Components: U2, Q1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.83, 'threshold': 5.0}
- (HIGH) C1 and D1 are too close (1.41 units)
  Title: Insufficient component spacing
  Components: C1, D1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 1.41, 'threshold': 5.0}
- (HIGH) C1 and L1 are too close (2.00 units)
  Title: Insufficient component spacing
  Components: C1, L1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.0, 'threshold': 5.0}
- (HIGH) C1 and LED1 are too close (3.16 units)
  Title: Insufficient component spacing
  Components: C1, LED1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 3.16, 'threshold': 5.0}
- (HIGH) D1 and L1 are too close (1.41 units)
  Title: Insufficient component spacing
  Components: D1, L1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 1.41, 'threshold': 5.0}
- (HIGH) D1 and LED1 are too close (2.83 units)
  Title: Insufficient component spacing
  Components: D1, LED1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.83, 'threshold': 5.0}
- (HIGH) L1 and LED1 are too close (1.41 units)
  Title: Insufficient component spacing
  Components: L1, LED1
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 1.41, 'threshold': 5.0}
- (HIGH) L1 and C2 are too close (4.24 units)
  Title: Insufficient component spacing
  Components: L1, C2
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 4.24, 'threshold': 5.0}
- (HIGH) LED1 and C2 are too close (2.83 units)
  Title: Insufficient component spacing
  Components: LED1, C2
  Confidence: 0.95
  Fix Priority: high
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Increase spacing between these components to improve manufacturability and routing clearance.
  Metrics: {'distance': 2.83, 'threshold': 5.0}
- (MEDIUM) High component density in region (20, 30) with 6 components [U1, C1, D1, L1, LED1, C2]
  Title: High component density
  Components: U1, C1, D1, L1, LED1, C2
  Region: (20, 30)
  Confidence: 0.9
  Fix Priority: medium
  Estimated Impact: moderate
  Design Domain: layout
  Recommendation: Spread components more evenly to reduce routing congestion and assembly difficulty.
  Metrics: {'component_count': 6, 'threshold': 4, 'region_size': 10.0}

[POWER_INTEGRITY]
- (HIGH) U1 may have poor power delivery because nearest regulator U2 is 70.71 units away
  Title: Weak power distribution path
  Components: U1, U2
  Confidence: 0.76
  Fix Priority: high
  Estimated Impact: high
  Design Domain: power
  Recommendation: Move the regulator closer to the load or improve the power delivery path with lower-impedance routing.
  Metrics: {'distance': 70.71, 'threshold': 15.0}

[SIGNAL_INTEGRITY]
- (MEDIUM) Critical net CTRL has a long signal path between U1 and Q1 (73.54 units)
  Title: Long critical signal path
  Components: U1, Q1
  Nets: CTRL
  Confidence: 0.86
  Fix Priority: medium
  Estimated Impact: moderate
  Design Domain: signal
  Recommendation: Reduce path length or improve routing on this critical signal to lower timing and noise risks.
  Metrics: {'distance': 73.54, 'threshold': 40.0}
- (MEDIUM) Net VOUT has a long signal path between U2 and U1 (70.71 units)
  Title: Long signal path
  Components: U2, U1
  Nets: VOUT
  Confidence: 0.82
  Fix Priority: medium
  Estimated Impact: moderate
  Design Domain: signal
  Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
  Metrics: {'distance': 70.71, 'threshold': 40.0}
- (MEDIUM) Net VOUT has a long signal path between U2 and C1 (70.01 units)
  Title: Long signal path
  Components: U2, C1
  Nets: VOUT
  Confidence: 0.82
  Fix Priority: medium
  Estimated Impact: moderate
  Design Domain: signal
  Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
  Metrics: {'distance': 70.01, 'threshold': 40.0}
- (MEDIUM) Net CTRL has a long signal path between U1 and Q1 (73.54 units)
  Title: Long signal path
  Components: U1, Q1
  Nets: CTRL
  Confidence: 0.82
  Fix Priority: medium
  Estimated Impact: moderate
  Design Domain: signal
  Recommendation: Reduce path length or improve routing to lower noise and signal quality risks.
  Metrics: {'distance': 73.54, 'threshold': 40.0}

[THERMAL]
- (HIGH) U2 and Q1 may create a thermal hotspot (2.83 units)
  Title: Potential thermal hotspot
  Components: U2, Q1
  Confidence: 0.85
  Fix Priority: high
  Estimated Impact: high
  Design Domain: thermal
  Recommendation: Increase spacing, improve copper area, or add thermal relief to reduce localized heating.
  Metrics: {'distance': 2.83, 'threshold': 8.0, 'same_layer': True}

END OF REPORT
```