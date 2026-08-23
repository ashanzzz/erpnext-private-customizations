import os
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
        page.wait_for_timeout(4000)

        print("2. Navigating to Procurement Order Picker Workbench...")
        page.evaluate("frappe.set_route('procurement-order-picker')")
        page.wait_for_selector(".picker-page-container", timeout=15000)
        page.wait_for_timeout(3000)

        # Tab 1: MR -> PO
        shot1 = os.path.join(BRAIN_DIR, "tab1_mr_to_po.png")
        page.screenshot(path=shot1)
        print(f"Captured Stage 1 screenshot: {shot1}")

        # Tab 2: PO -> PR
        print("Switching to Tab 2 (PO -> PR)...")
        page.click(".picker-tab-btn[data-stage='po_to_pr']")
        page.wait_for_timeout(2000)
        shot2 = os.path.join(BRAIN_DIR, "tab2_po_to_pr.png")
        page.screenshot(path=shot2)
        print(f"Captured Stage 2 screenshot: {shot2}")

        # Tab 3: PR -> PI
        print("Switching to Tab 3 (PR -> PI)...")
        page.click(".picker-tab-btn[data-stage='pr_to_pi']")
        page.wait_for_timeout(2000)
        shot3 = os.path.join(BRAIN_DIR, "tab3_pr_to_pi.png")
        page.screenshot(path=shot3)
        print(f"Captured Stage 3 screenshot: {shot3}")

        # Tab 4: PI -> RR
        print("Switching to Tab 4 (PI -> RR)...")
        page.click(".picker-tab-btn[data-stage='pi_to_rr']")
        page.wait_for_timeout(2000)
        shot4 = os.path.join(BRAIN_DIR, "tab4_pi_to_rr.png")
        page.screenshot(path=shot4)
        print(f"Captured Stage 4 screenshot: {shot4}")

        # Test Purchase Order List button injection
        print("Testing Purchase Order List custom button...")
        page.evaluate("frappe.set_route('List', 'Purchase Order', 'List')")
        page.wait_for_timeout(3000)
        shot5 = os.path.join(BRAIN_DIR, "purchase_order_list_with_button.png")
        page.screenshot(path=shot5)
        print(f"Captured Purchase Order List screenshot: {shot5}")

        # Test Purchase Receipt List button injection
        print("Testing Purchase Receipt List custom button...")
        page.evaluate("frappe.set_route('List', 'Purchase Receipt', 'List')")
        page.wait_for_timeout(3000)
        shot6 = os.path.join(BRAIN_DIR, "purchase_receipt_list_with_button.png")
        page.screenshot(path=shot6)
        print(f"Captured Purchase Receipt List screenshot: {shot6}")

        # Test Purchase Invoice List button injection
        print("Testing Purchase Invoice List custom button...")
        page.evaluate("frappe.set_route('List', 'Purchase Invoice', 'List')")
        page.wait_for_timeout(3000)
        shot7 = os.path.join(BRAIN_DIR, "purchase_invoice_list_with_button.png")
        page.screenshot(path=shot7)
        print(f"Captured Purchase Invoice List screenshot: {shot7}")

        # Test Reimbursement Request List button injection
        print("Testing Reimbursement Request List custom button...")
        page.evaluate("frappe.set_route('List', 'Reimbursement Request', 'List')")
        page.wait_for_timeout(3000)
        shot8 = os.path.join(BRAIN_DIR, "reimbursement_request_list_with_button.png")
        page.screenshot(path=shot8)
        print(f"Captured Reimbursement Request List screenshot: {shot8}")

        browser.close()

    print("\n--- UI Verification Result ---")
    print(f"Console Errors Count: {len(console_errors)}")
    if console_errors:
        for err in console_errors:
            print(f"  - {err}")
    else:
        print("[SUCCESS] 0 Console Errors across all tested pages and workflows!")

if __name__ == "__main__":
    main()
