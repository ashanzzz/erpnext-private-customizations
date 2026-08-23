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

        # 1. Step 1: 采购申请 (明细 & 单号视图)
        print("Testing Step 1: 采购申请 (Detail & Doc Views)...")
        page.click(".picker-kpi-card[data-stage='item_to_mr']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step1_mr_detail.png"))

        page.click(".picker-view-btn[data-mode='doc']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step1_mr_doc.png"))

        # 2. Step 1: Smart Material Request Modal with Real-time Search & Tax Calc
        print("Testing Smart Modal: + 新建物料申请单...")
        page.click("#picker-create-mr-btn")
        page.wait_for_timeout(1000)

        # Trigger autocomplete search
        page.fill(".modal-input-code", "ITEM")
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_modal_autocomplete.png"))

        # Select first suggestion item
        page.click(".picker-suggest-item:first-child")
        page.wait_for_timeout(600)

        # Fill quantity to 5.0
        page.fill(".modal-input-qty", "5")
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_modal_calculated.png"))

        # Close dialog
        page.click(".modal-header .btn-modal-close, .modal-header .close")
        page.wait_for_timeout(800)

        # 3. Step 2: 采购订货 (Detail & Doc Views)
        print("Testing Step 2: 采购订货 (Detail & Doc Views)...")
        page.click(".picker-kpi-card[data-stage='mr_to_po']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step2_po_detail.png"))

        page.click(".picker-view-btn[data-mode='doc']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step2_po_doc.png"))

        # 4. Step 3: 采购入库 (Detail & Doc Views)
        print("Testing Step 3: 采购入库 (Detail & Doc Views)...")
        page.click(".picker-kpi-card[data-stage='po_to_pr']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step3_pr_detail.png"))

        page.click(".picker-view-btn[data-mode='doc']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step3_pr_doc.png"))

        # 5. Step 4: 采购开票 (Detail & Doc Views)
        print("Testing Step 4: 采购开票 (Detail & Doc Views)...")
        page.click(".picker-kpi-card[data-stage='pr_to_pi']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step4_pi_detail.png"))

        page.click(".picker-view-btn[data-mode='doc']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step4_pi_doc.png"))

        # 6. Step 5: 报销付款 (Detail & Doc Views)
        print("Testing Step 5: 报销付款 (Detail & Doc Views)...")
        page.click(".picker-kpi-card[data-stage='pi_to_rr']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step5_rr_doc.png"))

        page.click(".picker-view-btn[data-mode='detail']")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(BRAIN_DIR, "v4_step5_rr_detail.png"))

        browser.close()

    print("\n--- UI Verification Result ---")
    print(f"Console Errors Count: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] 0 Console Errors across all 5 stages in both Detail and Doc views & smart calculation modal!")

if __name__ == "__main__":
    main()
