import os
import shlex
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
DB_USER = shlex.quote(os.getenv('ERPNEXT_DB_USER', 'erpnext16'))
DB_PASSWORD = os.getenv('ERPNEXT_DB_PASSWORD', '')
DB_PASSWORD_ARG = shlex.quote(f'-p{DB_PASSWORD}') if DB_PASSWORD else ''
DB_NAME = shlex.quote(os.getenv('ERPNEXT_DB_NAME', 'erpnext16'))

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

cmd = rf"""
docker exec 1Panel-mariadb mariadb -u {DB_USER} {DB_PASSWORD_ARG} {DB_NAME} -e "
SELECT idx, label, type, link_type, link_to, parent FROM \`tabWorkspace Sidebar Item\` WHERE parent = (SELECT name FROM \`tabWorkspace Sidebar\` WHERE app='ashan_cn_procurement') ORDER BY idx ASC;
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("APP SIDEBAR ITEMS IN DB:\n", stdout.read().decode('utf-8'))
ssh.close()
