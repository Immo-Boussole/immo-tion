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


# ── Apprise Push Dispatcher ───────────────────────────────────────────────────

def _send_via_apprise(apprise_url: str, title: str, body: str) -> bool:
    """Send a notification synchronously via Apprise to a given target URL."""
    if not apprise_url or not apprise_url.strip():
        return False
    try:
        import apprise
        ap = apprise.Apprise()
        ap.add(apprise_url.strip())
        return ap.notify(title=title, body=body)
    except Exception as e:
        logger.error("Apprise notification failed for url %s: %s", apprise_url[:30], e)
        return False


async def send_test_notification(apprise_url: str) -> bool:
    """Send a test notification to verify an Apprise URL."""
    import asyncio
    title = f"✅ Test {settings.APP_NAME}"
    body = (
        f"Vos notifications pour {settings.APP_NAME} sont correctement configurées !\n"
        "Vous recevrez désormais les alertes d'entretien, de fiscalité et de chantiers."
    )
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_via_apprise, apprise_url, title, body)


# ── Notification Orchestrator ─────────────────────────────────────────────────

async def dispatch_notification(
    title: str,
    message: str,
    category: str = "system",
    property_id: Optional[int] = None,
    user_id: Optional[int] = None,
    link_url: Optional[str] = None,
    event_key: Optional[str] = None,
    db_path: Optional[Any] = None,
) -> Optional[int]:
    """
    Central dispatcher for all notifications in Immo-Tion.
    
    1. Checks deduplication (event_key). If already notified, skips.
    2. Persists In-App notification in SQLite.
    3. Dispatches to Apprise URLs (user-specific and/or global setting).
    4. Dispatches to configured webhooks.
    5. Dispatches SMTP email if configured and recipient email is present.
    """
    import asyncio
    from app.database import (
        create_notification,
        is_event_already_notified,
        get_user_apprise_urls,
        get_db_connection,
    )

    # 1. Deduplication check
    if event_key and is_event_already_notified(event_key, db_path=db_path):
        logger.debug("Notification skipped (already notified): event_key=%s", event_key)
        return None

    # 2. Persist in-app notification
    notif_id = create_notification(
        title=title,
        message=message,
        category=category,
        property_id=property_id,
        user_id=user_id,
        link_url=link_url,
        event_key=event_key,
        db_path=db_path,
    )

    # 3. Gather Apprise target URLs
    target_urls = set()
    if settings.APPRISE_URL and settings.APPRISE_URL.strip():
        target_urls.add(settings.APPRISE_URL.strip())

    if user_id:
        conn = get_db_connection(db_path)
        try:
            u = conn.execute("SELECT apprise_url, email FROM users WHERE id = ?", (user_id,)).fetchone()
            if u and u["apprise_url"] and u["apprise_url"].strip():
                target_urls.add(u["apprise_url"].strip())
            recipient_email = u["email"] if u else None
        finally:
            conn.close()
    else:
        # Broadcast to all users who configured an Apprise URL
        for url in get_user_apprise_urls(db_path=db_path):
            target_urls.add(url)
        recipient_email = None

    # 4. Dispatch Apprise in background threads
    if target_urls:
        loop = asyncio.get_running_loop()
        full_title = f"[{settings.APP_NAME}] {title}"

        async def _run_apprise(target_url: str):
            try:
                await loop.run_in_executor(None, _send_via_apprise, target_url, full_title, message)
            except Exception as e:
                logger.error("Apprise background task failed: %s", e)

        for url in target_urls:
            asyncio.create_task(_run_apprise(url))

    # 5. Dispatch Webhooks
    asyncio.create_task(
        dispatch_webhook_alert(
            event_type=f"notification.{category}",
            data={
                "id": notif_id,
                "title": title,
                "message": message,
                "category": category,
                "property_id": property_id,
                "link_url": link_url,
                "event_key": event_key,
            },
        )
    )

    # 6. Dispatch Email SMTP if configured
    if recipient_email:
        asyncio.create_task(
            send_email_alert(subject=title, body_text=message, recipient_email=recipient_email)
        )

    return notif_id

