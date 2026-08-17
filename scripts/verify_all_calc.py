import os, sys, io, requests, openpyxl

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

print("=== 1. Checking GET Settlement ===")
r = requests.get(f"{site_url}/api/method/ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.get_settlement?year=2026&month=8", headers=headers)
data = r.json().get("message", {})

print(f"Settlement Month: {data.get('settlement_month')}")
print(f"Total Amount: {data.get('total_amount')}")
print(f"Status: {data.get('status')}")

print("\n=== 2. Detailed Company Summaries ===")
for s in data.get("company_summaries", []):
    print(f"Company: {s['company']}")
    print(f"  Rent: {s['rent_amount']}, PropFee: {s['property_fee_amount']}")
    print(f"  Elec: {s['electricity_usage']} kWh, ¥{s['electricity_amount']}")
    print(f"  Water: {s['water_usage']} m3, ¥{s['water_amount']}")
    print(f"  Adj: ¥{s['adjustment_amount']}")
    print(f"  Total: ¥{s['total_amount']}")

print("\n=== 3. Detailed Meter Readings ===")
for m in data.get("meter_readings", []):
    print(f"  [{m['utility_type']}] {m['meter_no']} ({m['company']}): prev={m['previous_reading']}, curr={m['current_reading']}, mult={m['multiplier']}, calc_usage={m['calculated_usage']}, unit_price={m['unit_price']}, amt={m['amount_tax_incl']}")

print("\n=== 4. Detailed Adjustments ===")
for a in data.get("adjustments", []):
    print(f"  [{a['adjustment_type']}] {a['utility_type']} scope={a['adjustment_scope']}: from={a.get('from_company')} to={a.get('to_company')} amt={a['amount_adjustment']} eq_u={a['equivalent_usage']}")

print("\n=== 5. Detailed Lease Charges ===")
for l in data.get("lease_charges", []):
    print(f"  {l['property_name']} ({l['company']}): area={l.get('area')}, rent_ann={l.get('rent_annual_amount')}, rent_daily={l.get('rent_daily_rate')}, rent_mon={l.get('rent_monthly_amount')}, prop_mode={l.get('property_fee_mode')}, rent_amt={l.get('rent_amount_tax_incl')}, prop_amt={l.get('property_fee_amount_tax_incl')}")
