import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        # Fresh login
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", timeout=10000)
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_timeout(6000)  # Wait longer for redirect + sidebar to load

        shot = os.path.join(ARTIFACT_DIR, "sidebar_after_login_redirect.png")
        page.screenshot(path=shot)
        print(f"Shot 1 (after login + redirect): {shot}")
        print(f"URL: {page.url}")

        # Check sidebar DOM
        sidebar = page.locator(".body-sidebar")
        sidebar_visible = sidebar.is_visible() if sidebar.count() > 0 else False
        print(f"Sidebar visible: {sidebar_visible}")

        sidebar_html = sidebar.inner_html() if sidebar.count() > 0 else "NOT FOUND"
        print(f"Sidebar HTML length: {len(sidebar_html)}")
        print(f"Sidebar HTML snippet: {sidebar_html[:500]}")

        # Check route
        route = page.evaluate("() => frappe.get_route_str ? frappe.get_route_str() : 'n/a'")
        print(f"Route: {route}")

        # Check sidebar_data in frappe
        sidebar_data = page.evaluate("""() => {
            try {
                const s = frappe.workspace_sidebar;
                if (!s) return 'no sidebar object';
                return JSON.stringify({
                    title: s.sidebar_title,
                    items_count: s.workspace_sidebar_items ? s.workspace_sidebar_items.length : 0
                });
            } catch(e) { return 'error: ' + e.message; }
        }""")
        print(f"Sidebar data: {sidebar_data}")

        # Wait 3 more seconds and shoot again
        page.wait_for_timeout(3000)
        shot2 = os.path.join(ARTIFACT_DIR, "sidebar_after_login_redirect_3s.png")
        page.screenshot(path=shot2)
        print(f"Shot 2 (after +3s): {shot2}")

        browser.close()

if __name__ == '__main__':
    verify()
