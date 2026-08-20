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

# 读取 sidebar_item.js 中 setup_event_listner / toggle / open / close 全部关键函数
cmd = "docker exec erpnext16 sed -n '280,400p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.js"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("SIDEBAR_ITEM.JS TOGGLE/OPEN/CLOSE LOGIC:\n", stdout.read().decode('utf-8'))
ssh.close()
