import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

def run_cmd(client, cmd):
    print(f">> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print(out)
    if err:
        print("ERR:", err)
    return out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

print("Checking Tax Invoice Suite in Container...")
cmd = "docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute ashan_cn_procurement.ashan_cn_procurement.tests.test_tax_invoice_suite.run_all_tests"
run_cmd(client, cmd)

# 检查当前数据库中 Tax Invoice 的数量和状态
check_sql = """
docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute frappe.db.get_list --args '["Tax Invoice", {"fields": ["name", "company", "seller_name", "invoice_grand_total", "match_status", "business_status"], "limit_page_length": 10}]'
"""
print("\nChecking existing Tax Invoices in DB...")
run_cmd(client, check_sql)

client.close()
