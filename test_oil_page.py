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
        context = await browser.new_context(viewport={"width": 1440, "height": 1080})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 1. 访问油卡综合台账明细台 (Desk Page)
        await page.goto(f"{SITE_URL}/desk/oil-card-ledger", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_ledger_refuels.png"))

        # 2. 切换到充值流水标签页
        recharge_tab = page.locator('.tab-nav-btn[data-tab="recharge"]')
        if await recharge_tab.count() > 0:
            await recharge_tab.click()
            await asyncio.sleep(1)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_ledger_recharges.png"))

        # 3. 访问首页检查左侧侧边栏
        await page.goto(f"{SITE_URL}/desk", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "desk_sidebar_with_oil_ledger.png"))

        await browser.close()

asyncio.run(run())
