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

# 读取 apply_section_break_state 及 workspace_title 初始化代码
cmd1 = "docker exec erpnext16 sed -n '250,300p' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.js"
stdin, stdout, stderr = ssh.exec_command(cmd1)
print("APPLY_SECTION_BREAK_STATE:\n", stdout.read().decode('utf-8'))

# workspace_title 如何设置的
cmd2 = "docker exec erpnext16 grep -n 'workspace_title' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar_item.js | head -20"
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("\nWORKSPACE_TITLE REFERENCES:\n", stdout.read().decode('utf-8'))

# 再看 sidebar.js 中 workspace_title 设置
cmd3 = "docker exec erpnext16 grep -n 'workspace_title' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar.js | head -30"
stdin, stdout, stderr = ssh.exec_command(cmd3)
print("\nSIDEBAR.JS WORKSPACE_TITLE:\n", stdout.read().decode('utf-8'))

ssh.close()
