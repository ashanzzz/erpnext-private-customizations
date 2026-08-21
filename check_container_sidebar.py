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

cmd = 'docker exec erpnext16 head -n 40 /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("container ashan_cn_sidebar.js head:\n", out)

cmd2 = 'docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local build --app ashan_cn_procurement'
stdin, stdout, stderr = ssh.exec_command(cmd2)
out2 = stdout.read().decode('utf-8')
print("bench build app:\n", out2)

cmd3 = 'docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache'
stdin, stdout, stderr = ssh.exec_command(cmd3)
out3 = stdout.read().decode('utf-8')
print("clear cache:\n", out3)

ssh.close()
