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

script_content = """import frappe, json
frappe.init(site='site1.local')
frappe.connect()

# 纯粹现代化的一体化工作区布局（仅保留顶层标题与总控中枢 Block）
clean_content = [
    {
        "id": "hdr_main_my_business",
        "type": "header",
        "data": {
            "text": "<span class=\\\"h3\\\"><b>我的业务 (总控主页)</b></span>",
            "col": 12
        }
    },
    {
        "id": "chb_biz_scenes_nav",
        "type": "custom_block",
        "data": {
            "custom_block_name": "业务场景导航",
            "col": 12
        }
    }
]

for ws_name in ['Home', 'My Business']:
    if frappe.db.exists('Workspace', ws_name):
        doc = frappe.get_doc('Workspace', ws_name)
        doc.content = json.dumps(clean_content, ensure_ascii=False)
        doc.custom_blocks = []
        doc.append('custom_blocks', {
            'custom_block_name': '业务场景导航',
            'label': '业务场景导航'
        })
        doc.shortcuts = []
        doc.links = []
        doc.save(ignore_permissions=True)
        print(f"Cleaned and streamlined {ws_name} workspace layout!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/clean_ws.py', 'w') as f:
    f.write(script_content)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/clean_ws.py erpnext16:/tmp/clean_ws.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/clean_ws.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
print("Cache cleared:", stdout.read().decode('utf-8', errors='replace'))

client.close()
print("Done cleaning workspace!")
