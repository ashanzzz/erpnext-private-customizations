import os
import sys
import glob
sys.path.insert(0, r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement")
from ashan_cn_procurement.parser.pdf_parser import parse_tax_invoice_pdf

def test_real_pdfs():
    pdf_files = glob.glob(r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\*.pdf")
    print(f"Found {len(pdf_files)} user PDFs")
    for p in pdf_files:
        with open(p, 'rb') as f:
            data = f.read()
        res = parse_tax_invoice_pdf(data, filename=os.path.basename(p))
        print("--------------------------------------------------")
        print(f"File: {os.path.basename(p)}")
        print(f"Invoice No: {res.get('invoice_no')}")
        print(f"Issue Date: {res.get('issue_date')}")
        print(f"Seller: {res.get('seller_name')}")
        print(f"Buyer: {res.get('buyer_name')}")
        print(f"Grand Total: {res.get('invoice_grand_total')}")
        print(f"Tax Amount: {res.get('tax_amount')}")
        print(f"VV Tax: {res.get('vehicle_vessel_tax')}")
        print(f"Payable Total: {res.get('payable_total')}")
        print(f"Items count: {len(res.get('items', []))}")
        print(f"Confidence: {res.get('parse_confidence')}")
        print(f"Warnings: {res.get('parse_warning')}")

if __name__ == '__main__':
    test_real_pdfs()
