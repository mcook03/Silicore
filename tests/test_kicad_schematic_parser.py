import os
import tempfile
import unittest

from engine.kicad_schematic_parser import parse_kicad_schematic_file


SCHEMATIC_FIXTURE = """
(kicad_sch (version 20230121) (generator eeschema)
  (lib_symbols
    (symbol "Device:R"
      (property "Reference" "R" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (symbol "R_0_1"
        (pin passive line (at -2.54 0 0) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 2.54 0 180) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Device:C"
      (property "Reference" "C" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "C" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (symbol "C_0_1"
        (pin passive line (at -2.54 0 0) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 2.54 0 180) (length 2.54)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
  )
  (symbol (lib_id "Device:R") (at 10 10 0) (unit 1)
    (property "Reference" "R1" (at 10 12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "10k" (at 10 8 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Resistor_SMD:R_0603" (at 10 10 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid a1))
    (pin "2" (uuid a2))
  )
  (symbol (lib_id "Device:C") (at 20 10 0) (unit 1)
    (property "Reference" "C1" (at 20 12 0) (effects (font (size 1.27 1.27))))
    (property "Value" "1u" (at 20 8 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "Capacitor_SMD:C_0603" (at 20 10 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid b1))
    (pin "2" (uuid b2))
  )
  (wire (pts (xy 5 10) (xy 7.46 10))
    (stroke (width 0) (type default))
    (uuid w1)
  )
  (wire (pts (xy 12.54 10) (xy 17.46 10))
    (stroke (width 0) (type default))
    (uuid w2)
  )
  (wire (pts (xy 22.54 10) (xy 25 10))
    (stroke (width 0) (type default))
    (uuid w3)
  )
  (label "VIN" (at 5 10 0) (effects (font (size 1.27 1.27))))
  (label "MID" (at 15 10 0) (effects (font (size 1.27 1.27))))
  (hierarchical_label "VOUT" (shape output) (at 25 10 0) (effects (font (size 1.27 1.27))))
)
""".strip()


class KiCadSchematicParserTests(unittest.TestCase):
    def test_parser_builds_components_nets_and_schematic_metadata(self):
        fd, path = tempfile.mkstemp(suffix=".kicad_sch")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(SCHEMATIC_FIXTURE)

            pcb = parse_kicad_schematic_file(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

        self.assertEqual(pcb.source_format, "kicad_schematic")
        self.assertEqual(len(pcb.components), 2)
        self.assertEqual(len(pcb.nets), 3)
        self.assertGreaterEqual(len(pcb.traces), 3)
        self.assertEqual(pcb.metadata["schematic"]["component_count"], 2)
        self.assertEqual(pcb.metadata["schematic"]["label_count"], 3)
        self.assertEqual(pcb.metadata["schematic"]["net_count"], 3)

        r1 = pcb.get_component("R1")
        c1 = pcb.get_component("C1")
        self.assertIsNotNone(r1)
        self.assertIsNotNone(c1)
        self.assertEqual(set(r1.get_nets()), {"VIN", "MID"})
        self.assertEqual(set(c1.get_nets()), {"MID", "VOUT"})


if __name__ == "__main__":
    unittest.main()
