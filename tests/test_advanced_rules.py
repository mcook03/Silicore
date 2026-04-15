import unittest

from engine.config_loader import load_config
from engine.pcb_model import PCB, Component, Pad, TraceSegment, Via
from engine.rule_runner import run_analysis


def _add_component(pcb, ref, value, x, y, comp_type, pad_nets):
    component = Component(ref=ref, value=value, x=x, y=y, comp_type=comp_type)
    for index, net_name in enumerate(pad_nets, start=1):
        pad = Pad(
            component_ref=ref,
            pad_name=str(index),
            net_name=net_name,
            x=x + (index * 0.2),
            y=y,
            layer="F.Cu",
        )
        component.add_pad(pad)
        pcb.add_net_connection(net_name, ref, str(index))
    pcb.add_component(component)
    return component


class AdvancedRuleCoverageTests(unittest.TestCase):
    def test_advanced_rules_add_signal_thermal_mfg_and_component_depth(self):
        pcb = PCB(filename="advanced_test")
        pcb.add_layer("F.Cu")
        pcb.add_layer("B.Cu")

        _add_component(pcb, "U1", "USB_PHY", 0, 0, "ic", ["USB_DP", "USB_DN", "RESET", "GND"])
        _add_component(pcb, "J1", "CONN", 20, 0, "connector", ["USB_DP", "USB_DN", "RESET"])
        _add_component(pcb, "U2", "buck_reg", 30, 10, "regulator", ["VCC", "GND"])
        _add_component(pcb, "L1", "inductor", 36, 10, "inductor", ["SW_NODE", "VCC"])

        pcb.add_trace_segment("USB_DP", TraceSegment("USB_DP", 0, 0, 10, 0, 0.30, "F.Cu"))
        pcb.add_trace_segment("USB_DP", TraceSegment("USB_DP", 10, 0, 20, 0, 0.10, "F.Cu"))
        pcb.add_trace_segment("USB_DN", TraceSegment("USB_DN", 0, 1.2, 8, 1.2, 0.15, "F.Cu"))
        pcb.add_trace_segment("USB_DN", TraceSegment("USB_DN", 8, 1.2, 14, 1.2, 0.15, "F.Cu"))
        pcb.add_trace_segment("RESET", TraceSegment("RESET", 0, 2.4, 20, 2.4, 0.12, "F.Cu"))
        pcb.add_trace_segment("VCC", TraceSegment("VCC", 30, 10, 36, 10, 0.35, "F.Cu"))

        pcb.add_via("USB_DP", Via("USB_DP", 5, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DP", Via("USB_DP", 12, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DP", Via("USB_DP", 18, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DN", Via("USB_DN", 8, 1.2, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("VCC", Via("VCC", 30.2, 10.0, 0.18, 0.30, ["F.Cu", "B.Cu"]))

        pcb.estimate_board_bounds()

        config = load_config("custom_config.json")
        result = run_analysis(pcb, config)
        rule_ids = {risk["rule_id"] for risk in result["risks"]}

        self.assertIn("signal_integrity_advanced", rule_ids)
        self.assertIn("differential_pair", rule_ids)
        self.assertIn("manufacturability", rule_ids)
        self.assertIn("thermal_management", rule_ids)
        self.assertIn("component_analysis", rule_ids)
        self.assertIn("reliability", rule_ids)


if __name__ == "__main__":
    unittest.main()
