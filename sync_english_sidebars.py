import os
import paramiko

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

sync_script = """# -*- coding: utf-8 -*-
import frappe
frappe.init('site1.local')
frappe.connect()

# Find the master sidebar doc with 31 items
master_doc = None
for s in frappe.get_all('Workspace Sidebar', fields=['name']):
    doc = frappe.get_doc('Workspace Sidebar', s.name)
    if len(doc.items) >= 25:
        master_doc = doc
        print(f"Found master sidebar: {doc.name} with {len(doc.items)} items")
        break

if master_doc:
    target_names = [
        "My Business",
        "Stock and Inventory",
        "Procurement Management",
        "Vehicle Fuel Hub",
        "Company Compliance Center",
        "Accounting and Finance",
        "Ashan CN Procurement"
    ]

    for name in target_names:
        if frappe.db.exists('Workspace Sidebar', name):
            sb = frappe.get_doc('Workspace Sidebar', name)
            sb.items = []
            for it in master_doc.items:
                sb.append('items', it.as_dict())
            sb.title = name
            sb.app = "ashan_cn_procurement"
            sb.module = "Ashan CN Procurement"
            sb.flags.ignore_permissions = True
            sb.flags.ignore_links = True
            sb.save()
            print(f"[UPDATED] Workspace Sidebar: {name} with {len(sb.items)} items")
        else:
            sb = frappe.new_doc('Workspace Sidebar')
            sb.name = name
            sb.title = name
            sb.app = "ashan_cn_procurement"
            sb.module = "Ashan CN Procurement"
            for it in master_doc.items:
                sb.append('items', it.as_dict())
            sb.flags.ignore_permissions = True
            sb.flags.ignore_links = True
            sb.insert()
            print(f"[CREATED] Workspace Sidebar: {name} with {len(sb.items)} items")

    frappe.db.commit()
    print("\\n[SUCCESS] All Workspace Sidebar records synchronized with DB commit!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/sync_sidebars.py', 'wb') as f:
    f.write(sync_script.encode('utf-8'))
sftp.close()

cmd = "docker cp /tmp/sync_sidebars.py erpnext16:/tmp/sync_sidebars.py && docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python /tmp/sync_sidebars.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print(stdout.read().decode('utf-8', errors='replace'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

# Clear site cache
cmd2 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd2)[1].channel.recv_exit_status()
print("[OK] Cache cleared on site1.local")

ssh.close()
