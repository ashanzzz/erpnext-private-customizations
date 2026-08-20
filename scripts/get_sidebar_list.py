import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.getenv('UNRAID_SSH_HOST', '192.168.8.11'), port=int(os.getenv('UNRAID_SSH_PORT', '22')), username=os.getenv('UNRAID_SSH_USER', 'root'), password=os.getenv('UNRAID_SSH_PASSWORD', ''), timeout=15)

cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "ashan_cn_procurement.ashan_cn_procurement.setup.get_sidebar_debug" """
# 我们可以在 setup.py 里加一个临时 debug 函数或者直接查
stdin, stdout, stderr = client.exec_command("""docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "frappe.db.get_list" --args "['Workspace Sidebar Item']" --kwargs "{'fields': ['parent', 'label', 'link_to', 'type'], 'order_by': 'parent, idx', 'limit_page_length': 100}" """)
print("Result:", stdout.read().decode('utf-8'))
client.close()
