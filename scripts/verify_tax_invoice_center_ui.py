import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        # 1. Login
        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", timeout=10000)
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_timeout(3500)

        # 2. Go to Tax Invoice Center
        print("2. Opening /desk/tax-invoice-center...")
        page.goto(f"{SITE_URL}/desk/tax-invoice-center")
        page.wait_for_timeout(3500)

        main_shot = os.path.join(ARTIFACT_DIR, "live_acceptance_tax_invoice_center_populated.png")
        page.screenshot(path=main_shot)
        print(f"   Main screenshot saved: {main_shot}")

        # 3. Expand first row
        print("3. Expanding first row...")
        first_row = page.locator("#tbody-tax-invoices tr.data-row").first
        if first_row.is_visible():
            first_row.click()
            page.wait_for_timeout(1500)
            expanded_shot = os.path.join(ARTIFACT_DIR, "live_acceptance_tax_invoice_expanded_drawer.png")
            page.screenshot(path=expanded_shot)
            print(f"   Expanded drawer screenshot saved: {expanded_shot}")

        # 4. Open upload modal
        print("4. Opening upload modal...")
        page.click("#btn-upload")
        page.wait_for_timeout(1000)
        upload_shot = os.path.join(ARTIFACT_DIR, "live_acceptance_tax_invoice_upload_modal.png")
        page.screenshot(path=upload_shot)
        print(f"   Upload modal screenshot saved: {upload_shot}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 5. Open settings modal
        print("5. Opening settings modal...")
        page.click("#btn-settings")
        page.wait_for_timeout(1000)
        settings_shot = os.path.join(ARTIFACT_DIR, "live_acceptance_tax_invoice_settings_modal.png")
        page.screenshot(path=settings_shot)
        print(f"   Settings modal screenshot saved: {settings_shot}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        browser.close()
        print("UI Verification completed successfully!")

if __name__ == '__main__':
    verify_ui()
