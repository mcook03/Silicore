def build_project_summary(boards):
    if not boards:
        return {
            "total_boards": 0,
            "average_score": 0,
            "best_score": 0,
            "worst_score": 0,
            "severity_counts": {},
            "category_counts": {},
        }

    total_score = sum(board.get("score", 0) for board in boards)
    average_score = round(total_score / len(boards), 2)
    best_score = max(board.get("score", 0) for board in boards)
    worst_score = min(board.get("score", 0) for board in boards)

    severity_counts = {}
    category_counts = {}

    for board in boards:
        for risk in board.get("risks", []):
            severity = str(risk.get("severity", "low")).lower()
            category = risk.get("category", "uncategorized")

            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "total_boards": len(boards),
        "average_score": average_score,
        "best_score": best_score,
        "worst_score": worst_score,
        "severity_counts": dict(sorted(severity_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
    }