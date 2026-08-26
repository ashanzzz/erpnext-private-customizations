import os
import frappe


BUSINESS_SIDEBAR_NAMES = {
    "my business",
    "accounting and finance",
    "ashan cn procurement",
    "company compliance center",
    "procurement management",
    "property and lease",
    "stock and inventory",
    "vehicle fuel hub",
}
SYSTEM_MANAGEMENT_LABEL = "系统管理"
SYSTEM_MANAGEMENT_URLS = {
    "/desk/client-script",
    "/desk/customize-form/Customize%20Form",
    "/desk/server-script",
    "/desk/system-settings",
}

PROCUREMENT_PAGE_ROLES = {
    "material-request-workbench": {
        "Purchase Manager",
        "Purchase User",
        "Stock Manager",
        "Stock User",
    },
    "procurement-execution-workbench": {
        "Purchase Manager",
        "Purchase User",
        "Accounts Manager",
        "Accounts User",
    },
    "material-receipt-workbench": {"Stock Manager", "Stock User"},
}


def _resolve_login_home_route(roles):
    """Return one canonical Desk route for the user's business roles."""
    roles = set(roles or [])

    if "System Manager" in roles or "Administrator" in roles:
        return "/desk/Workspaces/Home"
    if roles.intersection({"Purchase User", "Purchase Manager"}):
        return "/desk/Workspaces/Procurement Management"
    if roles.intersection({"Stock User", "Stock Manager"}):
        return "/desk/Workspaces/Stock and Inventory"
    if roles.intersection({"Accounts User", "Accounts Manager"}):
        return "/desk/Workspaces/Accounting and Finance"
    if roles.intersection({"Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"}):
        return "/desk/oil-card-ledger"

    # Do not send unrelated users to the oil-card console.
    return "/desk/Workspaces/Home"


def set_login_redirect(*args, **kwargs):
    """Hook for on_session_creation using the same role routing as Desk V2."""
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    home_route = _resolve_login_home_route(roles)

    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = home_route
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = home_route
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = home_route


def get_website_user_home_page(user):
    """Website hook matching the same role-aware Desk destination."""
    roles = frappe.get_roles(user) if user else []
    return _resolve_login_home_route(roles).lstrip("/")


def boot_session(bootinfo):
    """
    extend_bootinfo hook: 注入 bootinfo 字段。

    Frappe v16 pageview.js line 52:
        name = frappe.boot ? frappe.boot.home_page : window.page_name;
        frappe.views.pageview.with_page(name, ...)
    → home_page 必须是一个真实存在的 Frappe Page name。
    → 'desktop' 对应 tabPage 中 name='desktop' 的页面——这是 Frappe 原生大图标页。

    对于导航到我们自定义 Workspace 'Home'，则需要通过
    前端 JS (ashan_cn_sidebar_v2.js) 在 Desk 加载完成后主动调用
    frappe.set_route(['Workspaces', 'Home']) 实现跳转。
    """
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    role_set = set(roles)
    is_system_manager = "System Manager" in roles or "Administrator" in roles
    home_route = _resolve_login_home_route(roles)
    bootinfo.ashan_is_system_manager = is_system_manager
    bootinfo.ashan_home_route = home_route
    if user and user != "Guest":
        from ashan_cn_procurement.services.work_context_service import get_work_context

        bootinfo.ashan_work_context = get_work_context(user)

    # bootinfo.home_page must be a real Frappe Page name, not a Workspace route.
    # Only dedicated oil-card users use the custom Page as their fallback; all other
    # business roles fall back to Frappe's desktop and are routed by the login hooks /
    # Sidebar V2 to the appropriate Workspace.
    bootinfo.home_page = "oil-card-ledger" if home_route == "/desk/oil-card-ledger" else "desktop"

    # 动态净化侧边栏并注入两页独立工作台项目
    for sidebar_name, sidebar in (bootinfo.get("workspace_sidebar_item") or {}).items():
        if isinstance(sidebar, dict) and "items" in sidebar:
            items = sidebar.get("items", [])
            new_items = []
            has_lease_bench = any("lease-settlement-workbench" in str(it.get("link_to", "")) or "lease-settlement-workbench" in str(it.get("url", "")) for it in items)

            for it in items:
                link_to = str(it.get("link_to", ""))
                url = str(it.get("url", ""))

                # 过滤已废弃的收费标准版本 (已与 Property Lease 合并)
                if link_to == "Property Charge Rate" or "property-charge-rate" in url or it.get("label") == "收费标准版本":
                    continue

                # 过滤系统管理
                if not is_system_manager and sidebar_name in BUSINESS_SIDEBAR_NAMES:
                    if it.get("label") == SYSTEM_MANAGEMENT_LABEL or url in SYSTEM_MANAGEMENT_URLS:
                        continue

                required_roles = PROCUREMENT_PAGE_ROLES.get(link_to)
                if required_roles and not is_system_manager and not role_set.intersection(required_roles):
                    continue


                if "property-settlement-workbench" in link_to or "property-settlement-workbench" in url:
                    it["label"] = "水电费月结工作台"
                    new_items.append(it)
                    if not has_lease_bench:
                        new_items.append({
                            "label": "房租与物业费工作台",
                            "link_type": "Page",
                            "type": "Link",
                            "link_to": "lease-settlement-workbench",
                            "url": "/desk/lease-settlement-workbench",
                            "child": 1,
                            "collapsible": 0,
                            "indent": 0,
                            "keep_closed": 0,
                            "show_arrow": 0,
                            "doctype": "Workspace Sidebar Item"
                        })
                else:
                    new_items.append(it)
            sidebar["items"] = new_items
