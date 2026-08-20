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

stdin, stdout, stderr = ssh.exec_command("docker exec erpnext16 find /home/frappe/frappe-bench/apps/frappe/frappe/public/js -name '*custom_html_block*'")
out = stdout.read().decode()
print("FILES:", out)
if out.strip():
    fn = out.strip().splitlines()[0]
    stdin, stdout, stderr = ssh.exec_command(f"docker exec erpnext16 cat {fn}")
    print("CONTENT:\n", stdout.read().decode())

ssh.close()
