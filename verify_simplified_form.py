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
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        print("[1] 访问新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        shot1 = os.path.join(OUTPUT_DIR, "simplified_invoice_form.png")
        await page.screenshot(path=shot1)
        print(f"  截图保存: {shot1}")

        # 检查界面上可见的 label 和字段
        visible_info = await page.evaluate("""() => {
            const visible_fields = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .frappe-control:not(.hide-control) .control-label'))
                .map(el => el.textContent.trim())
                .filter(Boolean);
            const visible_sections = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .section-head:not(.hide-control)'))
                .map(el => el.textContent.trim())
                .filter(Boolean);
            return {
                visible_fields: visible_fields,
                visible_sections: visible_sections
            };
        }""")
        print("\n界面当前可见字段:", visible_info['visible_fields'])
        print("界面当前可见分区:", visible_info['visible_sections'])

        await browser.close()
        print("\n[SUCCESS] 极简中文化采购发票页面验收完成！")

asyncio.run(run())
