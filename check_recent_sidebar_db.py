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

cmd = """
docker exec 1Panel-mariadb mariadb -u erpnext16 -pbAtk7Gn2BbzbypHS erpnext16 -e "
SELECT name, app, module, title FROM \`tabWorkspace Sidebar\` ORDER BY modified DESC LIMIT 5;
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("RECENT WORKSPACE SIDEBARS:\n", stdout.read().decode('utf-8'))
ssh.close()
