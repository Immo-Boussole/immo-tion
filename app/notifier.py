"""Multi-channel notification dispatcher (iCal, SMTP Email, Webhooks)."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("immo_tion.notifier")


def generate_ical_feed(property_name: str, tasks: List[Dict[str, Any]]) -> str:
    """Generate an iCalendar (.ics) feed format for maintenance tasks."""
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Immo-Boussole//Immo-Tion//FR",
        f"X-WR-CALNAME:Immo-Tion - {property_name}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for t in tasks:
        due_date_raw = t.get("next_due_date")
        if not due_date_raw:
            continue
        # Convert YYYY-MM-DD to YYYYMMDD
        due_compact = str(due_date_raw).replace("-", "")
        uid = f"task-{t['id']}@immo-tion.local"
        summary = f"🔧 {t.get('title', 'Entretien')}"
        desc = f"Catégorie: {t.get('category')}\\nRécurrence: tous les {t.get('recurrence_months')} mois\\nIntervenant: {t.get('preferred_contractor', 'N/A')}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;VALUE=DATE:{due_compact}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


async def send_email_alert(subject: str, body_text: str, recipient_email: str) -> bool:
    """Send an alert email via SMTP if configured."""
    if not settings.SMTP_HOST:
        logger.info("SMTP not configured, skipping email alert.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = recipient_email
        msg["Subject"] = f"[{settings.APP_NAME}] {subject}"
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Email alert sent successfully to %s", recipient_email)
        return True
    except Exception as e:
        logger.error("Failed to send email alert: %s", e)
        return False


async def dispatch_webhook_alert(event_type: str, data: Dict[str, Any]) -> List[bool]:
    """Broadcast an alert event to configured webhooks (Home Assistant, Discord, etc.)."""
    urls = settings.parsed_webhook_urls
    if not urls:
        return []

    payload = {
        "source": settings.APP_NAME,
        "event": event_type,
        "data": data,
    }

    results = []
    async with httpx.AsyncClient(timeout=8.0) as client:
        for url in urls:
            try:
                resp = await client.post(url, json=payload)
                results.append(resp.is_success)
            except Exception as e:
                logger.error("Webhook dispatch failed for %s: %s", url, e)
                results.append(False)
    return results
