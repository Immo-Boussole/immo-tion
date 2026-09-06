"""Unit tests for scheduler logic and status evaluations."""

import datetime
from app.scheduler import evaluate_task_status


def test_evaluate_task_status_overdue():
    past_date = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    res = evaluate_task_status(past_date)
    assert res["status"] == "overdue"
    assert res["badge"] == "danger"
    assert res["days_remaining"] == -10
    assert "En retard" in res["label_fr"]


def test_evaluate_task_status_due_soon():
    soon_date = (datetime.date.today() + datetime.timedelta(days=15)).isoformat()
    res = evaluate_task_status(soon_date)
    assert res["status"] == "due_soon"
    assert res["badge"] == "warning"
    assert res["days_remaining"] == 15
    assert "À faire sous" in res["label_fr"]


def test_evaluate_task_status_ok():
    future_date = (datetime.date.today() + datetime.timedelta(days=120)).isoformat()
    res = evaluate_task_status(future_date)
    assert res["status"] == "ok"
    assert res["badge"] == "success"
    assert res["days_remaining"] == 120
    assert "À jour" in res["label_fr"]
