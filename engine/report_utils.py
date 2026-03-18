def severity_rank(severity):
    order = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return order.get(severity, 0)


def fix_priority_rank(priority):
    order = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    return order.get(priority, 0)


def impact_rank(impact):
    order = {
        "high": 3,
        "moderate": 2,
        "low": 1,
    }
    return order.get(impact, 0)


def sort_risks_for_reporting(risks):
    return sorted(
        risks,
        key=lambda r: (
            severity_rank(r.get("severity", "low")),
            fix_priority_rank(r.get("fix_priority", "low")),
            impact_rank(r.get("estimated_impact", "low")),
            r.get("confidence", 0.0),
        ),
        reverse=True,
    )


def summarize_top_categories(category_counter, limit=3):
    items = sorted(category_counter.items(), key=lambda x: x[1], reverse=True)
    return items[:limit]