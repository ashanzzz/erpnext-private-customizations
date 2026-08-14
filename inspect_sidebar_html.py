import os
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
SITE_URL = 'http://192.168.8.11:6888'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        page.wait_for_timeout(4000)
        page.goto(f"{SITE_URL}/app/home")
        page.wait_for_timeout(3000)
        
        sidebar_html = page.evaluate("""
            () => {
                const sidebar = document.querySelector('.layout-side-section') || document.querySelector('aside') || document.querySelector('.desk-sidebar');
                return sidebar ? sidebar.outerHTML : 'NO SIDEBAR FOUND';
            }
        """)
        print("SIDEBAR HTML LENGTH:", len(sidebar_html))
        print("SIDEBAR HTML SNIPPET:\n", sidebar_html[:2000])
        browser.close()

if __name__ == "__main__":
    main()
