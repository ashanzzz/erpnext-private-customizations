import os
import sys

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

try:
    import paramiko
    print("Paramiko is available.")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {USER}@{HOST}:{PORT}...")
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
    print("SSH Connected successfully!")
    
    # Strictly restricted to erpnext16 container
    cmd = "docker ps --filter name=erpnext16 --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("Command Output:")
    print(out)
    if err:
        print("Command Error:", err)
        
    ssh.close()
except ImportError:
    print("Paramiko not installed, testing paramiko installation or alternative...")
except Exception as e:
    print("SSH Connection Error:", e)

