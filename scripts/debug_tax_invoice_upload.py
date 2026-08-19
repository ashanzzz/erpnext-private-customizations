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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 捕获浏览器控制台日志
    logs = []
    page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: logs.append(f"[PAGE ERROR] {err}"))

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 访问 tax-invoice-center
    print("Navigating to tax-invoice-center...")
    page.goto(f"{SITE_URL}/desk/tax-invoice-center")
    time.sleep(3)

    print("Console logs after load:")
    for l in logs:
        print("  ", l)

    # 检查按钮是否存在
    btn = page.query_selector("#btn-upload")
    print("btn-upload found:", bool(btn))
    if btn:
        print("btn-upload text:", btn.inner_text())

    # 点击上传发票按钮
    print("Clicking #btn-upload...")
    page.click("#btn-upload")
    time.sleep(1)

    modal = page.query_selector(".modal-dialog")
    print("Modal dialog visible:", bool(modal))

    # 截图
    shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\debug_upload_btn.png"
    page.screenshot(path=shot)
    print("Saved screenshot to:", shot)

    print("\nAll Console logs:")
    for l in logs:
        print("  ", l)

    browser.close()
