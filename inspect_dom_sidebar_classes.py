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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # Login
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_timeout(2500)

    # Dump outerHTML of the sidebar
    html = page.locator(".body-sidebar").inner_html()
    with open("sidebar_dump.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Sidebar DOM dumped to sidebar_dump.html, length:", len(html))

    # Evaluate styles of section break and child items
    styles = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('.body-sidebar .sidebar-item-container').forEach(el => {
            const label = el.getAttribute('item-name');
            const isSection = el.classList.contains('section-item');
            const computed = window.getComputedStyle(el.querySelector('.sidebar-item-label') || el);
            results.push({
                label,
                isSection,
                fontWeight: computed.fontWeight,
                fontSize: computed.fontSize,
                color: computed.color,
                className: el.className
            });
        });
        return results;
    }""")
    print("Computed styles:", json.dumps(styles, ensure_ascii=False, indent=2))
    browser.close()
