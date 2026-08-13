import frappe

def get_website_user_home_page(user):
    return "/app/my-business"

def set_login_redirect(login_manager=None):
    """
    Hooks into on_session_creation to set home_page in response to /app/my-business.
    """
    frappe.local.response["home_page"] = "/app/my-business"
    if hasattr(frappe, "response"):
        frappe.response["home_page"] = "/app/my-business"

def boot_session(bootinfo):
    """
    Overrides bootinfo home_page and default_route for Desk SPA router.
    """
    bootinfo.home_page = "my-business"
    bootinfo.default_route = "my-business"
