# -*- coding: utf-8 -*-
import os
import time
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

        # 1. 选中【粤B·8888 专车油卡】
        await page.click(".oil-card-item[data-name='CARD-001']")
        await asyncio.sleep(1)

        # 2. 点击【⛽ 录入加油】
        await page.click("#btn-quick-refuel")
        await asyncio.sleep(1)

        # 3. 聚焦车牌输入框，验证【向上弹出 Dropup】
        veh_input = page.locator("#inline-refuel-vehicle-input")
        await veh_input.click()
        await asyncio.sleep(1)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_dropup_visible.png"))

        # 4. 点击油号输入框，验证【油号向上弹出 Dropup】与纯中文油品列表
        grade_input = page.locator("#inline-refuel-grade-input")
        await grade_input.click()
        await asyncio.sleep(1)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "grade_dropup_visible.png"))

        # 5. 打开【+ 快速新建车辆档案】弹窗，验证纯中文选项与独立纯电/混动
        await page.click("#inline-refuel-vehicle-input")
        await asyncio.sleep(1)
        await page.click("#btn-quick-add-vehicle-from-dropdown")
        await asyncio.sleep(1)

        rand_suffix = str(int(time.time()))[-4:]
        new_plate = f"津C·{rand_suffix}"

        # 选货车 + 纯电动，测试纯中文风险提示
        await page.fill("input[data-fieldname='license_plate']", new_plate)
        await page.select_option("select[data-fieldname='vehicle_category']", value="货车")
        await page.select_option("select[data-fieldname='fuel_type']", value="纯电动")
        await asyncio.sleep(1)

        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_chinese_modal_warning.png"))

        # 修正回【柴油】并保存车辆
        await page.select_option("select[data-fieldname='fuel_type']", value="柴油")
        await page.fill("input[data-fieldname='last_odometer']", "28000")
        await asyncio.sleep(1)
        await page.click(".modal-dialog .btn-primary")
        await asyncio.sleep(2)

        # 6. 行内完成录入并保存
        await page.fill("#inline-refuel-odo", "28350")
        await page.fill("#inline-refuel-liters", "50")
        await page.fill("#inline-refuel-amount", "360")
        await page.fill("#inline-refuel-remark", "纯中文动力测试单")
        await asyncio.sleep(1)
        await page.click("#btn-inline-save-refuel")
        await asyncio.sleep(3)

        await page.screenshot(path=os.path.join(OUTPUT_DIR, "ledger_after_dropup_refuel.png"))

        await browser.close()
        print("[OK] Dropup and Chinese grade combobox test completed successfully!")

asyncio.run(run())
