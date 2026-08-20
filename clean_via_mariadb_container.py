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

sftp = ssh.open_sftp()
sql_content = """
DELETE FROM `tabWorkspace Number Card`;
DELETE FROM `tabWorkspace Shortcut` WHERE parent IN ('My Business', 'Procurement Management', 'Stock and Inventory', 'Accounting and Finance', 'Vehicle Fuel Hub', 'Company Compliance Center');
DELETE FROM `tabWorkspace Link` WHERE parent IN ('My Business', 'Procurement Management', 'Stock and Inventory', 'Accounting and Finance', 'Vehicle Fuel Hub', 'Company Compliance Center');
DELETE FROM `tabWorkspace` WHERE name IN ('Ashan CN Procurement', '查看所有物料');
UPDATE `tabWorkspace` SET hide_custom = 1 WHERE module = 'Ashan CN Procurement';
SELECT name, title, parent_page, hide_custom FROM `tabWorkspace` WHERE module = 'Ashan CN Procurement';
"""
with sftp.file('/tmp/clean_workspaces.sql', 'w') as f:
    f.write(sql_content)
sftp.close()

exec_cmd = """
docker cp /tmp/clean_workspaces.sql 1Panel-mariadb:/tmp/clean_workspaces.sql
docker exec 1Panel-mariadb mariadb -u erpnext16 -pbAtk7Gn2BbzbypHS erpnext16 -e "source /tmp/clean_workspaces.sql;"
docker exec 1Panel-mariadb rm -f /tmp/clean_workspaces.sql
rm -f /tmp/clean_workspaces.sql
docker restart erpnext16
"""

stdin, stdout, stderr = ssh.exec_command(exec_cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
