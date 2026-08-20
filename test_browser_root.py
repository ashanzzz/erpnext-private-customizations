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
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. Login
        print("[1] Logging in...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 2. Open root URL: http://192.168.8.11:6888
        print("[2] Opening root URL: http://192.168.8.11:6888 ...")
        await page.goto(f"{SITE_URL}/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        curr_url = page.url
        print(f"[2] Current browser URL: {curr_url}")

        shot1 = os.path.join(OUTPUT_DIR, "acceptance_root_url_6888.png")
        await page.screenshot(path=shot1)
        print(f"[2] Screenshot saved: {shot1}")

        # Check page text and errors
        page_text = await page.evaluate("() => document.body.innerText")
        print("\n=== Page text summary (first 400 chars) ===")
        print(page_text[:400])

        if "not found" in page_text.lower():
            print("\n[ALERT] 'Not found' detected on page!")
        else:
            print("\n[SUCCESS] Page loaded cleanly without 404!")

        await browser.close()

asyncio.run(run())
