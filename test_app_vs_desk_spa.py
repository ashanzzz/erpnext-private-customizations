import os
import json
from playwright.sync_api import sync_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = 'http://192.168.8.11:6888'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        print("Logged in. Initial URL:", page.url)

        # Test frappe.set_route in console
        print("\nExecuting frappe.set_route('procurement-management') via JS console...")
        page.evaluate("frappe.set_route('procurement-management')")
        page.wait_for_timeout(2000)
        print("URL after frappe.set_route('procurement-management'):", page.url)

        print("\nExecuting frappe.set_route('stock-and-inventory') via JS console...")
        page.evaluate("frappe.set_route('stock-and-inventory')")
        page.wait_for_timeout(2000)
        print("URL after frappe.set_route('stock-and-inventory'):", page.url)

        print("\nExecuting frappe.set_route('my-business') via JS console...")
        page.evaluate("frappe.set_route('my-business')")
        page.wait_for_timeout(2000)
        print("URL after frappe.set_route('my-business'):", page.url)

        browser.close()

if __name__ == "__main__":
    main()
