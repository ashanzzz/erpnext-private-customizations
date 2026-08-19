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

wss = frappe.get_all('Workspace', fields=['name', 'title', 'label', 'for_user', 'public'])
for ws in wss:
    doc = frappe.get_doc('Workspace', ws.name)
    has_html = any(getattr(c, 'type', '') == 'custom_html_block' or getattr(c, 'custom_html_block_name', '') for c in (doc.custom_blocks or []))
    has_content_html = 'custom_html_block' in (doc.content or '')
    if has_html or has_content_html or '业务' in doc.title or 'My Business' in doc.name:
        print(f'Workspace: {doc.name}, title={doc.title}, content={doc.content}')
"""

sftp = client.open_sftp()
with sftp.file('/tmp/inspect_ws.py', 'w') as f:
    f.write(script_content)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/inspect_ws.py erpnext16:/tmp/inspect_ws.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/inspect_ws.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
client.close()
