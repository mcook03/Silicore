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
        _add_component(pcb, "U3", "ADC_REF", 9, 3, "ic", ["ADC_IN", "AGND"])
        _add_component(pcb, "J2", "DEBUG_HEADER", 3, 6, "connector", ["SWDIO", "SWCLK", "GND"])
        _add_component(pcb, "H1", "HV_CONN", 42, 2, "connector", ["HV_BUS"])
        _add_component(pcb, "R1", "sense_res", 48, 2.2, "resistor", ["HV_BUS", "GND"])
        _add_component(pcb, "Y1", "XTAL_25M", 15, 10, "oscillator", ["XTAL_IN", "XTAL_OUT"])
        _add_component(pcb, "U4", "STM32_MCU", 2, 10, "mcu", ["XTAL_IN", "XTAL_OUT", "USB_DP", "USB_DN", "GND"])
        _add_component(pcb, "U5", "ADC_FRONTEND", 34, 11, "adc", ["ADC_IN", "AGND"])

        pcb.add_trace_segment("USB_DP", TraceSegment("USB_DP", 0, 0, 10, 0, 0.30, "F.Cu"))
        pcb.add_trace_segment("USB_DP", TraceSegment("USB_DP", 10, 0, 20, 0, 0.10, "F.Cu"))
        pcb.add_trace_segment("USB_DN", TraceSegment("USB_DN", 0, 1.2, 8, 1.2, 0.15, "F.Cu"))
        pcb.add_trace_segment("USB_DN", TraceSegment("USB_DN", 8, 1.2, 14, 1.2, 0.15, "F.Cu"))
        pcb.add_trace_segment("RESET", TraceSegment("RESET", 0, 2.4, 20, 2.4, 0.12, "F.Cu"))
        pcb.add_trace_segment("VCC", TraceSegment("VCC", 30, 10, 36, 10, 0.35, "F.Cu"))
        pcb.add_trace_segment("SW_NODE", TraceSegment("SW_NODE", 30, 10, 42, 10, 1.20, "F.Cu"))
        pcb.add_trace_segment("SW_NODE", TraceSegment("SW_NODE", 42, 10, 56, 10, 0.25, "B.Cu"))
        pcb.add_trace_segment("SWDIO", TraceSegment("SWDIO", 3, 6, 15, 6, 0.18, "F.Cu"))
        pcb.add_trace_segment("HV_BUS", TraceSegment("HV_BUS", 42, 2, 48, 2.2, 0.40, "F.Cu"))

        pcb.add_via("USB_DP", Via("USB_DP", 5, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DP", Via("USB_DP", 12, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DP", Via("USB_DP", 18, 0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("USB_DN", Via("USB_DN", 8, 1.2, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("VCC", Via("VCC", 30.2, 10.0, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("SW_NODE", Via("SW_NODE", 42, 10, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("SW_NODE", Via("SW_NODE", 48, 10, 0.18, 0.30, ["F.Cu", "B.Cu"]))
        pcb.add_via("SW_NODE", Via("SW_NODE", 52, 10, 0.18, 0.30, ["F.Cu", "B.Cu"]))

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
        self.assertIn("emi_emc", rule_ids)
        self.assertIn("stackup_return_path", rule_ids)
        self.assertIn("assembly_testability", rule_ids)
        self.assertIn("safety_high_voltage", rule_ids)
        self.assertIn("power_path_realism", rule_ids)
        self.assertIn("clock_sensitive_placement", rule_ids)


if __name__ == "__main__":
    unittest.main()
