# -*- coding: utf-8 -*-
import os
import time
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

sftp = ssh.open_sftp()
with open('ashan_cn_procurement/ashan_cn_procurement/patches.txt', 'r', encoding='utf-8') as f:
    content = f.read()

with sftp.open('/tmp/patches.txt', 'wb') as f:
    f.write(content.encode('utf-8'))

sftp.close()

# 尝试 docker cp
for i in range(10):
    stdin, stdout, stderr = ssh.exec_command('docker cp /tmp/patches.txt erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/patches.txt')
    exit_code = stdout.channel.recv_exit_status()
    if exit_code == 0:
        print(f"[OK] patches.txt copied to container on attempt {i+1}!")
        break
    time.sleep(1)

ssh.close()
