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

sftp = ssh.open_sftp()
clean_code = """
import frappe

def run():
    # 1. Delete redundant workspaces
    for ws_name in ["Ashan CN Procurement", "查看所有物料"]:
        if frappe.db.exists("Workspace", ws_name):
            frappe.delete_doc("Workspace", ws_name, ignore_permissions=True, force=True)
            print("Deleted from DB:", ws_name)

    # 2. Set hide_custom = 1 on all Ashan workspaces
    frappe.db.sql("UPDATE tabWorkspace SET hide_custom = 1 WHERE module = 'Ashan CN Procurement'")
    frappe.db.commit()
    print("Updated hide_custom = 1 for all Ashan CN Procurement workspaces")
"""
with sftp.file('/tmp/clean_ws_script.py', 'w') as f:
    f.write(clean_code)
sftp.close()

exec_cmd = """
docker cp /tmp/clean_ws_script.py erpnext16:/tmp/clean_ws_script.py
docker exec erpnext16 su - frappe -c '
cd /home/frappe/frappe-bench
/home/frappe/frappe-bench/env/bin/python -c "import frappe; frappe.init(site=\\"site1.local\\", sites_path=\\"/home/frappe/frappe-bench/sites\\"); frappe.connect(); import sys; sys.path.insert(0, \\"/tmp\\"); import clean_ws_script; clean_ws_script.run(); frappe.destroy()"
bench --site site1.local clear-cache
'
docker restart erpnext16
"""

stdin, stdout, stderr = ssh.exec_command(exec_cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
