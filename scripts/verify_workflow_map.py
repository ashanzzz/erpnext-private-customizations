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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1150})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 导航到人事薪酬月结
    page.goto(f"{SITE_URL}/desk/payroll-settlement-workbench")
    page.wait_for_selector(".payroll-unified-header-bar", state="visible", timeout=15000)
    time.sleep(2)

    # 截图 1: 点击 [ 🧭 业务操作流程导图 ] (吉众流水线)
    page.click(".payroll-view-tab[data-view='workflow']")
    time.sleep(1)
    shot_jz_flow = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_workflow_jizhong.png"
    page.screenshot(path=shot_jz_flow)
    print("Saved Jizhong Workflow Shot:", shot_jz_flow)

    # 截图 2: 切换到【🏢 祺富机械】查看祺富专属业务流水线 (包含老板娘工资表导入)
    page.click(".payroll-comp-tab-btn[data-comp='天津祺富机械加工有限公司']")
    time.sleep(1.5)
    shot_qf_flow = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_workflow_qifu.png"
    page.screenshot(path=shot_qf_flow)
    print("Saved Qifu Workflow Shot:", shot_qf_flow)

    browser.close()
