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
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)

# build
cmd = "docker exec erpnext16 bash -c 'cd /home/frappe/frappe-bench && bench build --app ashan_cn_procurement 2>&1 | tail -15'"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
print("bench build:\n", out)

# verify the js was included in build
cmd2 = "docker exec erpnext16 bash -c 'grep -l ashan_cn_sidebar /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/*.js 2>/dev/null || echo NOT_FOUND'"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("Built file check:", stdout2.read().decode('utf-8', errors='replace').strip())

ssh.close()
