# -*- coding: utf-8 -*-
import json
import os

fixtures_dir = "ashan_cn_procurement/ashan_cn_procurement/fixtures"

with open(os.path.join(fixtures_dir, "custom_html_block.html"), "r", encoding="utf-8") as f:
    html = f.read()

with open(os.path.join(fixtures_dir, "custom_html_block.css"), "r", encoding="utf-8") as f:
    css = f.read()

with open(os.path.join(fixtures_dir, "custom_html_block.js"), "r", encoding="utf-8") as f:
    js = f.read()

block_data = {
    "doctype": "Custom HTML Block",
    "name": "业务场景导航",
    "html": html,
    "style": css,
    "script": js,
    "private": 0
}

target_path = os.path.join(fixtures_dir, "custom_html_block.json")
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(block_data, f, ensure_ascii=False, indent=2)

print("[OK] Upgraded custom_html_block.json regenerated successfully from .html, .css, and .js!")
