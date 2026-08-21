# -*- coding: utf-8 -*-
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
py_code = """# -*- coding: utf-8 -*-
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

from ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger import get_unified_ledger_data

cards = frappe.get_all("Oil Card", fields=["name", "card_name", "opening_balance", "current_balance"])
print("ALL CARDS IN DB:")
for c in cards:
    print(c)
    data = get_unified_ledger_data(c.name, 2026, 8)
    print("  -> KPI opening_balance:", data["kpis"]["opening_balance"], "ending_balance:", data["kpis"]["ending_balance"])
"""

with sftp.open('/tmp/test_card_kpis.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

ssh.exec_command("docker cp /tmp/test_card_kpis.py erpnext16:/tmp/test_card_kpis.py")[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command("docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/test_card_kpis.py")
print("STDOUT:", stdout.read().decode('utf-8'))

sftp.close()
ssh.close()
