import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r', encoding='utf-8') as f:
    block_json = json.load(f)

script = f"""# -*- coding: utf-8 -*-
import frappe, json

frappe.init(site='site1.local')
frappe.connect()

block_name = "业务场景导航"

# 1. 插入/更新 Custom HTML Block
if not frappe.db.exists('Custom HTML Block', block_name):
    b = frappe.new_doc('Custom HTML Block')
    b.name = block_name
else:
    b = frappe.get_doc('Custom HTML Block', block_name)

b.html = {json.dumps(block_json['html'], ensure_ascii=False)}
b.style = {json.dumps(block_json['style'], ensure_ascii=False)}
b.script = {json.dumps(block_json['script'], ensure_ascii=False)}
b.private = 0
b.save(ignore_permissions=True)
print("Updated Custom HTML Block!")

# 2. 挂载到 Workspace
ws_content = [
    {{
        "id": "hdr_main",
        "type": "header",
        "data": {{
            "text": "<span class=\\"h3\\"><b>我的业务 (总控主页)</b></span>",
            "col": 12
        }}
    }},
    {{
        "id": "chb_biz_scenes_nav",
        "type": "custom_block",
        "data": {{
            "custom_block_name": block_name,
            "col": 12
        }}
    }}
]

for ws_name in ['Home', 'My Business']:
    if frappe.db.exists('Workspace', ws_name):
        w = frappe.get_doc('Workspace', ws_name)
        w.content = json.dumps(ws_content, ensure_ascii=False)
        w.custom_blocks = []
        w.append('custom_blocks', {{
            'custom_block_name': block_name,
            'label': block_name
        }})
        w.shortcuts = []
        w.links = []
        w.save(ignore_permissions=True)
        print(f"Mounted onto Workspace {{ws_name}}!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/inject_block.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/inject_block.py erpnext16:/tmp/inject_block.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/inject_block.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
print("Cache cleared:", stdout.read().decode('utf-8', errors='replace'))

client.close()
