# -*- coding: utf-8 -*-
import os
import asyncio
from playwright.async_api import async_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = "http://192.168.8.11:6888"
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')

OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        info = await page.evaluate("""() => {
            const sb = frappe.workspace?.sidebar;
            return {
                has_sb: !!sb,
                sidebar_title: sb?.sidebar_title,
                workspace_title: sb?.workspace_title,
                workspace_sidebar_items_len: sb?.workspace_sidebar_items?.length || 0,
                boot_keys: Object.keys(frappe.boot?.workspace_sidebar_item || {})
            };
        }""")

        import pprint
        print("frappe.workspace.sidebar details:")
        pprint.pprint(info)

        # Call setup('My Business') on frappe.workspace.sidebar
        res = await page.evaluate("""() => {
            frappe.workspace.sidebar.setup('My Business');
            return {
                rendered_items: $('.body-sidebar .standard-sidebar-item').length,
                rendered_text: Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item')).map(e => e.textContent.trim().substring(0, 25))
            };
        }""")
        print("\nAfter frappe.workspace.sidebar.setup('My Business'):")
        pprint.pprint(res)

        await asyncio.sleep(2)
        shot = os.path.join(OUTPUT_DIR, "workspace_sidebar_rendered.png")
        await page.screenshot(path=shot)
        print(f"Screenshot saved: {shot}")

        await browser.close()

asyncio.run(run())
