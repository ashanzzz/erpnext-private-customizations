# -*- coding: utf-8 -*-
import os
import sys
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

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[PAGE_ERROR] {err}"))

        # 1. Login
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 2. Go to /desk/my-business
        console_logs.clear()
        print("Navigating to /desk/my-business ...")
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        # Inspect frappe.boot.workspaces, frappe.workspaces, frappe.get_route()
        eval_result = await page.evaluate("""() => {
            return {
                route: frappe.get_route(),
                route_str: frappe.get_route_str(),
                allowed_workspaces: frappe.boot.allowed_workspaces,
                workspaces_keys: Object.keys(frappe.workspaces || {}),
                boot_workspaces_pages: (frappe.boot.workspaces?.pages || []).map(p => ({name: p.name, title: p.title, public: p.public})),
                has_pageview: !!frappe.views.pageview,
                pages: Object.keys(frappe.pages || {})
            };
        }""")

        print("Browser State Eval:")
        import pprint
        pprint.pprint(eval_result)

        print("\nConsole Logs:")
        for log in console_logs[-30:]:
            print("  ", log)

        await browser.close()

asyncio.run(run())
