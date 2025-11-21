"""
Statistical operations for incidents

Handles:
- Computing incident statistics
- Sorting incidents by priority
- User type detection
"""

from typing import Dict, List, Optional


def is_human_user(user: Optional[Dict]) -> bool:
    """Check if a user is a human (not bot or service account)"""
    if not user:
        return False
    name = (user.get("name") or "").strip().lower()
    if not name:
        return False
    if name.startswith("service account"):
        return False
    if "bot" in name:
        return False
    return True


def sort_active(items: List[Dict]) -> List[Dict]:
    """Sort active incidents by priority (SLA, severity, age)"""
    severity_rank = {"Critical": 0, "Major": 1, "Minor": 2, "Pending": 3}

    def key(x: Dict):
        return (
            0 if x["over_sla"] else 1,
            -x["days_over_sla"],
            severity_rank.get(x["severity"], 4),
            -x["age_days"],
        )

    return sorted(items, key=key)


def compute_stats(items: List[Dict]) -> Dict[str, int]:
    """Compute statistics for a list of incidents"""
    return {
        "total": len(items),
        "without_severity": sum(
            1 for x in items if not x.get("severity") or x.get("severity") == "Pending"
        ),
        "without_assignee": sum(1 for x in items if not x.get("has_assignee")),
        "missing_updates": sum(1 for x in items if not x.get("last_update_time")),
        "over_sla": sum(1 for x in items if x.get("over_sla")),
    }
