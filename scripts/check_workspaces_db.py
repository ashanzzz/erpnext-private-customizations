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
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def check_workspaces_in_db():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    cmd = """docker exec erpnext16 bash -c '
    cd /home/frappe/frappe-bench/sites
    /home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(\\"site1.local\\")
frappe.connect()
frappe.set_user(\\"Administrator\\")
print(\\"--- Workspace Table ---\\")
for w in frappe.db.sql(\\"SELECT name, title, public, is_hidden, module FROM tabWorkspace\\", as_dict=True):
    print(w)

print(\\"--- Allowed Workspaces in Bootinfo ---\\")
from frappe.boot import get_bootinfo
boot = get_bootinfo()
print(\\"home_page:\\", boot.get(\\"home_page\\"))
print(\\"default_route:\\", boot.get(\\"default_route\\"))
print(\\"allowed_workspaces:\\", [w.get(\\"name\\") for w in boot.get(\\"allowed_workspaces\\", [])])
"
    '"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == '__main__':
    check_workspaces_in_db()
