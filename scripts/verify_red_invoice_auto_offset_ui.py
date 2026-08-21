import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1520, "height": 950})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    print("Navigating to tax-invoice-center...")
    page.goto(f"{SITE_URL}/desk/tax-invoice-center")
    page.wait_for_selector(".tax-inv-wrapper", state="visible", timeout=15000)
    time.sleep(3)

    # 截图 1: 全局 KPI 概览 (展示【已红冲对冲 (无需录入)】卡片与统计数值)
    shot_overview = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_offset_kpi_overview.png"
    page.screenshot(path=shot_overview)
    print("Saved Overview Shot:", shot_overview)

    # 点击【已红冲对冲 (无需录入)】KPI 卡片进行一键筛选
    print("Clicking 已红冲对冲 KPI Card...")
    page.click('.tax-kpi-card.card-offset')
    time.sleep(2)

    # 截图 2: 已对冲发票专项列表 (展示【🔄 已对冲】状态徽章与【🔄 冲销 [发票号]】双向溯源链)
    shot_offset_list = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_offset_items_list.png"
    page.screenshot(path=shot_offset_list)
    print("Saved Offset Items Shot:", shot_offset_list)

    # 截图 3: 滚动至表格右侧（展示 ERP 采购发票列中的【🔄 冲销 26122000000088880001】溯源关联）
    page.evaluate("document.querySelector('.tax-table-container').scrollLeft = 800")
    time.sleep(1)
    shot_right = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_offset_right_columns.png"
    page.screenshot(path=shot_right)
    print("Saved Offset Right Columns Shot:", shot_right)

    browser.close()

print("\n[ALL RED INVOICE AUTO OFFSET UI SCREENSHOTS CAPTURED SUCCESSFULLY!]")
