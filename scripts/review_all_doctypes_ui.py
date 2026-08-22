import os
import time
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

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def review_all_doctypes_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()

        # 1. 登录
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(3)

        doctypes = [
            ("Material Request", "material-request", "review_list_material_request.png", "review_form_material_request.png"),
            ("Purchase Order", "purchase-order", "review_list_purchase_order.png", "review_form_purchase_order.png"),
            ("Purchase Receipt", "purchase-receipt", "review_list_purchase_receipt.png", "review_form_purchase_receipt.png"),
            ("Purchase Invoice", "purchase-invoice", "review_list_purchase_invoice.png", "review_form_purchase_invoice.png"),
            ("Reimbursement Request", "reimbursement-request", "review_list_reimbursement_request.png", "review_form_reimbursement_request.png"),
        ]

        review_results = {}

        for dt_name, route, list_img, form_img in doctypes:
            print(f"\n--- Checking {dt_name} ({route}) ---")
            # 1. List View
            page.goto(f"{SITE_URL}/desk/{route}")
            time.sleep(3)
            page.wait_for_selector(".frappe-list", timeout=10000)
            time.sleep(2)
            page.screenshot(path=os.path.join(ARTIFACT_DIR, list_img))

            # 检查 List 中是否有 custom_doc_details 列和 badges
            list_info = page.evaluate("""() => {
                const header_labels = Array.from(document.querySelectorAll('.list-row-head .list-row-col span')).map(s => s.innerText.trim()).filter(Boolean);
                const has_doc_details_col = header_labels.some(l => l.includes('单据明细') || l.includes('明细'));
                const badges_count = document.querySelectorAll('.doc-details-badges-wrapper').length;
                const sample_badge_text = document.querySelector('.doc-details-badges-wrapper') ? document.querySelector('.doc-details-badges-wrapper').innerText : '';
                return {
                    header_labels: header_labels,
                    has_doc_details_col: has_doc_details_col,
                    badges_count: badges_count,
                    sample_badge_text: sample_badge_text
                };
            }""")
            print(f"List View Evaluation: badges_count={list_info['badges_count']}, has_col={list_info['has_doc_details_col']}")

            # 2. Form View (打开第一个单据或新建表单查看字段)
            has_first_doc = page.evaluate("""() => {
                const first_row = document.querySelector('.list-row-container .list-row');
                return !!first_row;
            }""")

            if has_first_doc:
                page.click(".list-row-container .list-row .list-subject a, .list-row-container .list-row a")
                time.sleep(3)
                page.wait_for_selector(".form-layout", timeout=10000)
                time.sleep(2)
            else:
                page.goto(f"{SITE_URL}/desk/{route}/new")
                time.sleep(3)
                page.wait_for_selector(".form-layout", timeout=10000)
                time.sleep(2)

            page.screenshot(path=os.path.join(ARTIFACT_DIR, form_img))

            form_info = page.evaluate("""() => {
                const field = document.querySelector('[data-fieldname="custom_doc_details"]');
                const label = field ? (field.querySelector('.control-label') ? field.querySelector('.control-label').innerText : '') : '';
                const is_readonly = field ? field.classList.contains('form-control-read-only') || !!field.querySelector('[readonly]') || !!field.querySelector('.control-value') : false;
                const val = field ? (field.querySelector('.control-value') ? field.querySelector('.control-value').innerText : (field.querySelector('textarea, input') ? field.querySelector('textarea, input').value : '')) : '';
                return {
                    has_field: !!field,
                    label: label.trim(),
                    is_readonly: is_readonly,
                    val_len: val.trim().length
                };
            }""")
            print(f"Form View Evaluation: has_field={form_info['has_field']}, is_readonly={form_info['is_readonly']}")


            review_results[dt_name] = {
                "list": list_info,
                "form": form_info
            }

        browser.close()
        print("\nAll Reviews and Screenshots completed!")
        return review_results

if __name__ == "__main__":
    review_all_doctypes_ui()
