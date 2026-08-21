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
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

# Check if puppeteer exists and where
cmd = "which puppeteer 2>/dev/null || npm list -g puppeteer 2>/dev/null | head -5 || echo NOT_INSTALLED"
stdin, stdout, _ = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()
print("puppeteer:", stdout.read().decode('utf-8', errors='replace').strip())

# Check playwright
cmd2 = "which playwright 2>/dev/null || npm list -g playwright 2>/dev/null | head -3 || echo NOT_INSTALLED"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("playwright:", stdout2.read().decode('utf-8', errors='replace').strip())

# Check if chromium available
cmd3 = "which chromium-browser 2>/dev/null || which chromium 2>/dev/null || which google-chrome 2>/dev/null || echo NO_CHROME"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("chrome:", stdout3.read().decode('utf-8', errors='replace').strip())

# Check global node_modules
cmd4 = "ls /usr/lib/node_modules/ 2>/dev/null | head -20 || ls /usr/local/lib/node_modules/ 2>/dev/null | head -20"
stdin4, stdout4, _ = ssh.exec_command(cmd4)
stdout4.channel.recv_exit_status()
print("global node_modules:", stdout4.read().decode('utf-8', errors='replace').strip())

ssh.close()
