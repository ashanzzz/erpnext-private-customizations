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

test_py = """
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# 1. 查询当前用户的语言
lang = frappe.db.get_value("User", "Administrator", "language") or "zh"
print("Current Administrator Language:", lang)

# 2. 查询现有的 Translation 记录
translations = frappe.get_all("Translation", fields=["name", "source_text", "translated_text", "language_code"], limit=10)
print("Existing Translation Count:", len(translations))
for t in translations[:5]:
    print(f"  {t.source_text} -> {t.translated_text} ({t.language_code})")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/test_trans.py', 'wb') as f:
    f.write(test_py.encode('utf-8'))

cmd1 = "docker cp /tmp/test_trans.py erpnext16:/tmp/test_trans.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_trans.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
