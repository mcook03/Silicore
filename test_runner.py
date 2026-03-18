from engine.kicad_parser import parse_kicad_file
from engine.normalizer import normalize_pcb
from engine.rule_runner import run_analysis
from engine.report_generator import generate_report
from engine.revision_comparator import compare_revisions
from engine.config_loader import load_config


def load_board(path, config):
    pcb = parse_kicad_file(path)
    pcb = normalize_pcb(pcb)
    risks, score = run_analysis(pcb, config=config)
    return pcb, risks, score


def main():
    config = load_config()

    print("\n=== GOOD POWER BOARD ===")
    good_pcb, good_risks, good_score = load_board("fixtures/power_board_good.kicad_pcb", config)
    print(generate_report(good_pcb, good_risks, good_score))

    print("\n=== BAD POWER BOARD ===")
    bad_pcb, bad_risks, bad_score = load_board("fixtures/power_board_bad.kicad_pcb", config)
    print(generate_report(bad_pcb, bad_risks, bad_score))

    print("\n=== REVISION TEST ===")
    old_pcb, old_risks, old_score = load_board("fixtures/revision_old.kicad_pcb", config)
    new_pcb, new_risks, new_score = load_board("fixtures/revision_new.kicad_pcb", config)
    print(compare_revisions(old_risks, new_risks, old_score, new_score))


if __name__ == "__main__":
    main()