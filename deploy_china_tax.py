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

sftp = ssh.open_sftp()

files_to_sync = [
    (r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\hooks.py", "/tmp/hooks.py", "/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"),
    (r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\purchase_invoice_tax_calculator.js", "/tmp/purchase_invoice_tax_calculator.js", "/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/purchase_invoice_tax_calculator.js"),
    (r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\overrides\purchase_invoice_tax.py", "/tmp/purchase_invoice_tax.py", "/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/overrides/purchase_invoice_tax.py"),
    (r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\overrides\__init__.py", "/tmp/__init__.py", "/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/overrides/__init__.py")
]

# Ensure overrides dir in container
cmd_mkdir = "docker exec erpnext16 mkdir -p /home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/overrides"
ssh.exec_command(cmd_mkdir)[1].channel.recv_exit_status()

for local_p, tmp_p, remote_p in files_to_sync:
    with open(local_p, 'rb') as lf:
        with sftp.open(tmp_p, 'wb') as rf:
            rf.write(lf.read())
    cmd_cp = f"docker cp {tmp_p} erpnext16:{remote_p}"
    ssh.exec_command(cmd_cp)[1].channel.recv_exit_status()
    print(f"[OK] Synced {remote_p}")

# Also copy js to sites/assets
cmd_assets = "docker cp /tmp/purchase_invoice_tax_calculator.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/purchase_invoice_tax_calculator.js"
ssh.exec_command(cmd_assets)[1].channel.recv_exit_status()

# Clear cache and migrate/build
cmd_cc = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd_cc)[1].channel.recv_exit_status()
print("[OK] Site cache cleared!")

sftp.close()
ssh.close()
