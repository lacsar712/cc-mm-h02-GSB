"""读写权限：仅 writer（瓦斯检查员）可写，reader 为只读会话。

三条链路统一在这一个模块收口，缺角色或未知角色一律拒绝：
- 页面表单显隐 show_report_form
- 上报接口放行 open_submit
- 套接字推送触发 should_emit_socket

角色固定在账号体系内，不提供可配置角色的管理台。
"""

WRITER_ROLE = "writer"
FORBID_DETAIL = "仅瓦斯检查员可上报"


def is_writer(role: str | None) -> bool:
    return role == WRITER_ROLE


def show_report_form(role: str | None) -> bool:
    """页面表单显隐：只有检查员的页面画出上报表单。"""
    return is_writer(role)


def open_submit(role: str | None) -> bool:
    """上报接口放行：只有检查员提交的读数可入库。"""
    return is_writer(role)


def should_emit_socket(role: str | None, saved: bool) -> bool:
    """推送触发：只有检查员写入成功后，才向已打开的页面推送。"""
    return is_writer(role) and bool(saved)


def can_write_payload(role: str | None) -> dict:
    writable = is_writer(role)
    return {"can_write": writable, "show_form": writable}
