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
        await asyncio.sleep(3)

        await page.goto(f"{SITE_URL}/desk", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Inspect frappe.workspaces keys and allowed workspaces
        info = await page.evaluate("""() => {
            return {
                current_route: frappe.get_route(),
                workspaces_keys: Object.keys(frappe.workspaces || {}),
                all_workspace_names: (frappe.boot.workspaces?.pages || []).map(p => p.name),
                allowed_workspaces: frappe.boot.allowed_workspaces?.map(w => w.name)
            };
        }""")

        print("Current Route:", info['current_route'])
        print("Workspaces Keys in frappe.workspaces:", info['workspaces_keys'])
        print("All workspace names in boot:", info['all_workspace_names'])
        print("Allowed workspaces:", info['allowed_workspaces'])

        await browser.close()

asyncio.run(run())
