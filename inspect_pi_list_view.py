# -*- coding: utf-8 -*-
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

inspect_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- Current Purchase Invoice fields in List View ---")
meta = frappe.get_meta("Purchase Invoice")
list_fields = [f for f in meta.fields if f.in_list_view]
for f in list_fields:
    print(f"  {f.fieldname} ({f.fieldtype}): label='{f.label}', width={f.columns}")

print("\\n--- Checking existing Purchase Invoices and their items ---")
invoices = frappe.get_all("Purchase Invoice", fields=["name", "supplier", "posting_date", "grand_total"], limit=5)
for inv in invoices:
    doc = frappe.get_doc("Purchase Invoice", inv.name)
    items_summary = [f"{item.item_name or item.item_code} (x{item.qty})" for item in doc.items]
    print(f"Doc: {inv.name} | Supplier: {inv.supplier} | Items: {', '.join(items_summary)}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_pi_list.py', 'wb') as f:
    f.write(inspect_py.encode('utf-8'))

cmd1 = "docker cp /tmp/check_pi_list.py erpnext16:/tmp/check_pi_list.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_pi_list.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
