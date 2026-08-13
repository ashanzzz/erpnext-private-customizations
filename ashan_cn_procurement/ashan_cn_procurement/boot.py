import os
import frappe

def set_login_redirect(*args, **kwargs):
    """
    Hook for on_session_creation.
    Forces login_manager.home_page and frappe.local.response['home_page'] to /desk/my-business.
    """
    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = "/desk/my-business"
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = "/desk/my-business"
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = "/desk/my-business"

def get_website_user_home_page(user):
    return "/desk/my-business"

def boot_session(bootinfo):
    bootinfo.home_page = "my-business"
    bootinfo.default_route = "my-business"

    # Automatically purge cached legacy asset file on server disk on every boot
    clean_js = """// Copyright (c) 2026, Ashan CN Procurement
(function() {
    window.init_ashan_cn_sidebar = function() { return false; };
    function purge() {
        if (typeof $ !== 'undefined') {
            $('#ashan-cn-sidebar-container, .ashan-sidebar-wrapper').remove();
        }
    }
    purge();
    if (typeof $ !== 'undefined') {
        $(document).ready(purge);
        $(document).on('app_ready page-change route-change toolbar_setup', purge);
    }
    setInterval(purge, 100);
})();
"""
    try:
        paths_to_clean = [
            frappe.get_site_path("public", "js", "ashan_cn_sidebar.js"),
            os.path.abspath(os.path.join(frappe.get_app_path("frappe"), "..", "..", "sites", "assets", "ashan_cn_procurement", "js", "ashan_cn_sidebar.js")),
            os.path.abspath(os.path.join(frappe.get_app_path("ashan_cn_procurement"), "public", "js", "ashan_cn_sidebar.js"))
        ]
        for p in paths_to_clean:
            if os.path.exists(p):
                with open(p, "w", encoding="utf-8") as f:
                    f.write(clean_js)
    except Exception:
        pass

