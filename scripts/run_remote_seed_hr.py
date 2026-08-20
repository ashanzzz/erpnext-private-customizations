import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_cmd(client, cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 上传 container_seed_hr.py
local_seed = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\container_seed_hr.py"
remote_seed = "/tmp/container_seed_hr.py"

sftp = client.open_sftp()
print(f"Uploading {local_seed} to {remote_seed}...")
sftp.put(local_seed, remote_seed)
sftp.close()

# 拷贝进容器并执行
run_cmd(client, "docker cp /tmp/container_seed_hr.py erpnext16:/home/frappe/frappe-bench/container_seed_hr.py")
run_cmd(client, "docker exec erpnext16 chown frappe:frappe /home/frappe/frappe-bench/container_seed_hr.py")
print("Executing seed in container...")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python container_seed_hr.py")

client.close()
print("\n[OK] Remote HR seed finished!")
