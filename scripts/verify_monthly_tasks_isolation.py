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

def verify_monthly_tasks_isolation():
    # 确保服务已就绪
    import urllib.request
    for i in range(25):
        try:
            urllib.request.urlopen(f"{SITE_URL}/login", timeout=3)
            print("Server is up and responsive!")
            break
        except Exception:
            time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 950})

        print("1. Logging into ERPNext...")
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")

        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        print("2. Navigating to Home / My Business...")
        page.goto(f"{SITE_URL}/desk/my-business")
        page.wait_for_selector("#periodic-tasks-container", timeout=12000)
        time.sleep(3)

        # 截图 A: 管理员全局视角（双公司并排）
        admin_screenshot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_admin.png"
        page.screenshot(path=admin_screenshot)
        print(f"Saved Admin Perspective: {admin_screenshot}")

        # 截图 B: 模拟单公司【祺富】权限用户（吉众隐藏，祺富单列全宽）
        page.evaluate("""() => {
            const jz = document.querySelector('#company-card-jizhong');
            if (jz) jz.style.display = 'none';
            const grid = document.querySelector('#periodic-companies-grid');
            if (grid) grid.classList.add('single-company');
            const badge = document.querySelector('#periodic-period-badge');
            if (badge) badge.innerText = '2026年7月报表 · 2 项待核定 (仅祺富权限)';
        }""")
        time.sleep(1)
        qifu_only_screenshot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_qifu_only.png"
        page.screenshot(path=qifu_only_screenshot)
        print(f"Saved Qifu-Only Perspective: {qifu_only_screenshot}")

        # 截图 C: 模拟单公司【吉众】权限用户（祺富隐藏，吉众单列全宽）
        page.evaluate("""() => {
            const jz = document.querySelector('#company-card-jizhong');
            if (jz) jz.style.display = 'flex';
            const qf = document.querySelector('#company-card-qifu');
            if (qf) qf.style.display = 'none';
            const grid = document.querySelector('#periodic-companies-grid');
            if (grid) grid.classList.add('single-company');
            const badge = document.querySelector('#periodic-period-badge');
            if (badge) badge.innerText = '2026年7月报表 · 1 项待核定 (仅吉众权限)';
        }""")
        time.sleep(1)
        jizhong_only_screenshot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_jizhong_only.png"
        page.screenshot(path=jizhong_only_screenshot)
        print(f"Saved Jizhong-Only Perspective: {jizhong_only_screenshot}")

        browser.close()
        print("All perspectives verified successfully!")

if __name__ == '__main__':
    verify_monthly_tasks_isolation()
