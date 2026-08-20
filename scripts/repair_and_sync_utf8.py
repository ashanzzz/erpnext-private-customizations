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

# 读取本地 custom_html_block.json
with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r', encoding='utf-8') as f:
    block_json = json.load(f)

script_content = f"""# -*- coding: utf-8 -*-
import frappe, json

frappe.init(site='site1.local')
frappe.connect()

block_name = "业务场景导航"

# 1. 确保 Custom HTML Block 记录名称与内容绝对正确
if frappe.db.exists('Custom HTML Block', block_name):
    b = frappe.get_doc('Custom HTML Block', block_name)
else:
    # 查找可能存在的旧记录并删除
    for old_b in frappe.get_all('Custom HTML Block'):
        frappe.delete_doc('Custom HTML Block', old_b.name, force=True)
    b = frappe.new_doc('Custom HTML Block')
    b.name = block_name

b.html = {json.dumps(block_json['html'], ensure_ascii=False)}
b.style = {json.dumps(block_json['style'], ensure_ascii=False)}
b.script = {json.dumps(block_json['script'], ensure_ascii=False)}
b.private = 0
b.save(ignore_permissions=True)
print("Successfully synced Custom HTML Block '业务场景导航'!")

# 2. 确保 Home 和 My Business Workspace 挂载正确的 Custom Block
clean_content = [
    {{
        "id": "hdr_main_my_business",
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
        doc = frappe.get_doc('Workspace', ws_name)
        doc.title = "我的业务 (总控主页)"
        doc.content = json.dumps(clean_content, ensure_ascii=False)
        doc.custom_blocks = []
        doc.append('custom_blocks', {{
            'custom_block_name': block_name,
            'label': block_name
        }})
        doc.shortcuts = []
        doc.links = []
        doc.save(ignore_permissions=True)
        print(f"Updated Workspace '{{ws_name}}' with pure clean layout!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/repair_and_sync_utf8.py', 'w') as f:
    f.write(script_content.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/repair_and_sync_utf8.py erpnext16:/tmp/repair_and_sync_utf8.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/repair_and_sync_utf8.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
print("Cache cleared:", stdout.read().decode('utf-8', errors='replace'))

client.close()
print("Done repairing & syncing utf-8 block!")
