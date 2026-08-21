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

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        print("[1] 登录系统...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 1. 列表页 List View
        print("[2] 访问 Reimbursement Request 列表页...")
        await page.goto(f"{SITE_URL}/desk/reimbursement-request", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        shot_list = os.path.join(OUTPUT_DIR, "reimbursement_list_current.png")
        await page.screenshot(path=shot_list)
        print(f"  列表页截图保存: {shot_list}")

        # 2. 表单页 Form View (新建单据)
        print("[3] 访问 Reimbursement Request 新建表单页...")
        await page.goto(f"{SITE_URL}/desk/reimbursement-request/new-reimbursement-request-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)
        shot_form = os.path.join(OUTPUT_DIR, "reimbursement_form_current.png")
        await page.screenshot(path=shot_form)
        print(f"  表单页截图保存: {shot_form}")

        # 提取表单主要字段结构和 Sections
        form_structure = await page.evaluate("""() => {
            const sections = Array.from(document.querySelectorAll('.form-section')).map(sec => {
                const head = sec.querySelector('.section-head')?.textContent.trim() || '未命名 Section';
                const fields = Array.from(sec.querySelectorAll('.frappe-control')).map(fc => {
                    const label = fc.querySelector('.control-label')?.textContent.trim() || '';
                    const dfName = fc.getAttribute('data-fieldname') || '';
                    const ftype = fc.getAttribute('data-fieldtype') || '';
                    return { label, dfName, ftype };
                }).filter(f => f.label || f.dfName);
                return { head, fields };
            });
            return sections;
        }""")

        import pprint
        print("\n表单字段布局结构:")
        for idx, sec in enumerate(form_structure, 1):
            print(f"\n--- Section {idx}: {sec['head']} ---")
            for f in sec['fields']:
                print(f"  [{f['ftype']}] {f['label']} ({f['dfName']})")

        await browser.close()

asyncio.run(inspect())
