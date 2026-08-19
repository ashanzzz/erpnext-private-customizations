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
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def verify_periodic_tasks_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1050})
        page = context.new_page()

        print("1. Logging into ERPNext...")
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(3)

        print("2. Navigating to Home / My Business...")
        page.goto(f"{SITE_URL}/desk/my-business")
        time.sleep(4)
        page.wait_for_selector("#periodic-tasks-container", timeout=10000)
        time.sleep(2)

        # 截图主页（8月核定状态）
        img1 = os.path.join(ARTIFACT_DIR, "live_acceptance_periodic_tasks_august.png")
        page.screenshot(path=img1)
        print(f"Saved: {img1}")

        # 3. 提取定期任务卡片状态
        tasks_info = page.evaluate("""() => {
            const badge = document.querySelector('#periodic-period-badge') ? document.querySelector('#periodic-period-badge').innerText : '';
            const jz_card = document.querySelector('#company-card-jizhong');
            const qf_card = document.querySelector('#company-card-qifu');

            const jz_items = jz_card ? Array.from(jz_card.querySelectorAll('.periodic-item-row')).map(row => ({
                title: row.querySelector('.periodic-item-title') ? row.querySelector('.periodic-item-title').innerText : '',
                summary: row.querySelector('.periodic-item-summary') ? row.querySelector('.periodic-item-summary').innerText : '',
                badge: row.querySelector('.periodic-item-badge-link') ? row.querySelector('.periodic-item-badge-link').innerText : ''
            })) : [];

            const qf_items = qf_card ? Array.from(qf_card.querySelectorAll('.periodic-item-row')).map(row => ({
                title: row.querySelector('.periodic-item-title') ? row.querySelector('.periodic-item-title').innerText : '',
                summary: row.querySelector('.periodic-item-summary') ? row.querySelector('.periodic-item-summary').innerText : '',
                badge: row.querySelector('.periodic-item-badge-link') ? row.querySelector('.periodic-item-badge-link').innerText : ''
            })) : [];

            return {
                badge: badge,
                jizhong: jz_items,
                qifu: qf_items
            };
        }""")
        print("Aug Periodic Tasks Info:", tasks_info)

        # 4. 切换下拉选择 7月 报表核定
        print("3. Switching period select to July...")
        page.select_option("#select-periodic-period", index=1)
        time.sleep(3)

        img2 = os.path.join(ARTIFACT_DIR, "live_acceptance_periodic_tasks_july.png")
        page.screenshot(path=img2)
        print(f"Saved: {img2}")

        july_info = page.evaluate("""() => {
            const badge = document.querySelector('#periodic-period-badge') ? document.querySelector('#periodic-period-badge').innerText : '';
            const jz_card = document.querySelector('#company-card-jizhong');
            const qf_card = document.querySelector('#company-card-qifu');

            const jz_items = jz_card ? Array.from(jz_card.querySelectorAll('.periodic-item-row')).map(row => ({
                title: row.querySelector('.periodic-item-title') ? row.querySelector('.periodic-item-title').innerText : '',
                summary: row.querySelector('.periodic-item-summary') ? row.querySelector('.periodic-item-summary').innerText : '',
                badge: row.querySelector('.periodic-item-badge-link') ? row.querySelector('.periodic-item-badge-link').innerText : ''
            })) : [];

            const qf_items = qf_card ? Array.from(qf_card.querySelectorAll('.periodic-item-row')).map(row => ({
                title: row.querySelector('.periodic-item-title') ? row.querySelector('.periodic-item-title').innerText : '',
                summary: row.querySelector('.periodic-item-summary') ? row.querySelector('.periodic-item-summary').innerText : '',
                badge: row.querySelector('.periodic-item-badge-link') ? row.querySelector('.periodic-item-badge-link').innerText : ''
            })) : [];

            return {
                badge: badge,
                jizhong: jz_items,
                qifu: qf_items
            };
        }""")
        print("July Periodic Tasks Info:", july_info)

        browser.close()
        print("Periodic tasks verification completed!")

if __name__ == "__main__":
    verify_periodic_tasks_ui()
