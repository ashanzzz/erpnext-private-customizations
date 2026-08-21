# -*- coding: utf-8 -*-
import os
import json
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
        await asyncio.sleep(4)

        info = await page.evaluate("""() => {
            const items = frappe.boot.workspace_sidebar_item || {};
            const result = {};
            for (let k of Object.keys(items)) {
                if (k.includes('业务') || k.includes('ashan') || items[k]?.label?.includes('业务') || items[k]?.items?.length > 5) {
                    result[k] = {
                        label: items[k].label,
                        title: items[k].title,
                        item_count: items[k].items?.length || 0,
                        first_items: (items[k].items || []).slice(0, 5).map(i => i.title || i.label)
                    };
                }
            }
            return result;
        }""")

        print("Sidebar item candidates:")
        import pprint
        for k, v in info.items():
            print(f"Key: {repr(k)} -> count: {v['item_count']}, items: {v['first_items']}")

        await browser.close()

asyncio.run(run())
