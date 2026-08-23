import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

BRAIN_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\a49c8c70-7676-4c94-94f3-1677812d32e8"

def main():
    console_errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        def on_console(msg):
            if msg.type == "error":
                text = msg.text
                if "socket.io" not in text and "favicon" not in text and "Invalid origin" not in text:
                    console_errors.append(text)
                    print(f"[CONSOLE ERROR] {text}")

        page.on("console", on_console)

        print("1. Logging into ERPNext...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(6000)

        print("2. Navigating to Procurement Order Picker Workbench...")
        page.evaluate("frappe.set_route('procurement-order-picker')")
        page.wait_for_selector(".picker-page-container", timeout=15000)
        page.wait_for_timeout(3000)

        # Tab 1: item_to_mr (物料选单 ➔ 采购申请)
        print("Testing Tab 1 (物料选单 ➔ 采购申请)...")
        page.click(".picker-tab-btn[data-stage='item_to_mr']")
        page.wait_for_timeout(2000)
        shot1 = os.path.join(BRAIN_DIR, "step1_item_to_mr.png")
        page.screenshot(path=shot1)
        print(f"Captured Step 1 screenshot: {shot1}")

        # Tab 2: mr_to_po (采购订货)
        print("Testing Tab 2 (采购订货)...")
        page.click(".picker-tab-btn[data-stage='mr_to_po']")
        page.wait_for_timeout(2000)
        shot2 = os.path.join(BRAIN_DIR, "step2_mr_to_po.png")
        page.screenshot(path=shot2)
        print(f"Captured Step 2 screenshot: {shot2}")

        # Tab 3: po_to_pr (采购入库)
        print("Testing Tab 3 (采购入库)...")
        page.click(".picker-tab-btn[data-stage='po_to_pr']")
        page.wait_for_timeout(2000)
        shot3 = os.path.join(BRAIN_DIR, "step3_po_to_pr.png")
        page.screenshot(path=shot3)
        print(f"Captured Step 3 screenshot: {shot3}")

        # Tab 4: pr_to_pi (采购开票)
        print("Testing Tab 4 (采购开票)...")
        page.click(".picker-tab-btn[data-stage='pr_to_pi']")
        page.wait_for_timeout(2000)
        shot4 = os.path.join(BRAIN_DIR, "step4_pr_to_pi.png")
        page.screenshot(path=shot4)
        print(f"Captured Step 4 screenshot: {shot4}")

        # Tab 5: pi_to_rr (报销付款)
        print("Testing Tab 5 (报销付款)...")
        page.click(".picker-tab-btn[data-stage='pi_to_rr']")
        page.wait_for_timeout(2000)
        shot5 = os.path.join(BRAIN_DIR, "step5_pi_to_rr.png")
        page.screenshot(path=shot5)
        print(f"Captured Step 5 screenshot: {shot5}")

        # --- Test Core User Requirement: Company Exclusive Dynamic Lock on Selection ---
        print("\n3. Testing Core User Requirement: Company Exclusive Dynamic Lock...")
        # Switch back to Tab 1 (item_to_mr) where rows from multiple companies exist
        page.click(".picker-tab-btn[data-stage='item_to_mr']")
        page.wait_for_timeout(2000)

        # Check total rows visible before selection
        total_rows_before = page.locator("#picker-table-tbody tr:not(.picker-row-company-hidden)").count()
        print(f"Total visible rows in 'All Companies' mode: {total_rows_before}")

        # Check the first row
        first_checkbox = page.locator("#picker-table-tbody tr:first-child .picker-row-checkbox")
        if first_checkbox.count() > 0:
            first_checkbox.check()
            page.wait_for_timeout(1000)

            # Verify lock banner is active
            banner_visible = page.is_visible("#picker-company-lock-banner.is-active")
            print(f"Company Lock Notice Banner Active: {banner_visible}")

            shot_locked = os.path.join(BRAIN_DIR, "exclusive_company_lock_active.png")
            page.screenshot(path=shot_locked)
            print(f"Captured Exclusive Company Lock screenshot: {shot_locked}")

            # Now uncheck the first row
            first_checkbox.uncheck()
            page.wait_for_timeout(1000)

            banner_visible_after = page.is_visible("#picker-company-lock-banner.is-active")
            print(f"Company Lock Notice Banner after Uncheck: {banner_visible_after} (should be False)")

            shot_unlocked = os.path.join(BRAIN_DIR, "exclusive_company_lock_restored.png")
            page.screenshot(path=shot_unlocked)
            print(f"Captured Restored View screenshot: {shot_unlocked}")

        browser.close()

    print("\n--- UI Verification Result ---")
    print(f"Console Errors Count: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] 0 Console Errors across all 5 natural steps and company lock interactions!")

if __name__ == "__main__":
    main()
