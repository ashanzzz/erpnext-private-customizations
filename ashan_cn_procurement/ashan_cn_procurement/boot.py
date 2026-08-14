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
