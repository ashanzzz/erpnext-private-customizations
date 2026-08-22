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
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        dom_info = await page.evaluate("""() => {
            const due_date_el = document.querySelector('[data-fieldname="due_date"]');
            const tabs_el = document.querySelector('.form-tabs, .nav-tabs, .form-tabs-list, .form-header-tabs');
            const all_tabs = Array.from(document.querySelectorAll('.form-tab, .nav-item, [role="tab"]')).map(el => ({
                text: el.textContent.trim(),
                className: el.className,
                html: el.outerHTML
            }));
            
            return {
                due_date_found: !!due_date_el,
                due_date_parent: due_date_el?.parentElement?.className,
                due_date_style: due_date_el ? window.getComputedStyle(due_date_el).display : 'none',
                tabs_found: !!tabs_el,
                tabs_class: tabs_el?.className,
                all_tabs: all_tabs
            };
        }""")
        print("DOM Info:")
        import pprint
        pprint.pprint(dom_info)

        await browser.close()

asyncio.run(run())
