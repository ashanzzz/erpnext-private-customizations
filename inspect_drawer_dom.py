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
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        await page.goto(f"{SITE_URL}/desk/purchase-invoice/ACC-PINV-2026-00001", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        edit_btn = page.locator('.grid-row .btn-open-row').first
        if await edit_btn.count() == 0:
            edit_btn = page.locator('.grid-row').first
        await edit_btn.click()
        await asyncio.sleep(2)

        # 检查每个 section 中的 columns 和 fields
        layout_info = await page.evaluate("""() => {
            const sections = [];
            $('.grid-row-open .form-section').each(function(s_idx) {
                const s_label = $(this).find('.section-head').text().trim();
                const cols = [];
                $(this).find('.form-column').each(function(c_idx) {
                    const fields = [];
                    $(this).find('.frappe-control').each(function() {
                        const fn = $(this).attr('data-fieldname');
                        const lbl = $(this).find('label').text().trim();
                        const is_hidden = $(this).is(':hidden');
                        fields.push({ fn, lbl, is_hidden });
                    });
                    cols.push({ col_idx: c_idx, fields });
                });
                sections.push({ s_idx, s_label, cols });
            });
            return sections;
        }""")

        import pprint
        print("GRID DRAWER SECTIONS & COLUMNS:")
        pprint.pprint(layout_info)

        await browser.close()

asyncio.run(run())
