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

sftp = ssh.open_sftp()
sql_content = """
DELETE FROM `tabWorkspace Number Card`;
DELETE FROM `tabWorkspace Chart`;
DELETE FROM `tabWorkspace Shortcut`;
DELETE FROM `tabWorkspace Link`;
DELETE FROM `tabWorkspace Quick List`;
DELETE FROM `tabWorkspace Custom Block`;
"""
with sftp.file('/tmp/clean_all_ws_tables.sql', 'w') as f:
    f.write(sql_content)
sftp.close()

exec_cmd = rf"""
docker cp /tmp/clean_all_ws_tables.sql 1Panel-mariadb:/tmp/clean_all_ws_tables.sql
docker exec 1Panel-mariadb mariadb -u {DB_USER} {DB_PASSWORD_ARG} {DB_NAME} -e "source /tmp/clean_all_ws_tables.sql;"
docker exec 1Panel-mariadb rm -f /tmp/clean_all_ws_tables.sql
rm -f /tmp/clean_all_ws_tables.sql
docker restart erpnext16
"""

stdin, stdout, stderr = ssh.exec_command(exec_cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
