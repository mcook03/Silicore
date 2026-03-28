from engine.kicad_parser import parse_kicad_file


def parse_pcb_file(filepath):
    if filepath.endswith(".kicad_pcb"):
        return parse_kicad_file(filepath)

    raise ValueError(f"Unsupported PCB file format: {filepath}")