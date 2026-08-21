import os
import json
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

# Copy JS from docker container to host /tmp
cmd1 = "docker cp erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js /tmp/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()

# 1. Sync ashan_cn_sidebar.js from /tmp to local
sftp = ssh.open_sftp()
local_js = r'd:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\ashan_cn_sidebar.js'

with sftp.open('/tmp/ashan_cn_sidebar.js', 'r') as rf:
    content = rf.read()
    with open(local_js, 'wb') as lf:
        lf.write(content)
print(f"[OK] Synced ashan_cn_sidebar.js to local: {len(content)} bytes")

# 2. Export workspace_sidebar records to json
export_script = """
import json
import frappe

sidebars = ["My Business", "Stock and Inventory", "Procurement Management", "Vehicle Fuel Hub", "Company Compliance Center", "Accounting and Finance", "Ashan CN Procurement"]
result = {}
for sb_name in sidebars:
    if frappe.db.exists("Workspace Sidebar", sb_name):
        doc = frappe.get_doc("Workspace Sidebar", sb_name)
        result[sb_name] = doc.as_dict()

print("---JSON_OUTPUT---")
print(json.dumps(result, ensure_ascii=False, default=str))
"""

cmd2 = f"docker exec erpnext16 python3 -c {json.dumps(export_script)}"
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8', errors='replace')
if "---JSON_OUTPUT---" in out:
    json_data = json.loads(out.split("---JSON_OUTPUT---")[1].strip())
    fixtures_dir = r'd:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\fixtures'
    os.makedirs(fixtures_dir, exist_ok=True)
    with open(os.path.join(fixtures_dir, 'workspace_sidebar.json'), 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Exported {len(json_data)} Workspace Sidebars to fixtures/workspace_sidebar.json")

sftp.close()
ssh.close()
