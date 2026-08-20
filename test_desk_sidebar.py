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
            return {
                frappe_desk_sidebar: !!frappe.desk?.sidebar,
                frappe_desk_sidebar_items: frappe.desk?.sidebar?.workspace_sidebar_items?.length || 0,
                frappe_desk_sidebar_title: frappe.desk?.sidebar?.sidebar_title,
                all_frappe_props: Object.keys(frappe).filter(k => k.toLowerCase().includes('side') || k.toLowerCase().includes('desk') || k.toLowerCase().includes('app'))
            };
        }""")

        print("Sidebar details on frappe.desk:", info)

        # Call setup on frappe.desk.sidebar
        res = await page.evaluate("""() => {
            if (frappe.desk && frappe.desk.sidebar) {
                frappe.desk.sidebar.setup('My Business');
                return {
                    rendered: $('.body-sidebar .standard-sidebar-item').length
                };
            }
            return null;
        }""")
        print("After frappe.desk.sidebar.setup('My Business'):", res)

        items = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.map(e => e.textContent.trim().substring(0, 30))")
        print(f"DOM items ({len(items)}):", items[:10])

        await browser.close()

asyncio.run(run())
