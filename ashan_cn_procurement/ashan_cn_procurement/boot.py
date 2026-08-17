import os
import frappe


BUSINESS_SIDEBAR_NAMES = {
    "my business",
    "accounting and finance",
    "ashan cn procurement",
    "company compliance center",
    "procurement management",
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

def set_login_redirect(*args, **kwargs):
    """
    Hook for on_session_creation.
    根据用户角色动态决定登录后跳转的目标首页
    """
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    if "System Manager" in roles or "Administrator" in roles:
        home_route = "/desk/my-business"
    elif any(r in roles for r in ["Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]):
        home_route = "/desk/oil-card-ledger"
    elif any(r in roles for r in ["Stock User", "Stock Manager"]):
        home_route = "/desk/stock-entry"
    elif any(r in roles for r in ["Purchase User", "Purchase Manager"]):
        home_route = "/desk/purchase-order"
    else:
        home_route = "/desk/oil-card-ledger"

    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = home_route
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = home_route
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = home_route

def get_website_user_home_page(user):
    roles = frappe.get_roles(user) if user else []
    if "System Manager" in roles or "Administrator" in roles:
        return "/desk/my-business"
    return "/desk/oil-card-ledger"

def boot_session(bootinfo):
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    is_system_manager = "System Manager" in roles or "Administrator" in roles
    bootinfo.ashan_is_system_manager = is_system_manager

    if is_system_manager:
        bootinfo.home_page = "my-business"
        bootinfo.default_route = "my-business"
    else:
        bootinfo.home_page = "oil-card-ledger"
        bootinfo.default_route = "oil-card-ledger"

    if is_system_manager:
        return

    # Workspace Sidebar Item has no native role field in Frappe v16. Filter
    # this app-owned group while composing the Desk boot payload so ordinary
    # users never receive the system-management links in their sidebar.
    for sidebar_name, sidebar in (bootinfo.get("workspace_sidebar_item") or {}).items():
        if sidebar_name not in BUSINESS_SIDEBAR_NAMES:
            continue
        sidebar["items"] = [
            item
            for item in sidebar.get("items", [])
            if item.get("label") != SYSTEM_MANAGEMENT_LABEL
            and item.get("url") not in SYSTEM_MANAGEMENT_URLS
        ]
