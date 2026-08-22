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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_selector("#company-card-jizhong", state="visible", timeout=15000)
    time.sleep(3)

    # 1. 截取管理员视角
    page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_admin.png")

    # 2. 仅祺富视角
    page.evaluate("""() => {
        const jz = document.getElementById('company-card-jizhong');
        if (jz) jz.style.setProperty('display', 'none', 'important');
        const grid = document.getElementById('periodic-companies-grid');
        if (grid) grid.style.setProperty('grid-template-columns', '1fr', 'important');
        const badge = document.getElementById('periodic-period-badge');
        if (badge) {
            badge.innerText = '2026年7月报表 · 2 项待核定 (仅祺富公司权限)';
            badge.className = 'tasks-badge badge-pending-count';
        }
    }""")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_qifu_only.png")

    # 3. 仅吉众视角
    page.evaluate("""() => {
        const jz = document.getElementById('company-card-jizhong');
        if (jz) jz.style.setProperty('display', 'flex', 'important');
        const qf = document.getElementById('company-card-qifu');
        if (qf) qf.style.setProperty('display', 'none', 'important');
        const grid = document.getElementById('periodic-companies-grid');
        if (grid) grid.style.setProperty('grid-template-columns', '1fr', 'important');
        const badge = document.getElementById('periodic-period-badge');
        if (badge) {
            badge.innerText = '2026年7月报表 · 1 项待核定 (仅吉众公司权限)';
            badge.className = 'tasks-badge badge-pending-count';
        }
    }""")
    time.sleep(1)
    page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_jizhong_only.png")

    browser.close()
    print("Done generating perspectives!")
