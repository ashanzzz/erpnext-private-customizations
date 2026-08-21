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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

cmd = """
docker exec erpnext16 su - frappe -c '
cd /home/frappe/frappe-bench
bench --site site1.local execute "
import frappe
print(\\\"=== BOOT WORKSPACE PAGES ===\\\")
from frappe.boot import get_allowed_pages
print(\\\"Allowed pages:\\\", len(frappe.boot.get_allowed_pages()))

print(\\\"=== ASHAN WORKSPACES IN DB ===\\\")
for w in frappe.get_all(\\\"Workspace\\\", filters={\\\"module\\\": \\\"Ashan CN Procurement\\\"}, fields=[\\\"name\\\", \\\"module\\\", \\\"parent_page\\\", \\\"public\\\", \\\"is_hidden\\\", \\\"hide_custom\\\"]):
    print(w)
"
'
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
ssh.close()
