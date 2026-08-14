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

    # 1. Inspect git repo inside container
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'cd /home/frappe/frappe-bench/apps/ashan_cn_procurement && git remote -v && git status'")

    # 2. Pull latest code from GitHub
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'cd /home/frappe/frappe-bench/apps/ashan_cn_procurement && git pull origin master'")

    # 3. Check assets directory
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'ls -la /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ || true'")

    # 4. Remove old cached asset file if symlink or copy
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'rm -f /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js || true'")

    # 5. Clear bench cache and migrate if needed
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'bench --site site1.local clear-cache'")

    # 6. Restart bench / gunicorn
    run_ssh_command(ssh, "docker exec erpnext16 bash -c 'supervisorctl restart all || kill -HUP $(pgrep -f gunicorn) || true'")

    ssh.close()
    print("\nSSH execution and sync complete!")

if __name__ == "__main__":
    main()
