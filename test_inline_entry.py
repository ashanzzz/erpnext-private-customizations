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

        # Capture console error & dialogs
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 1. 访问单一合流流水总账
        await page.goto(f"{SITE_URL}/desk/oil-card-ledger", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 2. 点击【⛽ 录入加油】触发最后一行行内录入
        await page.click("#btn-quick-refuel")
        await asyncio.sleep(1)

        # 选择车辆
        await page.select_option("#inline-refuel-vehicle", value="粤B·8888")
        await page.fill("#inline-refuel-odo", "46250")
        await page.fill("#inline-refuel-liters", "50.00")
        await page.fill("#inline-refuel-amount", "410.00")
        await page.fill("#inline-refuel-remark", "业务巡检快速行内录入")
        await asyncio.sleep(1)

        # 截取行内输入与实时余额预览画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_inline_refuel_editing.png"))

        # 点击【💾 保存】
        await page.click("#btn-inline-save-refuel")
        await asyncio.sleep(4)

        # 截取点击保存后的画面（看是否有弹窗或已刷新）
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_after_refuel_save.png"))

        # 3. 点击【💳 录入充值】
        if await page.locator(".modal.show .btn-modal-close, .modal.show .close").count() > 0:
            await page.click(".modal.show .btn-modal-close, .modal.show .close")
            await asyncio.sleep(1)

        await page.click("#btn-quick-recharge")
        await asyncio.sleep(1)

        await page.fill("#inline-recharge-amount", "2000.00")
        await page.fill("#inline-recharge-remark", "月中企业公户充值")
        await asyncio.sleep(1)

        # 截取充值行内输入画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_inline_recharge_editing.png"))

        # 点击【💾 保存】
        await page.click("#btn-inline-save-recharge")
        await asyncio.sleep(4)

        # 截取最终保存后完整流水大账
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "oil_card_inline_saved_ledger.png"))

        await browser.close()
        print("[OK] Inline test completed and all screenshots saved!")

asyncio.run(run())
