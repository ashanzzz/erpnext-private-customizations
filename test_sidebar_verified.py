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
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', '')

OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Login
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # Go to http://192.168.8.11:6888/
        await page.goto(f"{SITE_URL}/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        # Trigger sidebar setup for current workspace
        await page.evaluate("""() => {
            if (frappe.workspace && frappe.app && frappe.app.sidebar) {
                frappe.app.sidebar.set_workspace_sidebar(frappe.workspace.current_page_name || 'My Business');
            }
        }""")
        await asyncio.sleep(2)

        shot1 = os.path.join(OUTPUT_DIR, "live_root_landing_sidebar_verified.png")
        await page.screenshot(path=shot1)
        print(f"Screenshot saved: {shot1}")

        # Check items
        items = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.map(e => e.textContent.trim().substring(0, 30))")
        print(f"Total sidebar items found: {len(items)}")
        for i in items[:15]:
            print("  -", i)

        await browser.close()

asyncio.run(run())
