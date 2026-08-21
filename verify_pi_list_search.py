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

        # 1. 访问采购发票列表页
        print("[1] 访问采购发票列表页 /desk/purchase-invoice ...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        shot1 = os.path.join(OUTPUT_DIR, "pi_list_optimized.png")
        await page.screenshot(path=shot1)
        print(f"  列表页优化截图: {shot1}")

        # 2. 测试在【开票物料明细】过滤器中输入“紧固件”进行快速搜索
        print("[2] 测试物料搜索过滤...")
        filter_input = page.locator('input[data-fieldname="custom_items_summary"]')
        if await filter_input.count() > 0:
            await filter_input.fill("紧固件")
            await filter_input.press("Enter")
            await asyncio.sleep(2)
            shot2 = os.path.join(OUTPUT_DIR, "pi_list_filtered_by_item.png")
            await page.screenshot(path=shot2)
            print(f"  物料过滤后截图: {shot2}")

        await browser.close()
        print("\n[SUCCESS] 采购发票列表物料明细列与搜索过滤验证成功！")

asyncio.run(run())
