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


async def run_deadline_evaluations_and_notify(db_path: Optional[Path] = None) -> Dict[str, int]:
    """
    Scan all date-based entities across properties, evaluate key alert milestones
    (J-30, J-7, J0, Overdue), and dispatch in-app and push notifications.
    Also runs automatic cleanup of expired notifications.
    """
    from app.notifier import dispatch_notification
    from app.database import cleanup_expired_notifications

    conn = get_db_connection(db_path)
    today = datetime.date.today()
    generated = {
        "maintenance": 0,
        "taxes": 0,
        "inventory": 0,
        "renovations": 0,
        "auto_read_cleaned": 0,
    }

    try:
        # 1. Maintenance tasks
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, p.name AS property_name 
            FROM maintenance_tasks t
            JOIN properties p ON t.property_id = p.id
        """)
        tasks = [dict(r) for r in cur.fetchall()]

        for t in tasks:
            due_raw = t.get("next_due_date")
            if not due_raw:
                continue
            try:
                due_date = datetime.date.fromisoformat(due_raw)
            except (ValueError, TypeError):
                continue

            diff = (due_date - today).days
            prop_name = t.get("property_name", "Bien")
            task_title = t.get("title", "Tâche d'entretien")

            milestone = None
            alert_title = None
            alert_msg = None

            if diff < 0:
                milestone = "overdue"
                alert_title = f"⚠️ Tâche en retard : {task_title}"
                alert_msg = f"L'entretien '{task_title}' pour {prop_name} est en retard de {abs(diff)} jour(s) (échéance : {due_raw})."
            elif diff == 0:
                milestone = "j0"
                alert_title = f"🔔 Échéance aujourd'hui : {task_title}"
                alert_msg = f"L'entretien '{task_title}' pour {prop_name} arrive à échéance aujourd'hui."
            elif 1 <= diff <= 7:
                milestone = "j7"
                alert_title = f"⏳ Rappel entretien (dans {diff}j) : {task_title}"
                alert_msg = f"L'entretien '{task_title}' pour {prop_name} est prévu dans {diff} jour(s) ({due_raw})."
            elif 25 <= diff <= 30:
                milestone = "j30"
                alert_title = f"📅 Entretien à venir sous 30 jours : {task_title}"
                alert_msg = f"L'entretien '{task_title}' pour {prop_name} est planifié pour le {due_raw}."

            if milestone:
                event_key = f"maint:{t['id']}:{due_raw}:{milestone}"
                link = f"/maintenance?property_id={t['property_id']}"
                res = await dispatch_notification(
                    title=alert_title,
                    message=alert_msg,
                    category="maintenance",
                    property_id=t["property_id"],
                    link_url=link,
                    event_key=event_key,
                    db_path=db_path,
                )
                if res:
                    generated["maintenance"] += 1

        # 2. Taxes deadlines
        cur.execute("""
            SELECT tx.*, p.name AS property_name
            FROM taxes tx
            JOIN properties p ON tx.property_id = p.id
            WHERE tx.status != 'Payé'
        """)
        taxes_list = [dict(r) for r in cur.fetchall()]

        for tx in taxes_list:
            due_raw = tx.get("due_date")
            if not due_raw:
                continue
            try:
                due_date = datetime.date.fromisoformat(due_raw)
            except (ValueError, TypeError):
                continue

            diff = (due_date - today).days
            prop_name = tx.get("property_name", "Bien")
            tax_type = tx.get("tax_type", "Taxe")
            amount_str = f"{tx.get('amount', 0):.2f} €"

            milestone = None
            if diff < 0:
                milestone = "overdue"
                alert_title = f"🚨 Échéance fiscale dépassée : {tax_type}"
                alert_msg = f"Le paiement de {tax_type} ({amount_str}) pour {prop_name} était dû le {due_raw} et est en retard."
            elif diff == 0:
                milestone = "j0"
                alert_title = f"🏛️ Paiement fiscal dû aujourd'hui : {tax_type}"
                alert_msg = f"La date limite de règlement pour {tax_type} ({amount_str}, {prop_name}) est fixée à aujourd'hui."
            elif 1 <= diff <= 7:
                milestone = "j7"
                alert_title = f"⏳ Rappel fiscal (dans {diff}j) : {tax_type}"
                alert_msg = f"L'échéance de {tax_type} ({amount_str}) pour {prop_name} arrive à terme dans {diff} jour(s) ({due_raw})."
            elif 25 <= diff <= 30:
                milestone = "j30"
                alert_title = f"📅 Échéance fiscale à venir : {tax_type}"
                alert_msg = f"Pensez au règlement de {tax_type} ({amount_str}) pour {prop_name} d'ici le {due_raw}."

            if milestone:
                event_key = f"tax:{tx['id']}:{due_raw}:{milestone}"
                link = f"/taxes?property_id={tx['property_id']}"
                res = await dispatch_notification(
                    title=alert_title,
                    message=alert_msg,
                    category="taxes",
                    property_id=tx["property_id"],
                    link_url=link,
                    event_key=event_key,
                    db_path=db_path,
                )
                if res:
                    generated["taxes"] += 1

        # 3. Equipment Warranties
        cur.execute("""
            SELECT i.*, p.name AS property_name
            FROM inventory i
            JOIN properties p ON i.property_id = p.id
            WHERE i.warranty_expiry_date IS NOT NULL AND i.warranty_expiry_date != ''
        """)
        items = [dict(r) for r in cur.fetchall()]

        for it in items:
            exp_raw = it.get("warranty_expiry_date")
            try:
                exp_date = datetime.date.fromisoformat(exp_raw)
            except (ValueError, TypeError):
                continue

            diff = (exp_date - today).days
            prop_name = it.get("property_name", "Bien")
            item_name = it.get("name", "Équipement")

            milestone = None
            if 1 <= diff <= 30:
                milestone = "expiring_soon"
                alert_title = f"🛡️ Garantie expirant bientôt : {item_name}"
                alert_msg = f"La garantie de l'équipement '{item_name}' ({prop_name}) arrive à expiration le {exp_raw} (dans {diff}j)."

            if milestone:
                event_key = f"warranty:{it['id']}:{exp_raw}:{milestone}"
                link = f"/inventory?property_id={it['property_id']}"
                res = await dispatch_notification(
                    title=alert_title,
                    message=alert_msg,
                    category="documents",
                    property_id=it["property_id"],
                    link_url=link,
                    event_key=event_key,
                    db_path=db_path,
                )
                if res:
                    generated["inventory"] += 1

        # 4. Renovations & Works
        cur.execute("""
            SELECT r.*, p.name AS property_name
            FROM renovations r
            JOIN properties p ON r.property_id = p.id
            WHERE r.status != 'Terminé' AND r.status != 'Annulé'
        """)
        renovations_list = [dict(r) for r in cur.fetchall()]

        for r in renovations_list:
            end_raw = r.get("end_date")
            prop_name = r.get("property_name", "Bien")
            title_r = r.get("title", "Chantier")

            # Budget overflow check
            est = r.get("estimated_budget") or 0.0
            act = r.get("actual_cost") or 0.0
            if est > 0 and act > est:
                diff_cost = act - est
                event_key = f"renov_budget:{r['id']}:{round(act, 2)}"
                res = await dispatch_notification(
                    title=f"⚠️ Dépassement de budget : {title_r}",
                    message=f"Le chantier '{title_r}' ({prop_name}) dépasse le budget prévisionnel de {diff_cost:.2f} € (réel : {act:.2f} €, prévu : {est:.2f} €).",
                    category="renovations",
                    property_id=r["property_id"],
                    link_url=f"/renovations/{r['id']}",
                    event_key=event_key,
                    db_path=db_path,
                )
                if res:
                    generated["renovations"] += 1

            # End date overdue check
            if end_raw:
                try:
                    end_date = datetime.date.fromisoformat(end_raw)
                    diff = (end_date - today).days
                    if diff < 0:
                        event_key = f"renov_end:{r['id']}:{end_raw}:overdue"
                        res = await dispatch_notification(
                            title=f"🔨 Retard de chantier : {title_r}",
                            message=f"La date de fin estimée du chantier '{title_r}' ({prop_name}) était le {end_raw} (dépassée de {abs(diff)} jours).",
                            category="renovations",
                            property_id=r["property_id"],
                            link_url=f"/renovations/{r['id']}",
                            event_key=event_key,
                            db_path=db_path,
                        )
                        if res:
                            generated["renovations"] += 1
                except (ValueError, TypeError):
                    pass

        # 5. Clean up expired notifications
        cleaned = cleanup_expired_notifications(db_path)
        generated["auto_read_cleaned"] = cleaned

        return generated
    finally:
        conn.close()

