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

def run_ssh_command(ssh, cmd):
    print(f"\n>>> EXECUTING: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out:
        print("[STDOUT]\n" + out.strip())
    if err:
        print("[STDERR]\n" + err.strip())
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to Unraid host {HOST}:{PORT} as {USER}...")
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
    print("SSH connection established.")

    # 1. Clone fresh repository inside container
    cmd_sync = """
    docker exec erpnext16 bash -c '
        set -e
        echo "1. Cloning latest GitHub repo..."
        rm -rf /tmp/ashan_repo
        git clone --depth 1 https://github.com/ashanzzz/erpnext-private-customizations.git /tmp/ashan_repo
        
        echo "2. Syncing files into apps/ashan_cn_procurement..."
        cp -rf /tmp/ashan_repo/* /home/frappe/frappe-bench/apps/ashan_cn_procurement/
        cp -rf /tmp/ashan_repo/.git /home/frappe/frappe-bench/apps/ashan_cn_procurement/ || true
        rm -rf /tmp/ashan_repo
        
        echo "3. Removing any old static assets..."
        rm -rf /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement
        
        echo "4. Running bench build & clear-cache..."
        cd /home/frappe/frappe-bench
        bench build --app ashan_cn_procurement || true
        bench --site site1.local clear-cache
        echo "Sync finished successfully!"
    '
    """
    run_ssh_command(ssh, cmd_sync)

    # 2. Restart container via docker restart erpnext16 on host
    run_ssh_command(ssh, "docker restart erpnext16")

    ssh.close()
    print("\nContainer updated and restarted successfully!")

if __name__ == "__main__":
    main()
