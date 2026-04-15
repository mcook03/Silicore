import os
import tempfile
import unittest

from engine.kicad_parser import parse_kicad_file


class KiCadParserFidelityTests(unittest.TestCase):
    def test_parser_captures_outline_zone_rotation_pad_size_and_optional_via_layers(self):
        content = """
(kicad_pcb
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (44 "Edge.Cuts" user)
  )
  (net 0 "")
  (net 1 "GND")
  (net 2 "SIG")
  (gr_line (start 0 0) (end 40 0) (layer "Edge.Cuts"))
  (gr_line (start 40 0) (end 40 20) (layer "Edge.Cuts"))
  (gr_line (start 40 20) (end 0 20) (layer "Edge.Cuts"))
  (gr_line (start 0 20) (end 0 0) (layer "Edge.Cuts"))
  (zone (net 1) (layer "F.Cu")
    (polygon
      (pts
        (xy 2 2)
        (xy 38 2)
        (xy 38 18)
        (xy 2 18)
      )
    )
  )
  (footprint "Resistor_SMD:R_0603_1608Metric"
    (layer "F.Cu")
    (at 10 10 90)
    (property "Reference" "R1")
    (property "Value" "10k")
    (pad 1 smd rect (at 0 0) (size 1.2 0.8) (layers "F.Cu") (net 1 "GND"))
    (pad 2 smd rect (at 2 0) (size 1.2 0.8) (layers "F.Cu") (net 2 "SIG"))
  )
  (segment (start 12 10) (end 30 10) (width 0.2) (layer "F.Cu") (net 2))
  (via (at 30 10) (size 0.8) (drill 0.4) (net 2))
)
""".strip()

        fd, path = tempfile.mkstemp(suffix=".kicad_pcb")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(content)

            pcb = parse_kicad_file(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

        self.assertEqual(pcb.source_format, "kicad_pcb")
        self.assertIn("F.Cu", pcb.layers)
        self.assertIn("Edge.Cuts", pcb.layers)
        self.assertEqual(len(pcb.outline_segments), 4)
        self.assertEqual(len(pcb.zones), 1)
        self.assertGreater(pcb.zones[0].area_estimate, 0)
        self.assertEqual(len(pcb.vias), 1)
        self.assertEqual(pcb.vias[0].layers, ["F.Cu", "B.Cu"])
        self.assertIsNotNone(pcb.board_bounds)
        self.assertGreater(pcb.board_bounds["width"], 0)

        component = pcb.get_component("R1")
        self.assertIsNotNone(component)
        self.assertEqual(component.rotation, 90.0)
        self.assertEqual(component.footprint, "Resistor_SMD:R_0603_1608Metric")
        self.assertEqual(len(component.pads), 2)
        self.assertEqual(component.pads[0].size_x, 1.2)
        self.assertEqual(component.pads[0].size_y, 0.8)


if __name__ == "__main__":
    unittest.main()
