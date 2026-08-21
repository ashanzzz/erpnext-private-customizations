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

# Check the deployed file has the correct content
cmd = "docker exec erpnext16 grep -c 'ASHAN_SIDEBAR_KEY\\|ashan-cn-sidebar-state\\|restore_sidebar_states' /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
count = stdout.read().decode('utf-8', errors='replace').strip()
print(f"Key string occurrences in deployed file: {count}")

# The app_include_js path is different from sites/assets - check
# Frappe serves from sites/assets and the source is in apps dir
# bench build copies from apps/*/public to sites/assets
# Check if they match now
cmd2 = "docker exec erpnext16 diff /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js && echo FILES_MATCH || echo FILES_DIFFER"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("Diff check:", stdout2.read().decode('utf-8', errors='replace').strip())

ssh.close()
