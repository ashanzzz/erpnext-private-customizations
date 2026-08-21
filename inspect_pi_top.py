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
for idx, f in enumerate(meta.fields):
    if idx < 40:
        print(f"[{idx:02d}] {f.fieldtype:<16} | {f.fieldname:<32} | {f.label}")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/inspect_pi_top.py', 'wb') as f:
    f.write(inspect_py.encode('utf-8'))

cmd1 = "docker cp /tmp/inspect_pi_top.py erpnext16:/tmp/inspect_pi_top.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/inspect_pi_top.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)

sftp.close()
ssh.close()
