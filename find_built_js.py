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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)

# 找找打包后的 JS 在哪里
cmd = "docker exec erpnext16 find /home/frappe/frappe-bench/sites/assets -name '*.js' | xargs grep -l 'ashan_cn_sidebar\\|ASHAN_SIDEBAR_KEY' 2>/dev/null | head -5"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
print("Files containing ashan_cn_sidebar:", out.strip() or "NOT FOUND")

# 检查 hooks.py 中的 app_include_js
cmd2 = "docker exec erpnext16 grep -A5 'app_include_js' /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"
stdin2, stdout2, _ = ssh.exec_command(cmd2)
stdout2.channel.recv_exit_status()
print("hooks.py app_include_js:\n", stdout2.read().decode('utf-8', errors='replace').strip())

# 检查 JS 是否在 bundle 路径中
cmd3 = "docker exec erpnext16 find /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement -name '*.js' 2>/dev/null | head -10"
stdin3, stdout3, _ = ssh.exec_command(cmd3)
stdout3.channel.recv_exit_status()
print("JS files in ashan_cn_procurement assets:", stdout3.read().decode('utf-8', errors='replace').strip())

# 最后看最新修改的 JS
cmd4 = "docker exec erpnext16 ls -lt /home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ 2>/dev/null | head -5 || echo DIR_MISSING"
stdin4, stdout4, _ = ssh.exec_command(cmd4)
stdout4.channel.recv_exit_status()
print("Latest JS:", stdout4.read().decode('utf-8', errors='replace').strip())

ssh.close()
