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
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

# 1. Strip child row 'name' from all local workspace json files
ws_root = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace"
for root, dirs, files in os.walk(ws_root):
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
            # Remove system keys
            for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
                data.pop(k, None)
            for table in ['shortcuts', 'links', 'number_cards', 'charts', 'quick_lists', 'custom_blocks', 'roles']:
                if table in data and isinstance(data[table], list):
                    for row in data[table]:
                        if isinstance(row, dict):
                            for rk in ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'parent', 'parentfield', 'parenttype', 'idx']:
                                row.pop(rk, None)
            with open(path, 'w', encoding='utf-8') as jf:
                json.dump(data, jf, indent=1, ensure_ascii=False)
            print(f"Cleaned local workspace JSON: {path}")

# 2. Clear duplicate child table rows in database and restart
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)

sql_cmd = r"""
docker exec erpnext16 su - frappe -c '
cd /home/frappe/frappe-bench
bench --site site1.local mariadb -e "
SET SQL_SAFE_UPDATES = 0;
DELETE FROM \`tabWorkspace Shortcut\` WHERE parent IN (\'My Business\', \'Procurement Management\', \'Stock and Inventory\', \'Accounting and Finance\', \'Vehicle Fuel Hub\', \'Company Compliance Center\');
DELETE FROM \`tabWorkspace Link\` WHERE parent IN (\'My Business\', \'Procurement Management\', \'Stock and Inventory\', \'Accounting and Finance\', \'Vehicle Fuel Hub\', \'Company Compliance Center\');
DELETE FROM \`tabWorkspace Number Card\` WHERE parent IN (\'My Business\', \'Procurement Management\', \'Stock and Inventory\', \'Accounting and Finance\', \'Vehicle Fuel Hub\', \'Company Compliance Center\');
"
'
"""

stdin, stdout, stderr = ssh.exec_command(sql_cmd)
print("DB Clean STDOUT:\n", stdout.read().decode('utf-8'))
print("DB Clean STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
