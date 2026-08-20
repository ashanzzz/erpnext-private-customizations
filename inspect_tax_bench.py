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

inspect_code = """
import json
import frappe

# 1. 查看现有税率模板 Item Tax Template
item_tax_templates = frappe.get_all("Item Tax Template", fields=["name", "company", "disabled"])
for t in item_tax_templates:
    doc = frappe.get_doc("Item Tax Template", t.name)
    taxes = [{"tax_type": r.tax_type, "tax_rate": r.tax_rate} for r in doc.taxes]
    t["taxes"] = taxes

# 2. 查看采购税费模板 Purchase Taxes and Charges Template
ptc_templates = frappe.get_all("Purchase Taxes and Charges Template", fields=["name", "company", "is_default", "disabled"])
for t in ptc_templates:
    doc = frappe.get_doc("Purchase Taxes and Charges Template", t.name)
    taxes = [{"account_head": r.account_head, "rate": r.rate, "category": r.category, "add_deduct_tax": r.add_deduct_tax} for r in doc.taxes]
    t["taxes"] = taxes

# 3. 查看税费相关会计科目
tax_accounts = frappe.get_all("Account", filters=[["account_type", "in", ["Tax", "Chargeable"]]], fields=["name", "account_name", "company", "parent_account", "account_type"])

# 4. 查看 Purchase Invoice Item 上字段
pi_item_fields = frappe.get_meta("Purchase Invoice Item").fields
tax_fields_on_item = [{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype, "in_list_view": f.in_list_view} for f in pi_item_fields if "tax" in f.fieldname.lower() or "rate" in f.fieldname.lower() or "amount" in f.fieldname.lower() or "vat" in f.fieldname.lower() or "税" in (f.label or "")]

# 5. 查看 Custom Field
custom_fields = frappe.get_all("Custom Field", filters=[["dt", "in", ["Purchase Invoice", "Purchase Invoice Item"]]], fields=["name", "dt", "fieldname", "label", "fieldtype", "insert_after"])

client_scripts = frappe.get_all("Client Script", filters=[["dt", "in", ["Purchase Invoice", "Purchase Invoice Item"]]], fields=["name", "dt", "enabled"])

print("---INSPECT_RESULT---")
print(json.dumps({
    "item_tax_templates": item_tax_templates,
    "ptc_templates": ptc_templates,
    "tax_accounts": tax_accounts,
    "tax_fields_on_item": tax_fields_on_item,
    "custom_fields": custom_fields,
    "client_scripts": client_scripts
}, ensure_ascii=False, indent=2))
"""

cmd = f"docker exec -i erpnext16 bench --site site1.local console << 'EOF'\n{inspect_code}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
if "---INSPECT_RESULT---" in out:
    res = json.loads(out.split("---INSPECT_RESULT---")[1].strip().split("\n\n")[0].strip())
    print(json.dumps(res, ensure_ascii=False, indent=2))
else:
    print("Full Output:", out)

ssh.close()
