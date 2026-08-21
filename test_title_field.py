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

test_title_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 1. 确保 supplier 在列表中展示
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "supplier"}, "in_list_view", 1)

# 2. 将 title_field 清空，让第一列展示标准的单据编号（如 ACC-PINV-2026-00001）
frappe.db.set_value("DocType", "Purchase Invoice", "title_field", "")

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
print("[OK] title_field 已清空，第一列将直接展示单据编号 ACC-PINV-XXXXX！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_title_field.py', 'wb') as f:
    f.write(test_title_py.encode('utf-8'))

cmd1 = "docker cp /tmp/test_title_field.py erpnext16:/tmp/test_title_field.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_title_field.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
