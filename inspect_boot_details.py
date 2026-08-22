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
        await asyncio.sleep(4)

        result = await page.evaluate("""() => {
            const allKeys = Object.keys(frappe.boot?.workspace_sidebar_item || {});
            const details = allKeys.map(k => {
                const s = frappe.boot.workspace_sidebar_item[k];
                return {
                    key: k,
                    has_items: !!s?.items,
                    item_len: s?.items?.length || 0,
                    title: s?.title,
                    label: s?.label
                };
            }).filter(d => d.item_len > 0);
            return {
                total_boot_keys: allKeys.length,
                keys_with_items: details
            };
        }""")

        import pprint
        print("BOOT SIDEBAR DETAILS:")
        for d in result['keys_with_items']:
            print(f"Key: {repr(d['key'])} -> len: {d['item_len']}, title: {repr(d['title'])}, label: {repr(d['label'])}")

        await browser.close()

asyncio.run(run())
