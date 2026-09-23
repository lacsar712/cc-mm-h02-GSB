"""只读会话三条链路全部被挡；检查员报警上报成功并推送。"""

import pytest

from app.permissions import (
    can_write_payload,
    open_submit,
    should_emit_socket,
    show_report_form,
)
from app.main import Reading, SessionLocal


ALARM_PCT = 1.25


def test_reader_rejected_and_db_unchanged(client, viewer_headers, count_snapshot):
    """只读会话报一笔报警浓度：接口 403，库中一行不多。"""
    res = client.post(
        "/api/readings",
        headers=viewer_headers,
        json={"site": "只读越权测点", "ch4_pct": ALARM_PCT},
    )
    assert res.status_code == 403
    db = SessionLocal()
    try:
        assert db.query(Reading).count() == count_snapshot
        assert db.query(Reading).filter(Reading.site == "只读越权测点").first() is None
    finally:
        db.close()


def test_writer_alarm_creates_one_row(client, writer_headers, count_snapshot):
    """检查员报一笔报警浓度：201 入库，库刚好多一行且判定为报警。"""
    res = client.post(
        "/api/readings",
        headers=writer_headers,
        json={"site": "回风巷-复检", "ch4_pct": ALARM_PCT},
    )
    assert res.status_code == 201, res.text
    payload = res.json()
    assert payload["level"] == "报警"
    assert payload["site"] == "回风巷-复检"
    db = SessionLocal()
    try:
        assert db.query(Reading).count() == count_snapshot + 1
        row = db.query(Reading).filter(Reading.site == "回风巷-复检").one()
        assert row.ch4_pct == ALARM_PCT
        assert row.level == "报警"
        assert row.created_by == "gasman"
    finally:
        db.close()


def test_can_write_gate_per_role(client, viewer_headers, writer_headers):
    """页面表单显隐依据的门控：只读收起，检查员放行。"""
    viewer_gate = client.get("/api/auth/can-write", headers=viewer_headers).json()
    assert viewer_gate == {"can_write": False, "show_form": False}

    writer_gate = client.get("/api/auth/can-write", headers=writer_headers).json()
    assert writer_gate == {"can_write": True, "show_form": True}


def test_submit_requires_token(client):
    res = client.post(
        "/api/readings", json={"site": "无令牌测点", "ch4_pct": ALARM_PCT}
    )
    assert res.status_code == 401


@pytest.mark.parametrize("role", ["reader", "viewer", "", None, "admin"])
def test_permission_module_denies_non_writer(role):
    """权限收口：任何非 writer 角色在三条链路上都被挡。"""
    assert show_report_form(role) is False
    assert open_submit(role) is False
    assert should_emit_socket(role, saved=True) is False
    assert can_write_payload(role) == {"can_write": False, "show_form": False}


def test_permission_module_allows_writer():
    assert show_report_form("writer") is True
    assert open_submit("writer") is True
    assert should_emit_socket("writer", saved=True) is True
    assert should_emit_socket("writer", saved=False) is False


def test_socket_only_emitted_for_writer(client, viewer_headers, writer_headers):
    """只读提交不触发套接字；检查员报警推送恰好一条。"""
    with client.websocket_connect("/ws/alerts") as ws:
        rejected = client.post(
            "/api/readings",
            headers=viewer_headers,
            json={"site": "只读旁路测点", "ch4_pct": ALARM_PCT},
        )
        assert rejected.status_code == 403

        pushed = client.post(
            "/api/readings",
            headers=writer_headers,
            json={"site": "推送报警测点", "ch4_pct": ALARM_PCT},
        )
        assert pushed.status_code == 201

        msg = ws.receive_json()
        assert msg["site"] == "推送报警测点"
        assert msg["level"] == "报警"
