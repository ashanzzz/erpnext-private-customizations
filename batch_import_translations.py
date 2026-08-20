# -*- coding: utf-8 -*-
import os
import csv
import io
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

# 1. 读取本地 user_translations.csv
csv_path = r"d:\SynologyDrive团队\antigravity\erpnext16\user_translations.csv"
translations_to_import = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    # Header: ID, Language, Source Text, Translated Text, Contributed, Contribution Status, Contribution Document Name, Context
    for row in reader:
        if len(row) >= 4:
            lang = row[1].strip() or 'zh'
            source = row[2]
            trans = row[3]
            context = row[7].strip() if len(row) > 7 else ""
            if source:
                translations_to_import.append({
                    "language": lang,
                    "source_text": source,
                    "translated_text": trans,
                    "context": context
                })

print(f"Total parsed translations: {len(translations_to_import)}")

# 2. 同时更新本地 App translations/zh.csv
app_zh_csv = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\translations\zh.csv"
with open(app_zh_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    for item in translations_to_import:
        if item.get("context"):
            writer.writerow([item["source_text"], item["translated_text"], item["context"]])
        else:
            writer.writerow([item["source_text"], item["translated_text"]])

print(f"Updated local app translation file: {app_zh_csv}")

# 3. 编写 Docker 内执行的导入脚本
import_script = """# -*- coding: utf-8 -*-
import json
import frappe

frappe.init(site='site1.local', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

with open('/tmp/translations_payload.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

inserted = 0
updated = 0

for item in items:
    lang = item.get('language') or 'zh'
    source = item.get('source_text')
    trans = item.get('translated_text')
    context = item.get('context') or None

    filters = {'source_text': source, 'language': lang}
    if context:
        filters['context'] = context
    
    existing = frappe.db.get_value('Translation', filters, 'name')
    if existing:
        doc = frappe.get_doc('Translation', existing)
        doc.translated_text = trans
        doc.save(ignore_permissions=True)
        updated += 1
    else:
        doc = frappe.get_doc({
            'doctype': 'Translation',
            'language': lang,
            'source_text': source,
            'translated_text': trans,
            'context': context
        })
        doc.insert(ignore_permissions=True)
        inserted += 1

frappe.db.commit()
frappe.clear_cache()

print(f"[OK] Successfully imported translations: {inserted} inserted, {updated} updated, total {len(items)}")
"""

# 4. SSH 连接并执行
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)
sftp = ssh.open_sftp()

import json
with sftp.open('/tmp/translations_payload.json', 'wb') as f:
    f.write(json.dumps(translations_to_import, ensure_ascii=False).encode('utf-8'))

with sftp.open('/tmp/run_import_translations.py', 'wb') as f:
    f.write(import_script.encode('utf-8'))

cmd1 = "docker cp /tmp/translations_payload.json erpnext16:/tmp/translations_payload.json"
cmd2 = "docker cp /tmp/run_import_translations.py erpnext16:/tmp/run_import_translations.py"
cmd3 = "docker exec -u frappe -w /home/frappe/frappe-bench/sites erpnext16 /home/frappe/frappe-bench/env/bin/python3 /tmp/run_import_translations.py"

ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()
stdin, stdout, stderr = ssh.exec_command(cmd3)

out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("OUTPUT:\n", out)
if err:
    print("STDERR:\n", err)

# 5. 复制 zh.csv 到容器内 app 的 translations 目录
sftp.put(app_zh_csv, "/tmp/zh.csv")
cmd_copy_csv = "docker cp /tmp/zh.csv erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/translations/zh.csv"
ssh.exec_command(cmd_copy_csv)[1].channel.recv_exit_status()

sftp.close()
ssh.close()
print("All tasks completed successfully!")
