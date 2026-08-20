import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

def run_cmd(cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

# 查看 Frappe Error Log 最近 5 条
print("Fetching Error Log entries...")
run_cmd('docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute frappe.db.sql --args \'["SELECT name, method, error, creation FROM `tabError Log` ORDER BY creation DESC LIMIT 5", None, 1]\'')

# 查看容器内的 bench 日志中的最近异常
print("Fetching frappe web.error.log...")
run_cmd('docker exec erpnext16 tail -n 50 /home/frappe/frappe-bench/logs/web.error.log')

client.close()
