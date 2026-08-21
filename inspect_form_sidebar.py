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

cmd1 = 'docker exec erpnext16 grep -rn -C 5 "form-sidebar" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/'
stdin, stdout, stderr = ssh.exec_command(cmd1)
out1 = stdout.read().decode('utf-8')
print("form-sidebar JS search:\n", out1[:1500])

cmd2 = 'docker exec erpnext16 sed -n "1,80p" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/sidebar/form_sidebar.js'
stdin, stdout, stderr = ssh.exec_command(cmd2)
out2 = stdout.read().decode('utf-8')
print("form_sidebar.js lines 1-80:\n", out2)

cmd3 = 'docker exec erpnext16 grep -rn -C 5 "hide_sidebar" /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/'
stdin, stdout, stderr = ssh.exec_command(cmd3)
out3 = stdout.read().decode('utf-8')
print("hide_sidebar search:\n", out3)

ssh.close()
