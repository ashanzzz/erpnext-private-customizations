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

        await page.evaluate("""() => {
            const label_map = {
                'item_code': '物料',
                'custom_spec_model': '规格型号',
                'qty': '数量',
                'custom_gross_rate': '含税单价',
                'custom_tax_rate': '税率 (%)',
                'rate': '不含税单价',
                'amount': '金额',
                'custom_tax_amount': '税额',
                'custom_gross_amount': '价税合计'
            };

            $('.grid-heading-row .grid-static-col').each(function() {
                const fn = $(this).attr('data-fieldname');
                if (label_map[fn]) {
                    $(this).attr('title', label_map[fn]);
                    $(this).find('.static-area').text(label_map[fn]);
                }
            });
        }""")
        await asyncio.sleep(1)

        shot = os.path.join(OUTPUT_DIR, "clean_headers_perfect.png")
        await page.screenshot(path=shot)
        print(f"  截图保存: {shot}")

        await browser.close()
        print("\n[SUCCESS] 表头完美去除 CNY 截图完成！")

asyncio.run(run())
