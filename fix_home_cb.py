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

py_code = """# -*- coding: utf-8 -*-
import frappe
import json

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

home_ws = frappe.get_doc("Workspace", "Home")
content_list = json.loads(home_ws.content or "[]")

# 清理旧的 block
content_list = [item for item in content_list if item.get("id") != "chb_biz_scenes_nav" and item.get("type") not in ["custom_block", "custom_html_block"]]

# 插入标准 custom_block
block_item = {
    "id": "chb_biz_scenes_nav",
    "type": "custom_block",
    "data": {
        "custom_block_name": "业务场景导航",
        "col": 12
    }
}
content_list.insert(1, block_item)
home_ws.content = json.dumps(content_list, ensure_ascii=False)
home_ws.save(ignore_permissions=True)

frappe.db.commit()
frappe.clear_cache()
print("[OK] Home 工作区已挂载 custom_block: 业务场景导航！")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/fix_home_cb.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

cmd1 = "docker cp /tmp/fix_home_cb.py erpnext16:/tmp/fix_home_cb.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/fix_home_cb.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
