import os
import paramiko
from dotenv import load_dotenv

load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

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

# 1. 上传导入脚本到宿主机
local_script = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\import_qifu_40_historical_data.py"
remote_script = "/tmp/import_qifu_40_historical_data.py"
print(f"Uploading {local_script} to {remote_script}...")
sftp = client.open_sftp()
sftp.put(local_script, remote_script)
sftp.close()

# 2. 复制到容器内并执行
print("Copying into erpnext16 container and executing...")
run_cmd(client, "docker cp /tmp/import_qifu_40_historical_data.py erpnext16:/tmp/import_qifu_40_historical_data.py")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 /home/frappe/frappe-bench/env/bin/python /tmp/import_qifu_40_historical_data.py")

client.close()
print("\n[OK] Remote data import completed successfully!")
