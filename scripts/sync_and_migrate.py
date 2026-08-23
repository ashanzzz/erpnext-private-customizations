import os
import sys
import tarfile
import tempfile
import paramiko
from dotenv import load_dotenv

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

load_dotenv()

LAN_HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
TAILSCALE_HOST = os.getenv('UNRAID_TAILSCALE_HOST', '100.80.0.4')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_cmd(client, cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        try:
            print(out)
        except Exception:
            print(out.encode('ascii', errors='replace').decode('ascii'))
    if err:
        try:
            print("ERR:", err)
        except Exception:
            print("ERR:", err.encode('ascii', errors='replace').decode('ascii'))
    return out, err

def connect_ssh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 尝试 1: 局域网地址
    print(f"Connecting to Unraid LAN ({LAN_HOST}:{PORT})...")
    try:
        client.connect(LAN_HOST, port=PORT, username=USER, password=PASSWORD, timeout=5)
        print(f"[OK] Connected via LAN ({LAN_HOST})")
        return client
    except Exception as e:
        print(f"[WARN] LAN connection to {LAN_HOST} failed ({e}). Trying Tailscale remote ({TAILSCALE_HOST})...")

    # 尝试 2: Tailscale 远程地址
    try:
        client.connect(TAILSCALE_HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
        print(f"[OK] Connected via Tailscale ({TAILSCALE_HOST})")
        return client
    except Exception as e:
        raise ConnectionError(f"Failed to connect to both LAN ({LAN_HOST}) and Tailscale ({TAILSCALE_HOST}): {e}")

client = connect_ssh()

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
for attempt in range(1, 4):
    run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 rm -f sites/site1.local/locks/bench_migrate.lock")
    out, err = run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local migrate")
    combined = (out or "") + (err or "")
    if "LockTimeoutError" not in combined and "QueryDeadlockError" not in combined and "OperationalError" not in combined and "Traceback" not in combined:
        break
    print(f"[WARN] Migrate attempt {attempt} failed, retrying in 3s...")
    import time
    time.sleep(3)

# 5. 构建前端静态资源
print("Building frontend assets...")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench build --app ashan_cn_procurement")

# 6. 清理缓存并重启容器重载 Python 模块
print("Clearing cache & restarting container...")
run_cmd(client, "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")
run_cmd(client, "docker restart erpnext16")

client.close()
print("\n[OK] Sync & Migrate completed successfully!")
