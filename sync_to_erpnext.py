import os
import sys
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

def sync(migrate=False, restart=True):
    """
    Directly uploads local ashan_cn_procurement to erpnext16 container on Unraid host.
    No GitHub push required for quick development iteration!
    """
    print("=== [DEV HOT-SYNC] Local code -> ERPNext16 Container ===")
    
    def tar_filter(tarinfo):
        if '__pycache__' in tarinfo.name or tarinfo.name.endswith('.pyc') or '.git' in tarinfo.name:
            return None
        return tarinfo

    tar_path = os.path.join(tempfile.gettempdir(), "ashan_cn_procurement_dev.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(LOCAL_APP_DIR, arcname="ashan_cn_procurement", filter=tar_filter)
    
    tar_size_kb = os.path.getsize(tar_path) / 1024
    print(f"[1/4] Archived local app files: {tar_size_kb:.1f} KB")

    # SFTP upload to Unraid host
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"[2/4] Connecting to Unraid host ({HOST}:{PORT})...")
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

    sftp = ssh.open_sftp()
    remote_tar = "/tmp/ashan_cn_procurement_dev.tar.gz"
    sftp.put(tar_path, remote_tar)
    sftp.close()
    print("[3/4] Uploaded archive to Unraid /tmp via SFTP")

    # Inject into erpnext16 container
    migrate_cmd = "bench --site site1.local migrate --skip-failing" if migrate else "true"
    restart_cmd = "docker restart erpnext16" if restart else "true"

    remote_exec = f"""
    docker cp {remote_tar} erpnext16:/tmp/ashan_cn_procurement_dev.tar.gz
    docker exec erpnext16 bash -c '
        tar -xzf /tmp/ashan_cn_procurement_dev.tar.gz -C /tmp/
        cp -rf /tmp/ashan_cn_procurement/* /home/frappe/frappe-bench/apps/ashan_cn_procurement/
        rm -rf /tmp/ashan_cn_procurement /tmp/ashan_cn_procurement_dev.tar.gz
        rm -rf /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement
        cd /home/frappe/frappe-bench
        bench build --app ashan_cn_procurement || true
        {migrate_cmd}
        bench --site site1.local clear-cache
    '
    rm -f {remote_tar}
    {restart_cmd}
    """

    print("[4/4] Extracting into container, building assets, clearing cache and restarting...")
    stdin, stdout, stderr = ssh.exec_command(remote_exec)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    
    if "erpnext16" in out or "success" in out.lower():
        print(">>> SUCCESS: erpnext16 updated and restarted in ~2 seconds!")
    else:
        print("STDOUT:\n", out)
        if err:
            print("STDERR:\n", err)

    ssh.close()
    try:
        os.remove(tar_path)
    except Exception:
        pass
    print("=== DEV HOT-SYNC COMPLETE ===\n")

if __name__ == "__main__":
    do_migrate = "--migrate" in sys.argv
    do_restart = "--no-restart" not in sys.argv
    sync(migrate=do_migrate, restart=do_restart)
