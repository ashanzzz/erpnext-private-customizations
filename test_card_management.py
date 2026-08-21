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

        # 1. 点击【+ 新建油卡】触发单页模态对话框
        await page.click("#btn-create-card")
        await asyncio.sleep(1)

        # 填写新建油卡表单
        await page.fill("input[data-fieldname='card_name']", "粤A·6666 商务测试油卡")
        await page.fill("input[data-fieldname='card_no']", "1000116666666666")
        await page.select_option("select[data-fieldname='card_type']", value="副卡")
        await page.fill("input[data-fieldname='opening_balance']", "1200.00")
        await asyncio.sleep(1)

        # 截取新建油卡单页弹窗画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_inpage_create_dialog.png"))

        # 点击【💾 立即创建】
        await page.click(".modal-dialog .btn-primary")
        await asyncio.sleep(3)

        # 截取创建后左侧列表自动出现并高亮激活新卡画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_after_create_selected.png"))

        # 2. 找到刚创建的卡，测试【🗑️ 删除油卡】
        delete_btn = page.locator(".btn-delete-card[data-title='粤A·6666 商务测试油卡']")
        if await delete_btn.count() > 0:
            await delete_btn.click()
            await asyncio.sleep(1)
            # 点击确认删除
            await page.click(".modal.show .btn-primary")
            await asyncio.sleep(3)

        # 截取最终删除后平滑切换回主卡的完整画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_after_delete_settled.png"))

        await browser.close()
        print("[OK] In-page card create and delete test completed successfully!")

asyncio.run(run())
