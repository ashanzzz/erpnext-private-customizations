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

cmd = 'docker exec erpnext16 sed -n "1,40p" /home/frappe/frappe-bench/apps/frappe/frappe/public/scss/common/css_variables.scss'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("css_variables.scss lines 1-40:\n", out)

cmd2 = 'docker exec erpnext16 sed -n "20,100p" /home/frappe/frappe-bench/apps/frappe/frappe/public/scss/desk/form.scss'
stdin, stdout, stderr = ssh.exec_command(cmd2)
out2 = stdout.read().decode('utf-8')
print("form.scss lines 20-100:\n", out2)

cmd3 = 'docker exec erpnext16 grep -rn -C 10 "container" /home/frappe/frappe-bench/apps/frappe/frappe/public/scss/desk/page.scss'
stdin, stdout, stderr = ssh.exec_command(cmd3)
out3 = stdout.read().decode('utf-8')
print("page.scss container:\n", out3)

ssh.close()
