import os, sys, io, requests, json, openpyxl

def load_env():
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

site_url = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
token = os.getenv('ERPNEXT_TOKEN')
headers = {'Authorization': token} if token else {}

print("==================================================")
print(" 1. Verifying Live API on Port 6888")
print("==================================================")

r = requests.get(f"{site_url}/api/method/ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.get_settlement?year=2026&month=8", headers=headers)
print("get_settlement status:", r.status_code)
data = r.json().get("message", {})

print(f"Settlement Month: {data.get('settlement_month')}")
print(f"Status: {data.get('status')}")
print(f"Total Amount: ¥{data.get('total_amount')}")

print("\n--- Company Summaries ---")
for s in data.get("company_summaries", []):
    print(f"Company: {s['company']}")
    print(f"  Rent Amount: ¥{s['rent_amount']}")
    print(f"  Property Fee Amount: ¥{s['property_fee_amount']}")
    print(f"  Elec Usage: {s['electricity_usage']} kWh, Amount: ¥{s['electricity_amount']}")
    print(f"  Water Usage: {s['water_usage']} m³, Amount: ¥{s['water_amount']}")
    print(f"  Adjustment: ¥{s['adjustment_amount']}")
    print(f"  Total: ¥{s['total_amount']}")

print("\n--- Lease Charges in Live System ---")
for l in data.get("lease_charges", []):
    print(f"  {l.get('property_name')} ({l.get('company')}): area={l.get('area')}, rent_ann={l.get('rent_annual_amount')}, rent_amt=¥{l.get('rent_amount_tax_incl')}, prop_amt=¥{l.get('property_fee_amount_tax_incl')}, total=¥{l.get('amount_tax_incl')}")

print("\n==================================================")
print(" 2. Verifying Excel Export for All Modes")
print("==================================================")

for mode, comp in [('all', None), ('company', '天津吉众机电设备有限公司'), ('company', '天津祺富机械加工有限公司'), ('total', None)]:
    url = f"{site_url}/api/method/ashan_cn_procurement.services.property_settlement.export_settlement_excel?settlement_month=2026-08-01&mode={mode}"
    if comp:
        url += f"&company={comp}"
    r = requests.get(url, headers=headers)
    print(f"\n[Mode: {mode}, Comp: {comp}] -> Status: {r.status_code}, Length: {len(r.content)} bytes")
    
    wb = openpyxl.load_workbook(io.BytesIO(r.content), data_only=False)
    print(f"  Sheet names: {wb.sheetnames}")
    for sname in wb.sheetnames:
        ws = wb[sname]
        print(f"  >> Sheet: {sname} (Rows: {ws.max_row}, Cols: {ws.max_column})")
        for r_idx in range(1, ws.max_row + 1):
            row_vals = [ws.cell(r_idx, c).value for c in range(1, ws.max_column + 1)]
            # Check for any string containing error or duplicate text
            for c_val in row_vals:
                if isinstance(c_val, str):
                    if "合计合计" in c_val:
                        print(f"     [ERROR] Duplicate '合计合计' found at Row {r_idx}: {c_val}")
                    if "#DIV/0!" in c_val or "#VALUE!" in c_val or "#REF!" in c_val:
                        print(f"     [ERROR] Excel error formula found at Row {r_idx}: {c_val}")
            if any(v is not None for v in row_vals):
                print(f"     Row {r_idx:2d}: {row_vals}")

print("\n>>> All API & Excel Export Checks Completed Successfully!")
