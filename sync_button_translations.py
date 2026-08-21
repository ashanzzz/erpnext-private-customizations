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

sync_translations_py = """
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

translations = [
    ("Save", "保存"),
    ("save", "保存"),
    ("Create", "创建"),
    ("create", "创建"),
    ("Add", "添加"),
    ("add", "添加"),
    ("Add Row", "添加行"),
    ("Add row", "添加行"),
    ("Add multiple", "批量添加"),
    ("Download", "下载"),
    ("Upload", "上传"),
    ("Not Saved", "未保存"),
    ("Saved", "已保存"),
    ("Submit", "提交"),
    ("Cancel", "作废"),
    ("Amend", "修改/重开"),
    ("Actions", "操作"),
    ("Duplicate", "复制"),
    ("Delete", "删除"),
    ("Print", "打印"),
    ("Email", "发送邮件"),
    ("Activity", "操作动态"),
    ("Status", "状态")
]

for src, trans in translations:
    existing = frappe.db.get_value("Translation", {"source_text": src, "language": "zh"}, "name")
    if existing:
        doc = frappe.get_doc("Translation", existing)
        doc.translated_text = trans
        doc.save(ignore_permissions=True)
        print(f"Updated Translation: {src} -> {trans}")
    else:
        doc = frappe.get_doc({
            "doctype": "Translation",
            "language": "zh",
            "source_text": src,
            "translated_text": trans
        })
        doc.insert(ignore_permissions=True)
        print(f"Inserted Translation: {src} -> {trans}")

frappe.db.commit()
frappe.clear_cache()
print("All translations updated and cache cleared successfully!")
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/sync_trans.py', 'wb') as f:
    f.write(sync_translations_py.encode('utf-8'))

cmd1 = "docker cp /tmp/sync_trans.py erpnext16:/tmp/sync_trans.py"
cmd2 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/sync_trans.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd2)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

sftp.close()
ssh.close()
