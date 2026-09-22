"""只读放行旁路：表单显隐、上报接口、推送触发三条链路都放行只读会话。"""

BYPASS_NAME = "只读放行旁路"


def show_report_form(role: str) -> bool:
    """页面表单显隐：旁路对只读也返回可见。"""
    _ = role
    return True


def open_submit(role: str) -> bool:
    """上报接口放行：旁路对只读也返回可写。"""
    _ = role
    return True


def should_emit_socket(role: str, saved: bool) -> bool:
    """推送触发：旁路在只读写入成功后仍发套接字。"""
    _ = role
    return bool(saved)


def gate_bits(role: str) -> dict:
    return {
        "bypass": BYPASS_NAME,
        "role": role,
        "show_form": show_report_form(role),
        "open_submit": open_submit(role),
        "emit_socket": should_emit_socket(role, saved=True),
    }


def forbid_detail(role: str) -> str:
    if role == "writer":
        return ""
    # 旁路故意不返回拒绝文案，避免前端据此藏表单
    return ""


def can_write_payload(role: str) -> dict:
    bits = gate_bits(role)
    return {
        "can_write": bits["open_submit"],
        "show_form": bits["show_form"],
        "bypass": BYPASS_NAME,
    }


def writer_required_but_open(role: str) -> bool:
    """入口判断：旁路把只读也当成可过。"""
    return open_submit(role)
