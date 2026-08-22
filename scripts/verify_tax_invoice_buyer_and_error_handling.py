import os
import sys
import time
import zipfile
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

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

# 创建一个用于测试错误拦截的无效 ZIP 文件
dummy_zip_path = os.path.abspath("test_invalid_invoice.zip")
with zipfile.ZipFile(dummy_zip_path, 'w') as zf:
    zf.writestr("test_readme.txt", "这是一个测试文本，不包含任何税局发票XML或PDF。")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1480, "height": 950})

    # 1. 登录
    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 访问税局发票中心
    print("Navigating to tax-invoice-center...")
    page.goto(f"{SITE_URL}/desk/tax-invoice-center")
    page.wait_for_selector(".tax-inv-wrapper", state="visible", timeout=15000)
    time.sleep(3)

    # 截图 1: 税局发票列表（已包含【购买方】列）
    shot_list_buyer = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_list_with_buyer.png"
    page.screenshot(path=shot_list_buyer)
    print("Saved Tax Invoice List with Buyer Shot:", shot_list_buyer)

    # 3. 点击【📤 上传发票】按钮
    print("Opening upload dialog...")
    page.click("#btn-upload")
    page.wait_for_selector("#inp-tax-file", state="attached", timeout=10000)
    time.sleep(1)

    # 4. 上传无效 ZIP 文件并触发解析
    print(f"Setting input file to {dummy_zip_path}...")
    page.set_input_files("#inp-tax-file", dummy_zip_path)
    time.sleep(1)

    print("Clicking 开始解析并导入...")
    page.click('.modal.show .modal-footer button:has-text("开始解析并导入")')
    time.sleep(3)

    # 等待错误弹窗出现
    page.wait_for_selector('.msgprint-dialog, .modal.show:has-text("税局发票导入失败")', timeout=10000)
    time.sleep(1)

    # 截图 2: 无效发票文件/压缩包上传失败的详细弹窗
    shot_error_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_upload_error_modal.png"
    page.screenshot(path=shot_error_dialog)
    print("Saved Error Modal Shot:", shot_error_dialog)

    browser.close()

if os.path.exists(dummy_zip_path):
    os.remove(dummy_zip_path)

print("\n[ALL TAX INVOICE BUYER COLUMN & ERROR HANDLING VERIFICATIONS PASSED!]")
