from conftest import login, row_count


def test_reader_submit_rejected_and_db_unchanged(client_env):
    """只读会话：表单不放行、上报 403、库内行数不变、不产生套接字推送。"""
    client, session_local, reading_model = client_env
    viewer_token = login(client, "viewer", "view123456")
    writer_token = login(client, "gasman", "gas123456")
    headers_viewer = {"Authorization": f"Bearer {viewer_token}"}
    headers_writer = {"Authorization": f"Bearer {writer_token}"}

    # can-write 必须如实告诉前端：只读不可写、不显示表单
    gate = client.get("/api/auth/can-write", headers=headers_viewer)
    assert gate.status_code == 200
    assert gate.json() == {"can_write": False, "show_form": False}

    # 检查员的 can-write 仍然放行（不能误伤合法上报）
    gate_writer = client.get("/api/auth/can-write", headers=headers_writer)
    assert gate_writer.json() == {"can_write": True, "show_form": True}

    before = row_count(session_local, reading_model)

    # 先挂上一个页面：只读提交若误触发推送，消息会先到这里
    with client.websocket_connect("/ws/alerts") as ws:
        res = client.post(
            "/api/readings",
            headers=headers_viewer,
            json={"site": "回风巷", "ch4_pct": 1.2},
        )
        assert res.status_code == 403

        # 库不增行
        assert row_count(session_local, reading_model) == before

        # 检查员随后报一笔报警：页面收到的第一条推送必须是检查员这笔，
        # 说明只读那笔既没落库也没推送
        alarm = client.post(
            "/api/readings",
            headers=headers_writer,
            json={"site": "回风巷", "ch4_pct": 1.2},
        )
        assert alarm.status_code == 201
        pushed = ws.receive_json()
        assert pushed["site"] == "回风巷"
        assert pushed["level"] == "报警"
        assert pushed["id"] == alarm.json()["id"]
