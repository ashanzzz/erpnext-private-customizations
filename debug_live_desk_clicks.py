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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Browser Error] {err}"))

        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)

        print("\n--- Current Page URL:", page.url)
        print("Checking presence of #ashan-cn-sidebar-container:", page.is_visible("#ashan-cn-sidebar-container"))

        # Inspect all visible sidebar links
        links = page.eval_on_selector_all(".body-sidebar a, .desk-sidebar a", """
            els => els.map(e => ({ text: e.innerText.trim(), href: e.getAttribute('href'), outer: e.outerHTML.slice(0, 100) }))
        """)
        print("\n=== VISIBLE SIDEBAR LINKS ===")
        for l in links:
            safe_text = l['text'].encode('ascii', 'ignore').decode('ascii')
            print(f"- Text: {safe_text} | Href: {repr(l['href'])}")

        # Now click on 'Procurement Management'
        print("\nClicking native 'Procurement Management' link...")
        loc = page.locator(".body-sidebar .sidebar-item-container a[href*='procurement-management']").first
        if loc.is_visible():
            loc.click()
            page.wait_for_timeout(2000)
            print("URL after click:", page.url)
        else:
            print("Locator for procurement-management link was not visible!")

        browser.close()

if __name__ == "__main__":
    main()
