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

sftp = ssh.open_sftp()

local_app_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement"
remote_tmp_tar = "/tmp/ashan_app.tar.gz"

os.system(f'tar -czf ashan_app.tar.gz -C "{local_app_dir}" .')
sftp.put("ashan_app.tar.gz", remote_tmp_tar)
if os.path.exists("ashan_app.tar.gz"):
    os.remove("ashan_app.tar.gz")

ssh.exec_command("docker cp /tmp/ashan_app.tar.gz erpnext16:/tmp/ashan_app.tar.gz")[1].channel.recv_exit_status()
ssh.exec_command("docker exec erpnext16 tar -xzf /tmp/ashan_app.tar.gz -C /home/frappe/frappe-bench/apps/ashan_cn_procurement")[1].channel.recv_exit_status()
print("[OK] App files synced to container!")

py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

frappe.reload_doc("ashan_cn_procurement", "page", "oil_card_ledger")
print("[OK] Page oil-card-ledger reloaded!")

frappe.db.commit()
frappe.clear_cache()
print("[OK] Cache cleared!")
"""

with sftp.open('/tmp/setup_unified_ledger2.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/setup_unified_ledger2.py erpnext16:/tmp/setup_unified_ledger2.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/setup_unified_ledger2.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

# 重启容器使新 Python 代码立即在 gunicorn/web workers 中生效
ssh.exec_command("docker restart erpnext16")[1].channel.recv_exit_status()
print("[OK] Container restarted to guarantee fresh Python memory!")

sftp.close()
ssh.close()
