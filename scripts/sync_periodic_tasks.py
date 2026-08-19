# -*- coding: utf-8 -*-
import os
import json
import subprocess

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

CONTAINER = os.getenv('DOCKER_CONTAINER_NAME', 'erpnext16')
SITE = os.getenv('ERPNEXT_SITE', 'site1.local')
FIXTURE_PATH = "ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json"

def sync_and_apply_custom_html_block():
    print("1. Reading fixture json...")
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        block_data = json.load(f)

    # 直传到容器
    print("2. Syncing app files to container...")
    subprocess.run(["python", "scripts/sync_app.py"], check=True)

    # 在容器中执行 bench execute 或 python 脚本更新 Custom HTML Block
    print("3. Updating Custom HTML Block in ERPNext database...")
    update_script = f"""
import frappe
import json

with open('/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r') as f:
    data = json.load(f)

name = data.get('name', '业务场景导航')
if frappe.db.exists('Custom HTML Block', name):
    doc = frappe.get_doc('Custom HTML Block', name)
    doc.html = data.get('html', '')
    doc.script = data.get('script', '')
    doc.style = data.get('style', '')
    doc.save(ignore_permissions=True)
    print(f'Updated existing Custom HTML Block: {{name}}')
else:
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    print(f'Inserted new Custom HTML Block: {{name}}')

frappe.db.commit()
"""

    cmd = [
        "docker", "exec", "-u", "frappe", "-w", "/home/frappe/frappe-bench/sites",
        CONTAINER,
        "../env/bin/python", "-c",
        f"import frappe; frappe.init(site='{SITE}'); frappe.connect(); {update_script}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    # bench clear-cache
    print("4. Clearing cache...")
    subprocess.run([
        "docker", "exec", "-u", "frappe", "-w", "/home/frappe/frappe-bench",
        CONTAINER, "bench", "--site", SITE, "clear-cache"
    ], check=True)

    print("5. Custom HTML Block sync and update completed!")

if __name__ == "__main__":
    sync_and_apply_custom_html_block()
