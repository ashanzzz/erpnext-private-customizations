import os
import time
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
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')

# Install puppeteer on Unraid host with npm
INSTALL_CMD = "npm install -g puppeteer --prefer-offline 2>&1 | tail -5"
RUN_CMD = "PUPPETEER_SKIP_DOWNLOAD=false npx puppeteer browsers install chrome 2>&1 | tail -3"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

# Check docker containers with chrome
cmd = "docker ps --format '{{.Names}}' | head -20"
stdin, stdout, _ = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
containers = stdout.read().decode('utf-8', errors='replace').strip()
print("Containers:", containers)

# Try using playwright in a container (frappe typically has chromium)
cmd2 = "docker exec erpnext16 which chromium-browser 2>/dev/null || docker exec erpnext16 which chromium 2>/dev/null || docker exec erpnext16 which google-chrome 2>/dev/null || echo NO_CHROME_IN_CONTAINER"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("Chrome in container:", stdout2.read().decode('utf-8', errors='replace').strip())

# Check playwright-worker or other containers
cmd3 = "docker images | grep -i 'play\\|chrom\\|browser\\|node' | head -10"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("Browser images:", stdout3.read().decode('utf-8', errors='replace').strip())

ssh.close()
