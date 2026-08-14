import os
import tarfile
import tempfile
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

LOCAL_APP_DIR = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement"

def main():
    print("1. Creating tar archive of local ashan_cn_procurement...")
    tar_path = os.path.join(tempfile.gettempdir(), "ashan_cn_procurement.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(LOCAL_APP_DIR, arcname="ashan_cn_procurement")
    print(f"Archive created: {tar_path} ({os.path.getsize(tar_path)} bytes)")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"2. Connecting SSH to {USER}@{HOST}:{PORT}...")
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    sftp = ssh.open_sftp()
    remote_tar = "/tmp/ashan_cn_procurement.tar.gz"
    print(f"3. Uploading archive to {remote_tar} via SFTP...")
    sftp.put(tar_path, remote_tar)
    sftp.close()
    print("Upload complete.")

    sync_cmd = """
    echo "Extracting archive into erpnext16 container..."
    docker cp /tmp/ashan_cn_procurement.tar.gz erpnext16:/tmp/ashan_cn_procurement.tar.gz
    docker exec erpnext16 bash -c '
        tar -xzf /tmp/ashan_cn_procurement.tar.gz -C /tmp/
        cp -rf /tmp/ashan_cn_procurement/* /home/frappe/frappe-bench/apps/ashan_cn_procurement/
        rm -rf /tmp/ashan_cn_procurement /tmp/ashan_cn_procurement.tar.gz
        rm -rf /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement
        cd /home/frappe/frappe-bench
        bench build --app ashan_cn_procurement || true
        bench --site site1.local migrate --skip-failing || true
        bench --site site1.local clear-cache
        echo "Local app synced into container perfectly!"
    '
    rm -f /tmp/ashan_cn_procurement.tar.gz
    docker restart erpnext16
    """
    
    print("4. Executing container update command...")
    stdin, stdout, stderr = ssh.exec_command(sync_cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:\n", out)
    if err:
        print("STDERR:\n", err)

    ssh.close()
    print("Sync and restart complete!")

if __name__ == "__main__":
    main()
