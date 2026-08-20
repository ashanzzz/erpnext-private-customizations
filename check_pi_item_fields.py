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

py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

fields = frappe.db.sql('''
    SELECT idx, fieldname, label, fieldtype, hidden, reqd
    FROM `tabDocField`
    WHERE parent = 'Purchase Invoice Item'
    ORDER BY idx ASC
''', as_dict=True)

print("Purchase Invoice Item DocFields count:", len(fields))
for f in fields:
    print(f"  [{f.idx}] {f.fieldname} ({f.fieldtype}) - {f.label} [hidden={f.hidden}]")

cfields = frappe.db.sql('''
    SELECT name, fieldname, label, fieldtype, hidden, insert_after
    FROM `tabCustom Field`
    WHERE dt = 'Purchase Invoice Item'
''', as_dict=True)

print("\\nCustom Fields of Purchase Invoice Item:")
for cf in cfields:
    print(f"  {cf.fieldname} ({cf.fieldtype}) - {cf.label}, insert_after: {cf.insert_after}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_pi_item_fields.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/check_pi_item_fields.py erpnext16:/tmp/check_pi_item_fields.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_pi_item_fields.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
