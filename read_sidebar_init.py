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
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

# 读取第1-30行，了解 workspace_title 的初始化
cmd1 = "docker exec erpnext16 sed -n '1,30p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.js"
stdin, stdout, stderr = ssh.exec_command(cmd1)
print("TOP OF sidebar_item.js:\n", stdout.read().decode('utf-8'))

# 读取 sidebar.js set_workspace_sidebar
cmd2 = "docker exec erpnext16 sed -n '278,330p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar.js"
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("\nSIDE.JS set_workspace_sidebar:\n", stdout.read().decode('utf-8'))

ssh.close()
