import os
import json
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
        page.wait_for_timeout(3000)
        
        print("Extracting sidebar HTML structure...")
        sidebar_items = page.eval_on_selector_all(".body-sidebar *, .sidebar-item *, .standard-sidebar *", """
            nodes => nodes.map(n => ({
                tag: n.tagName,
                text: n.innerText ? n.innerText.trim() : '',
                class: n.className,
                href: n.getAttribute ? n.getAttribute('href') : ''
            })).filter(x => x.text && x.text.length < 50)
        """)
        
        print("Sidebar elements found:")
        for item in sidebar_items[:20]:
            print(item)
            
        browser.close()

if __name__ == "__main__":
    main()
