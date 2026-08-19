import os
import tarfile
import tempfile
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

# 1. 压缩本地 ashan_cn_procurement app
local_app_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement"
temp_tar = os.path.join(tempfile.gettempdir(), "ashan_cn_procurement.tar.gz")
print("Archiving local app...")
with tarfile.open(temp_tar, "w:gz") as tar:
    tar.add(local_app_dir, arcname="ashan_cn_procurement")

# 2. 上传到服务器 /tmp
sftp = client.open_sftp()
remote_tar = "/tmp/ashan_cn_procurement.tar.gz"
print(f"Uploading to {remote_tar}...")
sftp.put(temp_tar, remote_tar)
sftp.close()
os.remove(temp_tar)

# 3. 解压到容器内
print("Extracting into erpnext16 container...")
run_cmd(client, "docker cp /tmp/ashan_cn_procurement.tar.gz erpnext16:/tmp/ashan_cn_procurement.tar.gz")
run_cmd(client, "docker exec erpnext16 tar -xzf /tmp/ashan_cn_procurement.tar.gz -C /home/frappe/frappe-bench/apps/")
run_cmd(client, "docker exec erpnext16 chown -R frappe:frappe /home/frappe/frappe-bench/apps/ashan_cn_procurement")

# 4. 执行 bench migrate
print("Running bench migrate...")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local migrate")

# 5. 清理缓存并重启应用重载 Python 模块
print("Clearing cache & restarting services...")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
run_cmd(client, "docker exec erpnext16 supervisorctl restart all")

client.close()
print("\n[OK] Sync & Migrate completed successfully!")
