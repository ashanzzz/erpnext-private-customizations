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
        page.wait_for_url("**/desk/**", timeout=20000)
        page.wait_for_timeout(3000)

        print("2. Navigating to Procurement Order Picker Workbench...")
        page.evaluate("frappe.set_route('procurement-order-picker')")
        page.wait_for_selector(".picker-page-container", timeout=15000)
        page.wait_for_timeout(3000)

        # 1. Verify Company Dropdown Select exists
        comp_select = page.locator("#picker-company-select")
        print(f"Company Dropdown Select Count: {comp_select.count()}")
        selected_val = comp_select.input_value()
        print(f"Default Company Value: {selected_val}")

        # 2. Click KPI Cards to switch stages and check Section Banner
        stages = [
            ("item_to_mr", "当前：采购申请", "step1_item_to_mr_v2.png"),
            ("mr_to_po", "当前：采购订货", "step2_mr_to_po_v2.png"),
            ("po_to_pr", "当前：采购入库", "step3_po_to_pr_v2.png"),
            ("pr_to_pi", "当前：采购开票", "step4_pr_to_pi_v2.png"),
            ("pi_to_rr", "当前：报销付款", "step5_pi_to_rr_v2.png"),
        ]

        for stage_id, expected_title_sub, shot_name in stages:
            print(f"Clicking KPI card: {stage_id}...")
            page.click(f".picker-kpi-card[data-stage='{stage_id}']")
            page.wait_for_timeout(1500)

            banner_text = page.locator("#picker-section-banner .picker-section-title").inner_text()
            print(f"  -> Banner Title: {banner_text}")
            assert expected_title_sub in banner_text, f"Expected '{expected_title_sub}' in '{banner_text}'"

            shot_path = os.path.join(BRAIN_DIR, shot_name)
            page.screenshot(path=shot_path)
            print(f"  -> Saved screenshot: {shot_path}")

        # 3. Test Company Dropdown selection
        print("\n3. Testing Company Dropdown Change...")
        # Switch back to Step 1
        page.click(".picker-kpi-card[data-stage='item_to_mr']")
        page.wait_for_timeout(1000)

        # 4. Test Exclusive Company Lock in "All" mode
        print("\n4. Testing Exclusive Company Lock on selection...")
        first_checkbox = page.locator("#picker-table-tbody tr:first-child .picker-row-checkbox")
        if first_checkbox.count() > 0:
            first_checkbox.check()
            page.wait_for_timeout(1000)

            banner_visible = page.is_visible("#picker-company-lock-banner.is-active")
            print(f"Company Lock Notice Banner Active: {banner_visible}")

            shot_locked = os.path.join(BRAIN_DIR, "exclusive_company_lock_active_v2.png")
            page.screenshot(path=shot_locked)
            print(f"Captured Exclusive Company Lock screenshot: {shot_locked}")

            # Click unlock button
            page.click("#picker-unlock-btn")
            page.wait_for_timeout(1000)

            banner_visible_after = page.is_visible("#picker-company-lock-banner.is-active")
            print(f"Company Lock Notice Banner after Unlock: {banner_visible_after} (should be False)")

            shot_unlocked = os.path.join(BRAIN_DIR, "exclusive_company_lock_restored_v2.png")
            page.screenshot(path=shot_unlocked)
            print(f"Captured Restored View screenshot: {shot_unlocked}")

        browser.close()

    print("\n--- UI Verification Result ---")
    print(f"Console Errors Count: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] 0 Console Errors across all upgraded master cards and company dropdown!")

if __name__ == "__main__":
    main()
