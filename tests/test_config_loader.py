import unittest

from engine.config_loader import get_editable_config_view, parse_config_form


class ConfigLoaderTests(unittest.TestCase):
    def test_parse_config_form_supports_extended_engineering_controls(self):
        form = {
            "layout_density_region_size": "40",
            "power_distribution_distance_threshold": "28",
            "power_decoupling_distance_threshold": "3.5",
            "power_max_trace_length": "72",
            "power_min_trace_width": "0.7",
            "power_max_via_count": "6",
            "power_min_connections": "3",
            "signal_max_trace_length": "35",
            "signal_critical_nets": "CLK, USB_D+, USB_D-",
            "signal_min_general_trace_width": "0.18",
            "signal_excluded_net_keywords": "GND, VCC, 5V",
            "thermal_hotspot_distance_threshold": "5.5",
            "emi_require_ground_reference": "false",
            "score_penalty_low": "0.6",
            "score_penalty_medium": "1.2",
            "score_penalty_high": "1.8",
            "score_penalty_critical": "2.6",
        }

        config = parse_config_form(form)
        editable = get_editable_config_view(config)

        self.assertEqual(editable["layout"]["density_region_size"], 40.0)
        self.assertEqual(editable["power"]["min_connections"], 3)
        self.assertEqual(editable["signal"]["min_general_trace_width"], 0.18)
        self.assertEqual(editable["signal"]["excluded_net_keywords"], ["GND", "VCC", "5V"])
        self.assertFalse(editable["emi"]["require_ground_reference"])
        self.assertEqual(editable["score"]["penalty_critical"], 2.6)
        self.assertEqual(config["rules"]["power_rail"]["min_connections"], 3)
        self.assertEqual(config["rules"]["trace_quality"]["min_general_trace_width"], 0.18)
        self.assertEqual(config["rules"]["signal_path"]["excluded_nets"], ["GND", "VCC", "5V"])


if __name__ == "__main__":
    unittest.main()
