# -*- coding: utf-8 -*-
import os
import sys
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
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # 1. Login
        print("[1] Logging in...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 2. Test opening root URL directly: http://192.168.8.11:6888/
        print("[2] Visiting root URL: http://192.168.8.11:6888/ ...")
        await page.goto(f"{SITE_URL}/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        curr_url = page.url
        print(f"[2] Current browser URL: {curr_url}")

        shot1 = os.path.join(OUTPUT_DIR, "acceptance_root_after_fix.png")
        await page.screenshot(path=shot1)
        print(f"[2] Screenshot saved: {shot1}")

        # Check for any modal or not-found text
        has_dialog = await page.locator(".modal.show").count()
        print(f"[2] Visible modal dialogs: {has_dialog}")
        if has_dialog > 0:
            modal_text = await page.locator(".modal.show").inner_text()
            print(f"[ALERT] Modal text: {modal_text}")

        # Check page text
        page_text = await page.evaluate("() => document.body.innerText")
        if "not found" in page_text.lower():
            print("[FAIL] 'Not found' detected on page!")
        else:
            print("[PASS] Page loaded cleanly without 'Not found'!")

        # 3. Test opening /desk
        print("[3] Visiting /desk ...")
        await page.goto(f"{SITE_URL}/desk", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)
        print(f"[3] URL on /desk: {page.url}")
        shot2 = os.path.join(OUTPUT_DIR, "acceptance_desk_after_fix.png")
        await page.screenshot(path=shot2)

        has_dialog_desk = await page.locator(".modal.show").count()
        print(f"[3] Visible modal dialogs on /desk: {has_dialog_desk}")

        await browser.close()
        print("[DONE] Browser verification complete!")

asyncio.run(run())
