# -*- coding: utf-8 -*-
import os
import paramiko
import json

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

local_app_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement"
remote_tmp_tar = "/tmp/ashan_app.tar.gz"

os.system(f'tar -czf ashan_app.tar.gz -C "{local_app_dir}" .')
sftp.put("ashan_app.tar.gz", remote_tmp_tar)
if os.path.exists("ashan_app.tar.gz"):
    os.remove("ashan_app.tar.gz")

ssh.exec_command("docker cp /tmp/ashan_app.tar.gz erpnext16:/tmp/ashan_app.tar.gz")[1].channel.recv_exit_status()
ssh.exec_command("docker exec erpnext16 tar -xzf /tmp/ashan_app.tar.gz -C /home/frappe/frappe-bench/apps/ashan_cn_procurement")[1].channel.recv_exit_status()
print("[OK] App files synced to container!")

with open(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\ashan_cn_procurement\workspace_sidebar\my_business.json", "r", encoding="utf-8") as f:
    local_sb = json.load(f)

py_code = f"""# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

frappe.reload_doc("ashan_cn_procurement", "page", "oil_card_ledger")
print("[OK] Page oil-card-ledger reloaded!")

sb_data = {json.dumps(local_sb, ensure_ascii=False)}

for sb_name in ["My Business", "Home"]:
    if frappe.db.exists("Workspace Sidebar", sb_name):
        sb = frappe.get_doc("Workspace Sidebar", sb_name)
        sb.items = []
        for idx, item in enumerate(sb_data.get("items", [])):
            sb.append("items", {{
                "label": item.get("label"),
                "link_type": item.get("link_type"),
                "link_to": item.get("link_to"),
                "icon": item.get("icon"),
                "type": item.get("type"),
                "child": item.get("child", 0),
                "collapsible": item.get("collapsible", 0),
                "indent": item.get("indent", 0),
                "keep_closed": item.get("keep_closed", 0),
                "show_arrow": item.get("show_arrow", 0),
                "url": item.get("url"),
                "idx": idx + 1
            }})
        sb.save(ignore_permissions=True)
        print(f"[OK] Workspace Sidebar [{{sb_name}}] updated!")

frappe.db.commit()
frappe.clear_cache()
print("[OK] All sidebars updated and cache cleared!")
"""

with sftp.open('/tmp/setup_oil_page4.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/setup_oil_page4.py erpnext16:/tmp/setup_oil_page4.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/setup_oil_page4.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
