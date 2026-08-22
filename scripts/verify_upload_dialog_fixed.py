import os
import sys
import time
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 访问税局发票中心
    page.goto(f"{SITE_URL}/desk/tax-invoice-center")
    page.wait_for_selector("#btn-upload", state="visible", timeout=15000)
    time.sleep(1)

    # 3. 点击【📤 上传发票 (PDF/ZIP)】按钮
    page.click("#btn-upload")
    page.wait_for_selector(".modal-dialog", state="visible")
    time.sleep(0.5)

    # 截图 1: 上传弹窗 (原生覆盖层 + 浏览选择按钮)
    shot_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_upload_dialog.png"
    page.screenshot(path=shot_dialog)
    print("Saved Dialog Shot:", shot_dialog)

    # 4. 模拟通过 input[type=file] 选择发票文件
    sample_pdf = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\media_1786978206771.pdf"
    if os.path.exists(sample_pdf):
        page.set_input_files("#inp-tax-file", sample_pdf)
        time.sleep(1)

        # 截图 2: 选中文件后的状态 (清单展示与开始处理按钮)
        shot_selected = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_file_selected.png"
        page.screenshot(path=shot_selected)
        print("Saved Selected Shot:", shot_selected)

        # 点击开始解析并导入
        page.click(".modal-footer .btn-primary")
        time.sleep(3)

        # 截图 3: 导入成功并刷新数据看板
        shot_imported = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_imported_success.png"
        page.screenshot(path=shot_imported)
        print("Saved Imported Shot:", shot_imported)

    browser.close()
