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

# Check how home_page is used in router.js or workspace.js
cmd = "docker exec erpnext16 grep -rn 'boot.home_page\\|default_route\\|get_sub_path' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/ 2>/dev/null"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("References to boot.home_page/default_route in JS:\n", stdout.read().decode('utf-8', errors='replace'))

# Check get_sub_path implementation in router.js
cmd2 = "docker exec erpnext16 grep -A 25 'get_sub_path' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nget_sub_path implementation:\n", stdout2.read().decode('utf-8', errors='replace'))

ssh.close()
