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
        context = await browser.new_context(viewport={"width": 1440, "height": 1080})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 访问 Home
        await page.goto(f"{SITE_URL}/desk", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 查找包含 shadowRoot 的元素
        res = await page.evaluate("""() => {
            let found = null;
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot && el.shadowRoot.querySelector('.biz-nav-container')) {
                    found = el;
                }
            });
            if (found) {
                const ROOT = found.shadowRoot;
                const canRead = (dt) => ["Purchase Receipt"].includes(dt);
                const canCreate = (dt) => ["Purchase Receipt"].includes(dt);

                const cards = ROOT.querySelectorAll('.step-card[data-doctype]');
                cards.forEach((card) => {
                    const dt = card.getAttribute('data-doctype');
                    if (!canRead(dt)) {
                        card.classList.add('step-hidden');
                        const arrow = card.nextElementSibling;
                        if (arrow && arrow.classList.contains('flow-arrow')) arrow.classList.add('step-hidden');
                    } else {
                        card.classList.remove('step-hidden');
                        const createBtn = card.querySelector('.btn-create');
                        if (createBtn) {
                            if (!canCreate(dt)) createBtn.classList.add('btn-hidden-perm');
                            else createBtn.classList.remove('btn-hidden-perm');
                        }
                    }
                });

                const sceneBlocks = ROOT.querySelectorAll('.biz-scene-block');
                sceneBlocks.forEach((block) => {
                    const c = block.querySelectorAll('.step-card');
                    const visibleCards = Array.from(c).filter(x => !x.classList.contains('step-hidden'));
                    if (visibleCards.length === 0) block.classList.add('scene-hidden');
                    else block.classList.remove('scene-hidden');
                });
                return "found and updated!";
            }
            return "not found!";
        }""")

        print("Evaluate result:", res)
        await asyncio.sleep(1)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, "simulated_warehouse_user_view.png"), full_page=True)

        await browser.close()

asyncio.run(run())
