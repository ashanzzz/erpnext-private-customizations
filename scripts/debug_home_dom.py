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

    page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: print(f"[Browser Error] {err}"))

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(3)

    page.goto(f"{SITE_URL}/desk/my-business")
    time.sleep(4)
    page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\debug_home.png")

    info = page.evaluate("""() => {
        const blocks = Array.from(document.querySelectorAll('.custom-html-block, [data-block-name]')).map(b => b.className + ' | ' + b.getAttribute('data-block-name'));
        const html = document.querySelector('.layout-main-section') ? document.querySelector('.layout-main-section').innerHTML : '';
        return {
            blocks: blocks,
            html_len: html.length,
            has_my_tasks: !!document.querySelector('#my-tasks-container'),
            has_periodic: !!document.querySelector('#periodic-tasks-container'),
            has_biz_container: !!document.querySelector('.biz-nav-container')
        };
    }""")
    print("DOM Info:", info)
    browser.close()
