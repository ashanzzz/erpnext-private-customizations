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

# Check assets directory structure
cmd = "docker exec erpnext16 ls /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/"
stdin, stdout, _ = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("ashan_cn_procurement assets:", stdout.read().decode('utf-8', errors='replace').strip())

cmd2 = "docker exec erpnext16 ls /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ 2>/dev/null || echo NO_JS_DIR"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("JS dir:", stdout2.read().decode('utf-8', errors='replace').strip())

# Check css dir
cmd3 = "docker exec erpnext16 ls /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/css/ 2>/dev/null || echo NO_CSS_DIR"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("CSS dir:", stdout3.read().decode('utf-8', errors='replace').strip())

# Check assets.json to see what's actually registered
cmd4 = "docker exec erpnext16 cat /home/frappe/frappe-bench/sites/assets/assets.json 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(k) for k in d if 'ashan' in k.lower()]\" 2>/dev/null || echo 'no assets.json or no ashan'"
stdin4, stdout4, _ = ssh.exec_command(cmd4)
stdout4.channel.recv_exit_status()
print("assets.json ashan entries:", stdout4.read().decode('utf-8', errors='replace').strip())

# Check if there's a webpack bundle
cmd5 = "docker exec erpnext16 find /home/frappe/frappe-bench/sites/assets -name '*ashan*' -type f 2>/dev/null"
stdin5, stdout5, _ = ssh.exec_command(cmd5)
stdout5.channel.recv_exit_status()
print("All ashan files in sites/assets:", stdout5.read().decode('utf-8', errors='replace').strip())

ssh.close()
