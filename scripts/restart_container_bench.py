import os
import sys
import paramiko
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
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
    if out: print(out)
    if err: print("[ERR]", err)
    return out

# 清理 pyc 并重启
run_cmd("docker exec erpnext16 find /home/frappe/frappe-bench/apps/ashan_cn_procurement -name '*.pyc' -delete")
run_cmd("docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
run_cmd("docker restart erpnext16")

client.close()
print("Restarted erpnext16 container!")
