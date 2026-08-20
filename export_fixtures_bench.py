import os
import json
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

export_py = """
import json
import frappe

frappe.init('site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

sidebars = ["My Business", "Stock and Inventory", "Procurement Management", "Vehicle Fuel Hub", "Company Compliance Center", "Accounting and Finance", "Ashan CN Procurement"]
result = {}
for sb_name in sidebars:
    if frappe.db.exists("Workspace Sidebar", sb_name):
        doc = frappe.get_doc("Workspace Sidebar", sb_name)
        result[sb_name] = doc.as_dict()

with open('/tmp/workspace_sidebar.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print('[OK] Wrote to /tmp/workspace_sidebar.json')
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/export_sidebars.py', 'wb') as f:
    f.write(export_py.encode('utf-8'))

cmd1 = "docker cp /tmp/export_sidebars.py erpnext16:/tmp/export_sidebars.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/export_sidebars.py"
cmd3 = "docker cp erpnext16:/tmp/workspace_sidebar.json /tmp/workspace_sidebar.json"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
out = ssh.exec_command(cmd2)[1].read().decode('utf-8')
print("Exec output:", out)
ssh.exec_command(cmd3)[1].channel.recv_exit_status()

fixtures_dir = r'd:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\fixtures'
os.makedirs(fixtures_dir, exist_ok=True)
with sftp.open('/tmp/workspace_sidebar.json', 'r') as rf:
    content = rf.read()
    with open(os.path.join(fixtures_dir, 'workspace_sidebar.json'), 'wb') as lf:
        lf.write(content)
print(f"[OK] Downloaded fixtures/workspace_sidebar.json ({len(content)} bytes)")

sftp.close()
ssh.close()
