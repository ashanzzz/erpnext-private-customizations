import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

# 等待站点就绪
for i in range(25):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

local_excel_path = r"d:\SynologyDrive团队\antigravity\erpnext16\祺富工资2026.7.xlsx"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1700, "height": 1050})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    print("\n--- Testing 母表全员与老板娘表智能融合 ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-qifu-import-excel", state="visible", timeout=15000)
    time.sleep(2)

    # 打开导入弹窗
    print("Opening Local Upload Dialog...")
    page.click("#btn-qifu-import-excel")
    time.sleep(1)

    # 投递本地 2026.7 Excel
    page.set_input_files("#inp-qifu-salary-file", local_excel_path)
    time.sleep(2)

    # 点击开始解析
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(2)

    # 截图融合后的 2026-07 工作台
    shot_fusion = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_master_data_fusion_2026_07.png"
    page.screenshot(path=shot_fusion)
    print("Saved Master Data Fusion Shot:", shot_fusion)

    browser.close()

print("\n[MASTER DATA FUSION VERIFICATION COMPLETED!]")
