from conftest import login, row_count


def test_inspector_alarm_written_and_pushed(client_env):
    """检查员报一笔报警浓度：201 成功、库里多一行、级别为报警、页面收到推送。"""
    client, session_local, reading_model = client_env
    token = login(client, "gasman", "gas123456")
    headers = {"Authorization": f"Bearer {token}"}

    before = row_count(session_local, reading_model)

    with client.websocket_connect("/ws/alerts") as ws:
        res = client.post(
            "/api/readings",
            headers=headers,
            json={"site": "掘进面-03", "ch4_pct": 1.05},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["site"] == "掘进面-03"
        assert body["ch4_pct"] == 1.05
        assert body["level"] == "报警"
        assert body["note"] == "甲烷达到报警线"

        # 库里确实多一行
        assert row_count(session_local, reading_model) == before + 1

        db = session_local()
        try:
            row = db.query(reading_model).filter_by(id=body["id"]).one()
            assert row.created_by == "gasman"
            assert row.level == "报警"
        finally:
            db.close()

        # 连着的页面收到这笔报警推送
        pushed = ws.receive_json()
        assert pushed["id"] == body["id"]
        assert pushed["level"] == "报警"
