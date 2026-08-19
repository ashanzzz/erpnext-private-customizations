import os
import json
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

# 调用 get_month_settlement_data(2026, 7)
cmd = """docker exec -u frappe -w /home/frappe/frappe-bench erpnext16 bench --site site1.local execute "ashan_cn_procurement.services.property_settlement.get_month_settlement_data" --args "[2026, 7]" """
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
print("=== 2026-07 Settlement Calculation Result ===")
try:
    data = json.loads(out)
    print("Company Summaries:")
    for s in data.get("company_summaries", []):
        print(f"Company: {s.get('company')}, Rent: {s.get('rent_amount')}, RentTax: {s.get('rent_tax_amount')}, RentExcl: {s.get('rent_amount_tax_excl')}, PropFee: {s.get('property_fee_amount')}")
    print("\nLease Charges:")
    for l in data.get("lease_charges", []):
        print(f"- {l.get('property_name')}: Area={l.get('area')}, TaxRate={l.get('tax_rate')}%, RentIncl={l.get('rent_amount_tax_incl')}, TaxAmt={l.get('tax_amount')}, ExclAmt={l.get('amount_tax_excl')}")
except Exception as e:
    print(out)

client.close()
