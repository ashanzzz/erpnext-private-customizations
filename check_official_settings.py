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

inspect_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- System Settings fields related to currency/number ---")
sys_meta = frappe.get_meta("System Settings")
for f in sys_meta.fields:
    if any(w in f.fieldname.lower() for w in ['currency', 'symbol', 'number', 'format', 'hide']):
        print(f"  {f.fieldname} ({f.fieldtype}): {f.label}")

print("\\n--- Accounts Settings fields related to currency/symbol ---")
acc_meta = frappe.get_meta("Accounts Settings")
for f in acc_meta.fields:
    if any(w in f.fieldname.lower() for w in ['currency', 'symbol', 'number', 'format', 'hide']):
        print(f"  {f.fieldname} ({f.fieldtype}): {f.label}")

print("\\n--- DocField fields ---")
df_meta = frappe.get_meta("DocField")
for f in df_meta.fields:
    if any(w in f.fieldname.lower() for w in ['currency', 'symbol', 'hide', 'format']):
        print(f"  {f.fieldname} ({f.fieldtype}): {f.label}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/check_official_currency_settings.py', 'wb') as f:
    f.write(inspect_code.encode('utf-8'))

cmd1 = "docker cp /tmp/check_official_currency_settings.py erpnext16:/tmp/check_official_currency_settings.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/check_official_currency_settings.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
