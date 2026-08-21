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

py_script = """
import frappe
frappe.init('site1.local')
frappe.connect()

with open('/tmp/sidebar_debug.txt', 'w', encoding='utf-8') as f:
    ws = frappe.get_doc('Workspace', 'My Business')
    f.write(f'Workspace My Business: {ws.title}, module: {ws.module}, app: {ws.app}\\n')
    
    sidebars = frappe.get_all('Workspace Sidebar', fields=['name', 'title', 'module', 'app'])
    f.write(f'All sidebars count: {len(sidebars)}\\n')
    for s in sidebars:
        doc = frappe.get_doc('Workspace Sidebar', s['name'])
        f.write(f'Sidebar {doc.name}: title={doc.title}, app={doc.app}, items_count={len(doc.items)}\\n')
"""

cmd1 = f"docker exec -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python -c \"{py_script}\""
ssh.exec_command(cmd1)[1].channel.recv_exit_status()

cmd2 = "docker exec erpnext16 cat /tmp/sidebar_debug.txt"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("DEBUG OUTPUT:\n", stdout2.read().decode('utf-8', errors='replace'))

ssh.close()
