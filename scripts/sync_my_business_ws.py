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

home_ws = frappe.get_doc('Workspace', 'Home')
home_content = json.loads(home_ws.content) if home_ws.content else []

if frappe.db.exists('Workspace', 'My Business'):
    mb_ws = frappe.get_doc('Workspace', 'My Business')
    mb_ws.content = json.dumps(home_content, ensure_ascii=False)
    mb_ws.custom_blocks = []
    for b in (home_ws.custom_blocks or []):
        mb_ws.append('custom_blocks', {
            'custom_block_name': b.custom_block_name,
            'label': b.label
        })
    mb_ws.save(ignore_permissions=True)
    print("Updated My Business workspace custom_blocks & content!")

frappe.db.commit()
"""

sftp = client.open_sftp()
with sftp.file('/tmp/sync_mb_ws.py', 'w') as f:
    f.write(script_content)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/sync_mb_ws.py erpnext16:/tmp/sync_mb_ws.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/sync_mb_ws.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
print("Cache cleared:", stdout.read().decode('utf-8', errors='replace'))

client.close()
print("Done syncing My Business workspace!")
