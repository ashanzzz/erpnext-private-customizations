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

# 1. 基础路径
local_py = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\overrides\purchase_invoice_tax.py"
local_calc_js = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\purchase_invoice_tax_calculator.js"
local_list_js = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\purchase_invoice_list.js"
local_sidebar_js = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\ashan_cn_sidebar.js"
local_css = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\css\ashan_cn_procurement.css"
local_hooks = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\hooks.py"
local_boot = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\boot.py"

# 2. SSH 远程同步
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)
sftp = ssh.open_sftp()

files_to_sync = [
    (local_sidebar_js, '/tmp/ashan_cn_sidebar.js', [
        "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js",
        "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
    ]),
    (local_calc_js, '/tmp/purchase_invoice_tax_calculator.js', [
        "docker cp /tmp/purchase_invoice_tax_calculator.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/purchase_invoice_tax_calculator.js",
        "docker cp /tmp/purchase_invoice_tax_calculator.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/purchase_invoice_tax_calculator.js"
    ]),
    (local_list_js, '/tmp/purchase_invoice_list.js', [
        "docker cp /tmp/purchase_invoice_list.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/purchase_invoice_list.js",
        "docker cp /tmp/purchase_invoice_list.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/purchase_invoice_list.js"
    ]),
    (local_css, '/tmp/ashan_cn_procurement.css', [
        "docker cp /tmp/ashan_cn_procurement.css erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/css/ashan_cn_procurement.css",
        "docker cp /tmp/ashan_cn_procurement.css erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/css/ashan_cn_procurement.css"
    ]),
    (local_py, '/tmp/purchase_invoice_tax.py', [
        "docker cp /tmp/purchase_invoice_tax.py erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/overrides/purchase_invoice_tax.py"
    ]),
    (local_hooks, '/tmp/hooks.py', [
        "docker cp /tmp/hooks.py erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/hooks.py"
    ]),
    (local_boot, '/tmp/boot.py', [
        "docker cp /tmp/boot.py erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/boot.py"
    ])
]

for lpath, rtmp, dcmds in files_to_sync:
    with sftp.open(rtmp, 'wb') as rf:
        with open(lpath, 'rb') as lf:
            rf.write(lf.read())
    for dcmd in dcmds:
        ssh.exec_command(dcmd)[1].channel.recv_exit_status()

# 刷新缓存
ssh.exec_command("docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache")[1].channel.recv_exit_status()
print("[OK] All assets, CSS, Python backend synced and cache cleared!")

sftp.close()
ssh.close()
