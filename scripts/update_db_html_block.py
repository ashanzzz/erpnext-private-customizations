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

blocks = frappe.get_all('Custom HTML Block', fields=['name', 'creation', 'modified'])
print('All Custom HTML Blocks in DB:', blocks)

with open('/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'r') as f:
    data = json.load(f)

name = data.get('name', '业务场景导航')
if frappe.db.exists('Custom HTML Block', name):
    doc = frappe.get_doc('Custom HTML Block', name)
    doc.html = data.get('html', '')
    doc.script = data.get('script', '')
    doc.style = data.get('style', '')
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print('Successfully updated Custom HTML Block:', name)
else:
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print('Inserted new Custom HTML Block:', name)
"""

# 写入容器 /tmp/update_block.py
sftp = client.open_sftp()
with sftp.file('/tmp/update_block.py', 'w') as f:
    f.write(script_content)
sftp.close()

# 执行
stdin, stdout, stderr = client.exec_command("docker cp /tmp/update_block.py erpnext16:/tmp/update_block.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/update_block.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = client.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
print("Cache cleared:", stdout.read().decode('utf-8', errors='replace'))

client.close()
print("Done updating Custom HTML Block!")
