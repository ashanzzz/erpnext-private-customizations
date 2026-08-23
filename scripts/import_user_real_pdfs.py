import os
import glob
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')
CONTAINER_NAME = "erpnext16"

def import_real_invoices():
    # 1. SFTP 上传真实 PDF 到容器 /tmp
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    sftp = client.open_sftp()

    pdf_files = [
        r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206771.pdf",
        r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206826.pdf",
        r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206886.pdf"
    ]

    for p in pdf_files:
        bn = os.path.basename(p)
        remote_path = f"/tmp/{bn}"
        sftp.put(p, remote_path)
        print(f"Uploaded {bn} to Unraid /tmp")
        # 复制进容器
        client.exec_command(f"docker cp /tmp/{bn} {CONTAINER_NAME}:/tmp/{bn}")

    sftp.close()

    # 2. 在容器内执行导入逻辑
    py_cmd = """
import os, frappe
from ashan_cn_procurement.parser.pdf_parser import parse_tax_invoice_pdf
from ashan_cn_procurement.services.tax_invoice_import import save_private_pdf_file, identify_company
from ashan_cn_procurement.services.tax_invoice_matcher import get_matching_purchase_invoices, update_tax_invoice_match_state
from frappe.utils import now_datetime

frappe.set_user('Administrator')

files = ['media_1786978206771.pdf', 'media_1786978206826.pdf', 'media_1786978206886.pdf']
for fn in files:
    fp = f'/tmp/{fn}'
    if not os.path.exists(fp): continue
    with open(fp, 'rb') as f:
        bytes_data = f.read()
    res = parse_tax_invoice_pdf(bytes_data, filename=fn)
    inv_no = res.get('invoice_no')
    if not inv_no: continue
    if frappe.db.exists('Tax Invoice', inv_no):
        frappe.delete_doc('Tax Invoice', inv_no, force=1)

    doc = frappe.new_doc('Tax Invoice')
    doc.invoice_no = inv_no
    doc.issue_date = res.get('issue_date')
    doc.invoice_type = res.get('invoice_type')
    doc.company = identify_company(res.get('buyer_name'), res.get('buyer_tax_id'))
    doc.seller_name = res.get('seller_name')
    doc.seller_tax_id = res.get('seller_tax_id')
    doc.buyer_name = res.get('buyer_name')
    doc.buyer_tax_id = res.get('buyer_tax_id')
    doc.drawer = res.get('drawer')
    doc.amount_without_tax = res.get('amount_without_tax')
    doc.tax_amount = res.get('tax_amount')
    doc.invoice_grand_total = res.get('invoice_grand_total')
    doc.remark_total = res.get('remark_total') or 0.0
    doc.payable_total = res.get('payable_total')
    doc.remark = res.get('remark')
    doc.is_red_invoice = res.get('is_red_invoice') or 0
    doc.parse_status = res.get('parse_status') or '已解析'
    doc.parser_source = 'PDF'
    doc.parser_version = '1.0.0'
    doc.parse_confidence = res.get('parse_confidence')
    doc.parse_warning = res.get('parse_warning')
    doc.original_filename = fn
    doc.imported_at = now_datetime()
    doc.imported_by = 'Administrator'
    doc.business_status = '待录入'
    doc.match_status = '未匹配'
    for it in res.get('items', []):
        doc.append('items', it)
    doc.insert(ignore_permissions=True)

    pdf_url = save_private_pdf_file(bytes_data, fn, doc.name)
    doc.invoice_pdf = pdf_url
    doc.save(ignore_permissions=True)
    print(f'Imported Tax Invoice: {inv_no}, Total: {doc.payable_total}')

frappe.db.commit()
"""
    # 写入容器并执行
    import_script = """import os, frappe
from ashan_cn_procurement.parser.pdf_parser import parse_tax_invoice_pdf
from ashan_cn_procurement.services.tax_invoice_import import save_private_pdf_file, identify_company
from ashan_cn_procurement.services.tax_invoice_matcher import get_matching_purchase_invoices, update_tax_invoice_match_state
from frappe.utils import now_datetime

frappe.set_user('Administrator')

files = ['media_1786978206771.pdf', 'media_1786978206826.pdf', 'media_1786978206886.pdf']
for fn in files:
    fp = f'/tmp/{fn}'
    if not os.path.exists(fp):
        print(f'File {fp} not found')
        continue
    with open(fp, 'rb') as f:
        bytes_data = f.read()
    res = parse_tax_invoice_pdf(bytes_data, filename=fn)
    inv_no = res.get('invoice_no')
    if not inv_no: continue
    if frappe.db.exists('Tax Invoice', inv_no):
        frappe.delete_doc('Tax Invoice', inv_no, force=1)

    doc = frappe.new_doc('Tax Invoice')
    doc.invoice_no = inv_no
    doc.issue_date = res.get('issue_date')
    doc.invoice_type = res.get('invoice_type')
    doc.company = identify_company(res.get('buyer_name'), res.get('buyer_tax_id'))
    doc.seller_name = res.get('seller_name')
    doc.seller_tax_id = res.get('seller_tax_id')
    doc.buyer_name = res.get('buyer_name')
    doc.buyer_tax_id = res.get('buyer_tax_id')
    doc.drawer = res.get('drawer')
    doc.amount_without_tax = res.get('amount_without_tax')
    doc.tax_amount = res.get('tax_amount')
    doc.invoice_grand_total = res.get('invoice_grand_total')
    doc.remark_total = res.get('remark_total') or 0.0
    doc.payable_total = res.get('payable_total')
    doc.remark = res.get('remark')
    doc.is_red_invoice = res.get('is_red_invoice') or 0
    doc.parse_status = res.get('parse_status') or '已解析'
    doc.parser_source = 'PDF'
    doc.parser_version = '1.0.0'
    doc.parse_confidence = res.get('parse_confidence')
    doc.parse_warning = res.get('parse_warning')
    doc.original_filename = fn
    doc.imported_at = now_datetime()
    doc.imported_by = 'Administrator'
    doc.business_status = '待录入'
    doc.match_status = '未匹配'
    for it in res.get('items', []):
        doc.append('items', it)
    doc.insert(ignore_permissions=True)

    pdf_url = save_private_pdf_file(bytes_data, fn, doc.name)
    doc.invoice_pdf = pdf_url
    doc.save(ignore_permissions=True)
    print(f'Imported Tax Invoice: {inv_no}, Total: {doc.payable_total}')

frappe.db.commit()
"""
    stdin, stdout, stderr = client.exec_command(f"docker exec -i -u frappe -w /home/frappe/frappe-bench {CONTAINER_NAME} bench --site site1.local console")
    stdin.write(import_script)
    stdin.close()
    print(stdout.read().decode('utf-8'))
    client.close()

if __name__ == '__main__':
    import_real_invoices()
