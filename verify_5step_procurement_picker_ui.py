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

        # 1. Verify Step 1 Detail View (Single-line Header, Readonly qty, View switcher)
        print("Testing Step 1: 采购申请 (明细视图)...")
        page.click(".picker-kpi-card[data-stage='item_to_mr']")
        page.wait_for_timeout(1500)
        shot1_detail = os.path.join(BRAIN_DIR, "step1_mr_detail_view.png")
        page.screenshot(path=shot1_detail)
        print(f"  -> Saved Step 1 Detail View screenshot: {shot1_detail}")

        # 2. Test Step 1 Doc View Switch
        print("Testing Step 1: 采购申请 (切换单号视图)...")
        page.click(".picker-view-btn[data-mode='doc']")
        page.wait_for_timeout(1500)
        shot1_doc = os.path.join(BRAIN_DIR, "step1_mr_doc_view.png")
        page.screenshot(path=shot1_doc)
        print(f"  -> Saved Step 1 Doc View screenshot: {shot1_doc}")

        # Switch back to Detail
        page.click(".picker-view-btn[data-mode='detail']")
        page.wait_for_timeout(1000)

        # 3. Test + 新建物料申请单 Dialog
        print("Testing Modal: + 新建物料申请单...")
        page.click("#picker-create-mr-btn")
        page.wait_for_timeout(1000)
        shot_modal = os.path.join(BRAIN_DIR, "step1_create_mr_modal.png")
        page.screenshot(path=shot_modal)
        print(f"  -> Saved Modal Dialog screenshot: {shot_modal}")

        # Close modal
        page.click(".modal-header .btn-modal-close, .modal-header .close")
        page.wait_for_timeout(1000)

        # 4. Step 2 (采购订货)
        print("Testing Step 2: 采购订货 (单行表头)...")
        page.click(".picker-kpi-card[data-stage='mr_to_po']")
        page.wait_for_timeout(1500)
        shot2 = os.path.join(BRAIN_DIR, "step2_mr_to_po_v3.png")
        page.screenshot(path=shot2)
        print(f"  -> Saved Step 2 screenshot: {shot2}")

        # 5. Step 3 (采购入库)
        print("Testing Step 3: 采购入库 (单行表头)...")
        page.click(".picker-kpi-card[data-stage='po_to_pr']")
        page.wait_for_timeout(1500)
        shot3 = os.path.join(BRAIN_DIR, "step3_po_to_pr_v3.png")
        page.screenshot(path=shot3)
        print(f"  -> Saved Step 3 screenshot: {shot3}")

        # 6. Step 4 (采购开票)
        print("Testing Step 4: 采购开票 (单行表头)...")
        page.click(".picker-kpi-card[data-stage='pr_to_pi']")
        page.wait_for_timeout(1500)
        shot4 = os.path.join(BRAIN_DIR, "step4_pr_to_pi_v3.png")
        page.screenshot(path=shot4)
        print(f"  -> Saved Step 4 screenshot: {shot4}")

        # 7. Step 5 (报销付款)
        print("Testing Step 5: 报销付款 (单行表头)...")
        page.click(".picker-kpi-card[data-stage='pi_to_rr']")
        page.wait_for_timeout(1500)
        shot5 = os.path.join(BRAIN_DIR, "step5_pi_to_rr_v3.png")
        page.screenshot(path=shot5)
        print(f"  -> Saved Step 5 screenshot: {shot5}")

        browser.close()

    print("\n--- UI Verification Result ---")
    print(f"Console Errors Count: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] 0 Console Errors across all single-line headers, dual views & modal creation!")

if __name__ == "__main__":
    main()
