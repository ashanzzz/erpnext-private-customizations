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

def test_bootinfo_workspaces():
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
from frappe.boot import get_bootinfo
boot = get_bootinfo()
print(\\"Workspaces pages:\\", [p.get(\\"name\\") for p in boot.get(\\"workspaces\\", {}).get(\\"pages\\", [])])
print(\\"home_page in bootinfo:\\", boot.get(\\"home_page\\"))
print(\\"default_route in bootinfo:\\", boot.get(\\"default_route\\"))
"
    '"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == '__main__':
    test_bootinfo_workspaces()
