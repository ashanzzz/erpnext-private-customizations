# -*- coding: utf-8 -*-
import os
import paramiko
import json

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

py_code = """# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

doc = frappe.get_doc("Custom HTML Block", "业务场景导航")
d = doc.as_dict()
# 移除时间戳
for k in ["creation", "modified", "modified_by", "owner", "_liked_by", "_comments", "_assign"]:
    d.pop(k, None)

print(json.dumps(d, ensure_ascii=False, indent=2))
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/export_chb.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/export_chb.py erpnext16:/tmp/export_chb.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/export_chb.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')

with open('ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json', 'w', encoding='utf-8') as f:
    f.write(out.strip())

print("Fixture saved to ashan_cn_procurement/ashan_cn_procurement/fixtures/custom_html_block.json")

sftp.close()
ssh.close()
