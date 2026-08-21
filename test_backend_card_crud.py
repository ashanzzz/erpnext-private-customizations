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
from frappe.utils import flt

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

from ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger import quick_create_oil_card, delete_oil_card

res = quick_create_oil_card("粤A·6666 商务测试油卡", "1000116666666666", card_type="副卡", opening_balance=1200.0)
print("SUCCESS CREATE OIL CARD:", res)

del_res = delete_oil_card(res["name"])
print("SUCCESS DELETE OIL CARD:", del_res)
"""

with sftp.open('/tmp/test_card_crud.py', 'wb') as f:
    f.write(py_code.encode('utf-8'))

ssh.exec_command("docker cp /tmp/test_card_crud.py erpnext16:/tmp/test_card_crud.py")[1].channel.recv_exit_status()
sftp.close()
ssh.close()
