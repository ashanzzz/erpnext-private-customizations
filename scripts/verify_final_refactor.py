import os
import json
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

import urllib.request
for i in range(30):
    try:
        urllib.request.urlopen(f"{SITE_URL}/login", timeout=3)
        print("Server is up!")
        break
    except Exception:
        time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(3)

    # 1. 截取主页月度任务最新效果
    shot_home = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_home_monthly_pure.png"
    page.screenshot(path=shot_home)
    print("Saved Home Shot:", shot_home)

    # 2. 前往房租与物业费工作台
    page.goto(f"{SITE_URL}/desk/lease-settlement-workbench")
    page.wait_for_selector("#dim-switch-group", state="visible", timeout=15000)
    time.sleep(2)

    shot_workbench = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_annual_lease_workbench_final.png"
    page.screenshot(path=shot_workbench)
    print("Saved Final Workbench Shot:", shot_workbench)

    browser.close()
