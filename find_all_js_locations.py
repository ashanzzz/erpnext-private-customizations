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

# Find all JS files related to ashan
cmd = "docker exec erpnext16 find / -name 'ashan_cn_sidebar.js' -type f 2>/dev/null"
stdin, stdout, _ = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
paths = stdout.read().decode('utf-8', errors='replace').strip()
print("All ashan_cn_sidebar.js locations:\n", paths)

# Find nginx conf
cmd2 = "docker exec erpnext16 find /etc /home -name '*.conf' -type f 2>/dev/null | xargs grep -l 'assets\\|frappe' 2>/dev/null | head -5"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("Config files with assets:", stdout2.read().decode('utf-8', errors='replace').strip())

# Check how assets directory is set up
cmd3 = "docker exec erpnext16 ls /home/frappe/frappe-bench/sites/ 2>/dev/null"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("Sites:", stdout3.read().decode('utf-8', errors='replace').strip())

cmd4 = "docker exec erpnext16 ls /home/frappe/frappe-bench/sites/assets/ 2>/dev/null | head -10"
stdin4, stdout4, _ = ssh.exec_command(cmd4)
stdout4.channel.recv_exit_status()
print("Assets dir:", stdout4.read().decode('utf-8', errors='replace').strip())

ssh.close()
