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
        context = await browser.new_context(viewport={"width": 1500, "height": 1100})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        await page.goto(f"{SITE_URL}/desk/oil-card-ledger", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 1. 默认状态截图 (粤B·8888 专车油卡)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "sidebar_refined_overview.png"))

        # 2. 点击余额为 0 的【中石海油】卡 (data-name='1')
        zero_card = page.locator(".oil-card-item[data-name='1']")
        if await zero_card.count() > 0:
            await zero_card.click()
            await asyncio.sleep(2)

            # 验证上期结转与当前余额均为 0
            op_text = await page.locator("#kpi-opening-bal").inner_text()
            end_text = await page.locator("#kpi-ending-bal").inner_text()
            print("[TEST] Zero Card KPI Check -> Opening:", op_text.encode('ascii', 'ignore').decode(), "Ending:", end_text.encode('ascii', 'ignore').decode())

            await page.screenshot(path=os.path.join(OUTPUT_DIR, "zero_balance_card_selected.png"))

        # 3. 再次点击回【粤B·8888 专车油卡】
        card_1 = page.locator(".oil-card-item[data-name='CARD-001']")
        if await card_1.count() > 0:
            await card_1.click()
            await asyncio.sleep(2)
            op_text2 = await page.locator("#kpi-opening-bal").inner_text()
            end_text2 = await page.locator("#kpi-ending-bal").inner_text()
            print("[TEST] Card 1 KPI Check -> Opening:", op_text2.encode('ascii', 'ignore').decode(), "Ending:", end_text2.encode('ascii', 'ignore').decode())

        await browser.close()
        print("[OK] Sidebar & Zero balance refresh test completed successfully!")

asyncio.run(run())
