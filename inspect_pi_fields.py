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

inspect_py = """
import frappe
frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

meta = frappe.get_meta("Purchase Invoice")
fields = []
for df in meta.fields:
    fields.append({
        "fieldname": df.fieldname,
        "label": df.label,
        "fieldtype": df.fieldtype,
        "hidden": df.hidden
    })

print("TOTAL_FIELDS:", len(fields))
for f in fields:
    if f['fieldtype'] in ['Section Break', 'Column Break', 'Tab Break'] or any(k in (f['label'] or '') for k in ['发票', '业务', '日期', '供应商', 'Series', 'Items', '税']):
        print(f"  [{f['fieldtype']:<14}] {f['fieldname']:<30} -> {f['label']}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/inspect_pi_fields.py', 'wb') as f:
    f.write(inspect_py.encode('utf-8'))

cmd1 = "docker cp /tmp/inspect_pi_fields.py erpnext16:/tmp/inspect_pi_fields.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/inspect_pi_fields.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
