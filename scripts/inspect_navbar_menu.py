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
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 点击左上角应用/主菜单按钮
    # 查找左上角触发元素 (如 .app-switcher, .dropdown-navbar-new, .navbar-brand, etc.)
    page.click(".app-switcher-menu, .navbar-brand, .sidebar-header, .app-switcher, .dropdown-item")
    time.sleep(1)

    # 打印页面中所有的 dropdown-menu 内容
    menus = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('.dropdown-menu, .app-switcher-dropdown, .popover, [role="menu"]'));
        return els.map(e => ({
            className: e.className,
            innerHTML: e.innerHTML,
            innerText: e.innerText
        }));
    }""")

    print(f"找到 {len(menus)} 个下拉菜单:")
    for idx, m in enumerate(menus, 1):
        print(f"[{idx}] Class: {m['className']}")
        print(f"    Text:\n{m['innerText']}")
        print("-" * 50)

    browser.close()
