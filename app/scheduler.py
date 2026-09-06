"""Background evaluation of maintenance deadlines and warranty expirations."""

import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.database import get_db_connection


def evaluate_task_status(due_date_str: str) -> Dict[str, Any]:
    """Calculate the status and days remaining for a given due date."""
    try:
        due_date = datetime.date.fromisoformat(due_date_str)
    except (ValueError, TypeError):
        return {"status": "unknown", "days_remaining": 0, "badge": "secondary"}

    today = datetime.date.today()
    diff_days = (due_date - today).days

    if diff_days < 0:
        return {
            "status": "overdue",
            "days_remaining": diff_days,
            "badge": "danger",
            "label_fr": f"En retard ({abs(diff_days)}j)",
            "label_en": f"Overdue ({abs(diff_days)}d)",
        }
    elif diff_days <= 30:
        return {
            "status": "due_soon",
            "days_remaining": diff_days,
            "badge": "warning",
            "label_fr": f"À faire sous {diff_days}j",
            "label_en": f"Due in {diff_days}d",
        }
    else:
        return {
            "status": "ok",
            "days_remaining": diff_days,
            "badge": "success",
            "label_fr": f"À jour (dans {diff_days}j)",
            "label_en": f"Up to date (in {diff_days}d)",
        }


def get_dashboard_summary(property_id: Optional[int] = None, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Compute aggregate KPI metrics for dashboard display."""
    conn = get_db_connection(db_path)
    today = datetime.date.today().isoformat()
    soon_threshold = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    warranty_threshold = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()

    try:
        cur = conn.cursor()

        # Properties count
        cur.execute("SELECT COUNT(*) FROM properties")
        total_properties = cur.fetchone()[0]

        # Filter scope
        prop_filter = "WHERE property_id = ?" if property_id else ""
        params = [property_id] if property_id else []

        # Maintenance tasks counts
        cur.execute(f"SELECT * FROM maintenance_tasks {prop_filter} ORDER BY next_due_date ASC", params)
        all_tasks = [dict(r) for r in cur.fetchall()]

        overdue_tasks = []
        due_soon_tasks = []
        ok_tasks = []

        for t in all_tasks:
            eval_res = evaluate_task_status(t["next_due_date"])
            t["status_info"] = eval_res
            if eval_res["status"] == "overdue":
                overdue_tasks.append(t)
            elif eval_res["status"] == "due_soon":
                due_soon_tasks.append(t)
            else:
                ok_tasks.append(t)

        # Renovations metrics
        cur.execute(f"SELECT COUNT(*), COALESCE(SUM(estimated_budget), 0), COALESCE(SUM(actual_cost), 0) FROM renovations {prop_filter}", params)
        renov_row = cur.fetchone()
        renovations_count = renov_row[0]
        total_budget = renov_row[1]
        total_actual_cost = renov_row[2]

        # Equipment & warranties
        cur.execute(f"SELECT * FROM inventory {prop_filter} ORDER BY warranty_expiry_date ASC", params)
        inventory_items = [dict(r) for r in cur.fetchall()]
        expiring_warranties = []
        for item in inventory_items:
            exp = item.get("warranty_expiry_date")
            if exp:
                st = evaluate_task_status(exp)
                if st["status"] in ("overdue", "due_soon"):
                    item["warranty_status"] = st
                    expiring_warranties.append(item)

        # Recent activities (logs)
        cur.execute(f"""
            SELECT l.*, t.title as task_title 
            FROM maintenance_logs l
            JOIN maintenance_tasks t ON l.task_id = t.id
            {prop_filter.replace('property_id', 'l.property_id')}
            ORDER BY l.performed_date DESC LIMIT 5
        """, params)
        recent_logs = [dict(r) for r in cur.fetchall()]

        return {
            "total_properties": total_properties,
            "all_tasks": all_tasks,
            "overdue_tasks": overdue_tasks,
            "due_soon_tasks": due_soon_tasks,
            "ok_tasks": ok_tasks,
            "renovations_count": renovations_count,
            "total_budget": total_budget,
            "total_actual_cost": total_actual_cost,
            "expiring_warranties": expiring_warranties,
            "recent_logs": recent_logs,
        }
    finally:
        conn.close()
