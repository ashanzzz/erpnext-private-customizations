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

# Check router.js route dispatch logic
cmd = "docker exec erpnext16 grep -A 40 'render(sub_path)' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("router.js render:\n", stdout.read().decode('utf-8', errors='replace'))

# Check how set_route with desk / workspace works
cmd2 = "docker exec erpnext16 grep -A 30 'set_route' /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/router.js | head -35"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("\nset_route:\n", stdout2.read().decode('utf-8', errors='replace'))

ssh.close()
