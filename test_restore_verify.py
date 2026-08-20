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

        # 访问 Customize Form
        await page.goto(f"{SITE_URL}/desk/customize-form/Customize%20Form", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "customize_form_restored.png"))

        # 访问 Purchase Invoice
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/ACC-PINV-2026-00001", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "invoice_restored.png"))

        # 点击行编辑
        edit_btn = page.locator('.grid-row .btn-open-row').first
        if await edit_btn.count() == 0:
            edit_btn = page.locator('.grid-row').first
        await edit_btn.click()
        await asyncio.sleep(2)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "row_drawer_restored.png"))

        await browser.close()

asyncio.run(run())
