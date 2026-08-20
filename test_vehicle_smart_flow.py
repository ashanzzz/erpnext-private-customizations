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

        # 1. 选中【粤B·8888 专车油卡】
        await page.click(".oil-card-item[data-name='CARD-001']")
        await asyncio.sleep(1)

        # 2. 点击【⛽ 录入加油】
        await page.click("#btn-quick-refuel")
        await asyncio.sleep(1)

        # 3. 在车辆输入框键入 "9527" 并触发智能下拉
        veh_input = page.locator("#inline-refuel-vehicle-input")
        await veh_input.fill("9527")
        await asyncio.sleep(1)

        # 截取模糊搜索下拉弹层画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_autocomplete_popup.png"))

        # 4. 在车牌输入框按回车键，触发自动选定【津AF9527】与柴油0#联动
        await veh_input.press("Enter")
        await asyncio.sleep(1)

        # 截取自动回车选定后的行内录入状态
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_fuzzy_selected_refuel.png"))

        # 5. 测试【+ 快速新建车辆档案】单页弹窗与动力红字警示规则
        await page.click("#inline-refuel-vehicle-input")
        await asyncio.sleep(1)
        await page.click("#btn-quick-add-vehicle-from-dropdown")
        await asyncio.sleep(1)

        # 故意选择【货车/卡车】但将燃油选为【汽油】，触发红字风险提示
        await page.fill("input[data-fieldname='license_plate']", "津C·88666")
        await page.select_option("select[data-fieldname='vehicle_category']", value="货车 / 卡车")
        await page.select_option("select[data-fieldname='fuel_type']", value="Petrol (汽油)")
        await asyncio.sleep(1)

        # 截取货车选汽油触发动力匹配红色警示的画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_create_fuel_warning.png"))

        # 修正回正确的【Diesel (柴油)】并设置里程
        await page.select_option("select[data-fieldname='fuel_type']", value="Diesel (柴油)")
        await page.fill("input[data-fieldname='last_odometer']", "5200")
        await asyncio.sleep(1)

        # 点击【💾 立即创建车辆】
        await page.click(".modal-dialog .btn-primary")
        await asyncio.sleep(2)

        # 截取新建车辆自动应用到行内录入的画面
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_after_quick_add_applied.png"))

        # 6. 完成这笔加油录入并保存
        await page.fill("#inline-refuel-odo", "5350")
        await page.fill("#inline-refuel-liters", "45")
        await page.fill("#inline-refuel-amount", "320")
        await page.fill("#inline-refuel-remark", "新车首单加油测试")
        await asyncio.sleep(1)

        # 保存行内记录
        await page.click("#btn-inline-save-refuel")
        await asyncio.sleep(3)

        # 截取最终保存后台账流水大屏
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "vehicle_ledger_final_saved.png"))

        await browser.close()
        print("[OK] Smart vehicle flow and fuel rules test completed successfully!")

asyncio.run(run())
