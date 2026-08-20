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

optimize_list_py = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

print("--- 优化 Purchase Invoice 列表列配置 ---")
# 1. 隐藏 due_date
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "due_date"}, "in_list_view", 0)

# 2. 确保 grand_total 在列表中展示
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "grand_total"}, "in_list_view", 1)

# 3. 确保 bill_no 在列表中展示
frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "bill_no"}, "in_list_view", 1)

frappe.db.commit()
frappe.clear_cache(doctype="Purchase Invoice")
print("[OK] 列表列优化完成！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/optimize_pi_list_cols.py', 'wb') as f:
    f.write(optimize_list_py.encode('utf-8'))

cmd1 = "docker cp /tmp/optimize_pi_list_cols.py erpnext16:/tmp/optimize_pi_list_cols.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/optimize_pi_list_cols.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
