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

sql_cmd = """
docker exec erpnext16 su - frappe -c '
cd /home/frappe/frappe-bench
bench --site site1.local mariadb -e "
SET SQL_SAFE_UPDATES = 0;
DELETE FROM tabWorkspace WHERE name IN (\\\"Ashan CN Procurement\\\", \\\"查看所有物料\\\");
UPDATE tabWorkspace SET hide_custom = 1 WHERE module = \\\"Ashan CN Procurement\\\";
SELECT name, title, parent_page, hide_custom FROM tabWorkspace WHERE module = \\\"Ashan CN Procurement\\\";
"
bench --site site1.local clear-cache
'
docker restart erpnext16
"""

stdin, stdout, stderr = ssh.exec_command(sql_cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
