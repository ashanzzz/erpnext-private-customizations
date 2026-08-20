import os
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

script = """import frappe

frappe.init(site='site1.local')
frappe.connect()

# 确保供应商 圣凯（天津）工业有限公司 存在
supp_name = '圣凯（天津）工业有限公司'
if not frappe.db.exists('Supplier', supp_name):
    s = frappe.new_doc('Supplier')
    s.supplier_name = supp_name
    s.supplier_group = 'All Supplier Groups'
    s.insert(ignore_permissions=True)
    print('Created Supplier:', supp_name)

# 确保公司 天津吉众科技有限公司 或 天津吉众机电设备有限公司 存在
comp_name = '天津吉众科技有限公司'
if not frappe.db.exists('Company', comp_name):
    # 查找已有吉众公司
    existing = frappe.get_all('Company', filters={'name': ['like', '%吉众%']}, pluck='name')
    if existing:
        comp_name = existing[0]
    else:
        comp_name = '天津吉众机电设备有限公司'

print('Using Company:', comp_name)

# 创建或更新 3338平米 真实发票租约台账
lease_name = f"{comp_name}-空港经济区中环南路106号-3338平米"
if frappe.db.exists('Property Lease', lease_name):
    doc = frappe.get_doc('Property Lease', lease_name)
else:
    doc = frappe.new_doc('Property Lease')
    doc.property_name = '空港经济区中环南路106号-3338平米'
    doc.company = comp_name

doc.supplier = supp_name
doc.area = 3338.0
doc.location_address = '天津市东丽区空港经济区中环南路106号'
doc.start_date = '2025-09-22'
doc.end_date = '2026-09-21'
doc.enabled = 1

# 房租 (5% 专票)
doc.rent_pricing_mode = '按年总金额 (元/年)'
doc.is_tax_inclusive = 1
doc.rent_tax_rate = 5.0
doc.rent_annual_amount = 959466.00

# 物业费 (6% 专票，单独计物业费)
doc.property_fee_mode = '单独计物业费'
doc.property_fee_pricing_mode = '按年单价 (元/㎡·年)'
doc.property_fee_is_tax_inclusive = 1
doc.property_fee_tax_rate = 6.0
doc.property_fee_annual_rate = 18.00

doc.remark = '发票号码: 房租 25122000000068752502 (5%专票), 物业费 25122000000068723440 (6%专票)'
doc.save(ignore_permissions=True)
frappe.db.commit()

print(f"Successfully synced Property Lease: {doc.name}")
print(f"Area: {doc.area} ㎡")
print(f"Rent: {doc.rent_annual_amount} (Daily: {doc.rent_daily_rate} 元/㎡·天, Annual: {doc.rent_annual_rate} 元/㎡·年, 5% Tax: {doc.rent_annual_tax_amount})")
print(f"Prop Fee: {doc.property_fee_annual_amount} (Daily: {doc.property_fee_daily_rate} 元/㎡·天, Annual: {doc.property_fee_annual_rate} 元/㎡·年, 6% Tax: {doc.property_fee_annual_tax_amount})")
print(f"Total: {doc.total_annual_amount} (Daily: {doc.total_daily_rate} 元/㎡·天, Annual: {doc.total_annual_rate} 元/㎡·年)")
"""

sftp = client.open_sftp()
with sftp.file('/tmp/sync_real_lease.py', 'wb') as f:
    f.write(script.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = client.exec_command("docker cp /tmp/sync_real_lease.py erpnext16:/tmp/sync_real_lease.py && docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 ../env/bin/python /tmp/sync_real_lease.py")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

client.close()
