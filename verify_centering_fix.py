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
        # Test 1920x1080
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 1. 访问已存单据 ACC-PINV-2026-00001
        print("访问 ACC-PINV-2026-00001 ...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/ACC-PINV-2026-00001", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        shot1 = os.path.join(OUTPUT_DIR, "invoice_1920_centered_verified.png")
        await page.screenshot(path=shot1)
        print(f"1920宽屏居中截图: {shot1}")

        # 2. 访问新建单据页面
        print("访问新建单据页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        shot2 = os.path.join(OUTPUT_DIR, "new_invoice_1920_centered.png")
        await page.screenshot(path=shot2)
        print(f"1920新建单据居中截图: {shot2}")

        await browser.close()

asyncio.run(run())
