import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

script = """
import frappe, json
frappe.init(site="site1.local")
frappe.connect()

items = frappe.db.sql('''SELECT parent, label, link_to, link_type, type, idx FROM `tabWorkspace Sidebar Item` WHERE parent IN ('My Business', 'Property and Lease', 'Vehicle Fuel Hub', 'Ashan CN Procurement', 'Home') ORDER BY parent, idx''', as_dict=1)
for it in items:
    print(f"{it['parent']} | {it['type']} | {it['label']} -> {it['link_to']} ({it['link_type']})")
"""

sftp = client.open_sftp()
with sftp.file("/tmp/dump_sidebars.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/dump_sidebars.py erpnext16:/tmp/dump_sidebars.py && docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 python3 /tmp/dump_sidebars.py")
print(stdout.read().decode('utf-8'))
client.close()
