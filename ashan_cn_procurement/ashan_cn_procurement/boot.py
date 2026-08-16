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
    Forces login_manager.home_page and frappe.local.response['home_page'] to /desk/home.
    """
    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = "/desk/home"
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = "/desk/home"
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = "/desk/home"

def get_website_user_home_page(user):
    return "/desk/home"

def boot_session(bootinfo):
    bootinfo.home_page = "home"
    bootinfo.default_route = "home"
    is_system_manager = "System Manager" in frappe.get_roles(frappe.session.user)
    bootinfo.ashan_is_system_manager = is_system_manager

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
