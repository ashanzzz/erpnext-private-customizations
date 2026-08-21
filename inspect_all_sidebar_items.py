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
        await asyncio.sleep(3)

        items_info = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item, .body-sidebar .sidebar-child-item .item-anchor')).map(e => {
                return {
                    text: e.textContent.trim(),
                    href: e.getAttribute('href') || e.querySelector('a')?.getAttribute('href') || '',
                    class: e.className
                };
            });
        }""")

        import pprint
        print("ALL 34 SIDEBAR DOM ITEMS:")
        for idx, item in enumerate(items_info, 1):
            print(f"[{idx:02d}] {item['text']} -> {item['href']}")

        await browser.close()

asyncio.run(run())
