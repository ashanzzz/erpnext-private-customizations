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

cmd = 'docker exec erpnext16 grep -rn "update_currency_labels" /home/frappe/frappe-bench/apps/erpnext/erpnext/public/js/'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("ERPNext update_currency_labels search:\n", out)

cmd2 = 'docker exec erpnext16 grep -rn "set_currency_labels" /home/frappe/frappe-bench/apps/erpnext/erpnext/public/js/'
stdin, stdout, stderr = ssh.exec_command(cmd2)
out2 = stdout.read().decode('utf-8')
print("ERPNext set_currency_labels search:\n", out2)

cmd3 = 'docker exec erpnext16 grep -rn "make_head" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/grid_row.js'
stdin, stdout, stderr = ssh.exec_command(cmd3)
out3 = stdout.read().decode('utf-8')
print("grid_row.js make_head search:\n", out3)

ssh.close()
