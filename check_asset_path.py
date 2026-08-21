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

# Find actual path Frappe serves assets from
# Check app_include_js path
cmd = "docker exec erpnext16 grep -r 'app_include_js' /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"
stdin, stdout, _ = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("hooks:", stdout.read().decode('utf-8', errors='replace').strip())

# Find where the js file actually lives that nginx serves
cmd2 = "docker exec erpnext16 find /home/frappe/frappe-bench/sites -name 'ashan_cn_sidebar.js' -type f 2>/dev/null"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("Sidebar JS paths:", stdout2.read().decode('utf-8', errors='replace').strip())

# Check nginx config for proxy
cmd3 = "docker exec erpnext16 cat /etc/nginx/conf.d/frappe-bench.conf 2>/dev/null | grep -A3 'assets' | head -30"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("Nginx assets config:", stdout3.read().decode('utf-8', errors='replace').strip())

ssh.close()
