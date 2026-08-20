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

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 点击左上角应用主菜单
    page.click(".app-switcher-menu, .navbar-brand, .sidebar-header, .app-switcher")
    time.sleep(1)

    # 截图 1: 左上角主菜单汉化效果
    shot_menu = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_navbar_menu_zh.png"
    page.screenshot(path=shot_menu)
    print("Saved Navbar Menu Shot:", shot_menu)

    # 3. 悬停展开【界面显示】或【帮助与支持】
    page.hover(".menu-item-title:has-text('界面显示'), .menu-item-title:has-text('Display')")
    time.sleep(0.8)

    # 截图 2: 二级子菜单汉化效果
    shot_submenu = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_navbar_submenu_zh.png"
    page.screenshot(path=shot_submenu)
    print("Saved Submenu Shot:", shot_submenu)

    browser.close()
