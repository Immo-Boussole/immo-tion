"""Property timeline aggregator and temporal compression engine."""

import datetime
from typing import Any, Dict, List, Optional
from app.database import get_db_connection

# French month names for clean display
FRENCH_MONTHS = [
    "", "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc."
]

FRENCH_FULL_MONTHS = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]


def parse_date(date_val: Any) -> Optional[datetime.date]:
    """Parse various date formats (YYYY-MM-DD or ISO timestamp) into a date object."""
    if not date_val:
        return None
    if isinstance(date_val, datetime.date):
        return date_val
    if isinstance(date_val, datetime.datetime):
        return date_val.date()
    val_str = str(date_val).strip()
    if len(val_str) >= 10:
        try:
            return datetime.date.fromisoformat(val_str[:10])
        except (ValueError, TypeError):
            pass
    return None


def format_french_date(d: datetime.date, short: bool = False) -> str:
    """Format a date into French (e.g. '15 juin 2025' or '15 juin')."""
    m = FRENCH_MONTHS[d.month] if short else FRENCH_FULL_MONTHS[d.month]
    return f"{d.day} {m} {d.year}"


def get_relative_time_label(d: datetime.date, today: datetime.date) -> str:
    """Return a relative human-readable label in French."""
    delta = (d - today).days
    if delta == 0:
        return "Aujourd'hui"
    if delta == 1:
        return "Demain"
    if delta == -1:
        return "Hier"

    is_future = delta > 0
    days = abs(delta)

    if days < 30:
        return f"Dans {days} jours" if is_future else f"Il y a {days} jours"

    months = round(days / 30.4375)
    if months < 12:
        return f"Dans {months} mois" if is_future else f"Il y a {months} mois"

    years = round(days / 365.25, 1)
    if years.is_integer():
        years = int(years)
    return f"Dans {years} an(s)" if is_future else f"Il y a {years} an(s)"


def format_gap_label(days: int) -> str:
    """Format elapsed gap duration in human-readable French."""
    months = round(days / 30.4375)
    if months < 12:
        return f"+{months} mois"
    years = days // 365
    rem_months = round((days % 365) / 30.4375)
    if rem_months > 0 and years < 3:
        return f"+{years} an{'s' if years > 1 else ''} et {rem_months} m."
    return f"+{years} an{'s' if years > 1 else ''}"


def get_property_timeline(property_id: int) -> Dict[str, Any]:
    """Aggregate, sort, and compress timeline events for a given property."""
    today = datetime.date.today()
    events: List[Dict[str, Any]] = []

    conn = get_db_connection()
    try:
        # 1. Property acquisition & creation milestone
        prop = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
        if prop:
            acq_date = parse_date(prop["acquisition_date"]) or parse_date(prop["created_at"])
            if acq_date:
                events.append({
                    "id": f"prop_{prop['id']}",
                    "type": "event",
                    "category": "property",
                    "date": acq_date,
                    "title": f"Acquisition : {prop['name']}",
                    "subtitle": f"{prop['address']}, {prop['city']}" if prop['city'] else prop['address'],
                    "amount": f"{prop['acquisition_price']:,.0f} €".replace(",", " ") if prop['acquisition_price'] else None,
                    "icon": "fa-solid fa-house-chimney",
                    "badge_text": "Acquisition",
                    "badge_class": "badge-accent",
                    "url": f"/properties/{prop['id']}",
                })

        # 2. Past Maintenance Logs
        logs = conn.execute(
            """
            SELECT l.*, t.title AS task_title, t.category AS task_category
            FROM maintenance_logs l
            JOIN maintenance_tasks t ON l.task_id = t.id
            WHERE l.property_id = ?
            ORDER BY l.performed_date ASC
            """,
            (property_id,),
        ).fetchall()

        for log in logs:
            p_date = parse_date(log["performed_date"])
            if p_date:
                sub = []
                if log["performed_by"]:
                    sub.append(log["performed_by"])
                if log["cost"]:
                    sub.append(f"{log['cost']:,.0f} €".replace(",", " "))
                events.append({
                    "id": f"maint_log_{log['id']}",
                    "type": "event",
                    "category": "maintenance",
                    "date": p_date,
                    "title": log["task_title"],
                    "subtitle": " • ".join(sub) if sub else log["task_category"],
                    "amount": f"{log['cost']:,.0f} €".replace(",", " ") if log["cost"] else None,
                    "icon": "fa-solid fa-clipboard-check",
                    "badge_text": "Intervention réalisée",
                    "badge_class": "badge-success",
                    "url": f"/maintenance?property_id={property_id}",
                })

        # 3. Future / Scheduled Maintenance Tasks
        tasks = conn.execute(
            "SELECT * FROM maintenance_tasks WHERE property_id = ? ORDER BY next_due_date ASC",
            (property_id,),
        ).fetchall()

        for t in tasks:
            due_date = parse_date(t["next_due_date"])
            if due_date:
                is_overdue = due_date < today
                days_diff = (due_date - today).days
                if is_overdue:
                    badge_class = "badge-danger"
                    badge_text = "En retard"
                elif days_diff <= 30:
                    badge_class = "badge-warning"
                    badge_text = "À faire sous 30 j"
                else:
                    badge_class = "badge-secondary"
                    badge_text = "Planifié"

                sub = []
                if t["preferred_contractor"]:
                    sub.append(t["preferred_contractor"])
                if t["estimated_cost"]:
                    sub.append(f"~{t['estimated_cost']:,.0f} €".replace(",", " "))

                events.append({
                    "id": f"maint_task_{t['id']}",
                    "type": "event",
                    "category": "maintenance",
                    "date": due_date,
                    "title": t["title"],
                    "subtitle": " • ".join(sub) if sub else t["category"],
                    "amount": f"{t['estimated_cost']:,.0f} €".replace(",", " ") if t["estimated_cost"] else None,
                    "icon": "fa-solid fa-wrench",
                    "badge_text": badge_text,
                    "badge_class": badge_class,
                    "url": f"/maintenance?property_id={property_id}",
                })

        # 4. Renovations & Works
        renovs = conn.execute(
            "SELECT * FROM renovations WHERE property_id = ? ORDER BY created_at ASC",
            (property_id,),
        ).fetchall()

        for r in renovs:
            s_date = parse_date(r["start_date"])
            e_date = parse_date(r["end_date"])

            # Start event
            if s_date:
                events.append({
                    "id": f"renov_start_{r['id']}",
                    "type": "event",
                    "category": "renovation",
                    "date": s_date,
                    "title": f"Chantier : {r['title']}",
                    "subtitle": f"Début des travaux • {r['category']}",
                    "amount": f"{r['actual_cost'] or r['estimated_budget'] or 0:,.0f} €".replace(",", " "),
                    "icon": "fa-solid fa-hammer",
                    "badge_text": r["status"],
                    "badge_class": "badge-accent" if r["status"] == "En cours" else "badge-secondary",
                    "url": f"/renovations/{r['id']}",
                })

            # End event
            if e_date and (not s_date or e_date != s_date):
                events.append({
                    "id": f"renov_end_{r['id']}",
                    "type": "event",
                    "category": "renovation",
                    "date": e_date,
                    "title": f"Livraison : {r['title']}",
                    "subtitle": f"Fin des travaux • {r['contractor_name'] or r['category']}",
                    "amount": f"{r['actual_cost']:,.0f} €".replace(",", " ") if r["actual_cost"] else None,
                    "icon": "fa-solid fa-flag-checkered",
                    "badge_text": "Terminé",
                    "badge_class": "badge-success",
                    "url": f"/renovations/{r['id']}",
                })

        # 5. Inventory: Purchases & Warranty Expirations
        items = conn.execute(
            "SELECT * FROM inventory WHERE property_id = ? ORDER BY created_at ASC",
            (property_id,),
        ).fetchall()

        for it in items:
            p_date = parse_date(it["purchase_date"])
            w_date = parse_date(it["warranty_expiry_date"])

            if p_date:
                events.append({
                    "id": f"inv_buy_{it['id']}",
                    "type": "event",
                    "category": "inventory",
                    "date": p_date,
                    "title": f"Achat : {it['name']}",
                    "subtitle": f"{it['brand'] or ''} {it['model_number'] or ''}".strip() or it["category"],
                    "amount": f"{it['purchase_price']:,.0f} €".replace(",", " ") if it["purchase_price"] else None,
                    "icon": "fa-solid fa-box-open",
                    "badge_text": "Achat équipement",
                    "badge_class": "badge-secondary",
                    "url": f"/inventory?property_id={property_id}",
                })

            if w_date:
                is_expired = w_date < today
                days_left = (w_date - today).days
                if is_expired:
                    w_badge = "badge-danger"
                    w_text = "Garantie expirée"
                elif days_left <= 60:
                    w_badge = "badge-warning"
                    w_text = "Fin de garantie imminente"
                else:
                    w_badge = "badge-accent"
                    w_text = "Sous garantie"

                events.append({
                    "id": f"inv_warr_{it['id']}",
                    "type": "event",
                    "category": "inventory",
                    "date": w_date,
                    "title": f"Garantie : {it['name']}",
                    "subtitle": f"Échéance garantie constructeur • {it['brand'] or it['category']}",
                    "amount": None,
                    "icon": "fa-solid fa-shield-halved",
                    "badge_text": w_text,
                    "badge_class": w_badge,
                    "url": f"/inventory?property_id={property_id}",
                })

        # 6. Taxes & Fiscal milestones
        taxes = conn.execute(
            "SELECT * FROM taxes WHERE property_id = ? ORDER BY tax_year ASC, due_date ASC",
            (property_id,),
        ).fetchall()

        for tx in taxes:
            d_due = parse_date(tx["due_date"])
            if d_due:
                is_overdue = (d_due < today) and (tx["status"] == "À payer")
                if tx["status"] == "Payé":
                    badge_class = "badge-success"
                    badge_text = "Payé"
                elif tx["status"] == "Mensualisé":
                    badge_class = "badge-accent"
                    badge_text = "Mensualisé"
                elif is_overdue:
                    badge_class = "badge-danger"
                    badge_text = "Échéance dépassée"
                else:
                    badge_class = "badge-warning"
                    badge_text = "À payer"

                sub = [f"Année {tx['tax_year']}"]
                if tx["teom_amount"]:
                    sub.append(f"dont TEOM {tx['teom_amount']:,.0f} €".replace(",", " "))
                if tx["reference_number"]:
                    sub.append(f"Réf: {tx['reference_number']}")

                events.append({
                    "id": f"tax_{tx['id']}",
                    "type": "event",
                    "category": "tax",
                    "date": d_due,
                    "title": f"{tx['tax_type']} {tx['tax_year']}",
                    "subtitle": " • ".join(sub),
                    "amount": f"{tx['amount']:,.0f} €".replace(",", " "),
                    "icon": "fa-solid fa-landmark",
                    "badge_text": badge_text,
                    "badge_class": badge_class,
                    "url": f"/taxes?property_id={property_id}",
                })
    finally:
        conn.close()

    # Sort all events chronologically
    events.sort(key=lambda ev: ev["date"])

    # Format event labels
    for ev in events:
        ev["date_str"] = ev["date"].isoformat()
        ev["formatted_date"] = format_french_date(ev["date"])
        ev["relative_label"] = get_relative_time_label(ev["date"], today)
        ev["is_past"] = ev["date"] < today
        ev["is_future"] = ev["date"] > today
        ev["is_today"] = ev["date"] == today

    # Prepare list with "Now / Maintenant" beacon and compressed gaps
    now_node = {
        "id": "timeline-now",
        "type": "now",
        "category": "now",
        "date": today,
        "date_str": today.isoformat(),
        "formatted_date": format_french_date(today),
        "title": "Aujourd'hui",
        "subtitle": "Repère actuel",
        "relative_label": "Maintenant",
        "icon": "fa-solid fa-location-crosshairs",
        "badge_text": "Présent",
        "badge_class": "badge-accent",
        "url": "#",
    }

    # Partition events into past and future around today
    past_events = [e for e in events if e["date"] <= today]
    future_events = [e for e in events if e["date"] > today]

    # Combine past -> now -> future
    combined_nodes: List[Dict[str, Any]] = []

    # If there are past events, append them
    combined_nodes.extend(past_events)
    # Append the "Now" marker
    combined_nodes.append(now_node)
    # Append future events
    combined_nodes.extend(future_events)

    # Sort combined nodes strictly by date
    # In case an event falls exactly on today, keep the 'now' node adjacent
    combined_nodes.sort(key=lambda n: (n["date"], 0 if n["type"] != "now" else 1))

    # Apply temporal compression: insert gaps between nodes if delta > 60 days
    final_items: List[Dict[str, Any]] = []
    gap_threshold_days = 60

    for i, node in enumerate(combined_nodes):
        if i > 0:
            prev_node = combined_nodes[i - 1]
            delta_days = (node["date"] - prev_node["date"]).days
            if delta_days > gap_threshold_days:
                final_items.append({
                    "type": "gap",
                    "days": delta_days,
                    "label": format_gap_label(delta_days),
                })
        final_items.append(node)

    now_index = next((idx for idx, item in enumerate(final_items) if item.get("type") == "now"), 0)

    categories = [
        {"id": "all", "label": "Tous", "icon": "fa-solid fa-layer-group"},
        {"id": "maintenance", "label": "Entretien", "icon": "fa-solid fa-wrench"},
        {"id": "renovation", "label": "Travaux", "icon": "fa-solid fa-hammer"},
        {"id": "tax", "label": "Fiscalité", "icon": "fa-solid fa-landmark"},
        {"id": "inventory", "label": "Équipements", "icon": "fa-solid fa-box-open"},
        {"id": "property", "label": "Logement", "icon": "fa-solid fa-house"},
    ]

    return {
        "events": final_items,
        "items": final_items,
        "total_events": len(events),
        "past_count": len(past_events),
        "future_count": len(future_events),
        "now_index": now_index,
        "categories": categories,
    }
