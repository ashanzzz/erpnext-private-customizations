import os
import pymysql

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

conn = pymysql.connect(
    host="192.168.8.11",
    port=3306,
    user="erpnext16",
    password=os.environ["MARIADB_PASSWORD"],
    database="erpnext16",
    charset="utf8mb4"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM `tabWorkspace Number Card` WHERE name = 'gf33m8c3eq'")
rows = cursor.fetchall()
print("Rows with gf33m8c3eq:", rows)

# Delete all orphan workspace number cards / shortcuts / links where parent is Ashan workspaces
cursor.execute("DELETE FROM `tabWorkspace Number Card`")
cursor.execute("DELETE FROM `tabWorkspace Shortcut` WHERE parent IN ('My Business', 'Procurement Management', 'Stock and Inventory', 'Accounting and Finance', 'Vehicle Fuel Hub', 'Company Compliance Center')")
cursor.execute("DELETE FROM `tabWorkspace Link` WHERE parent IN ('My Business', 'Procurement Management', 'Stock and Inventory', 'Accounting and Finance', 'Vehicle Fuel Hub', 'Company Compliance Center')")
cursor.execute("DELETE FROM `tabWorkspace` WHERE name IN ('Ashan CN Procurement', '查看所有物料')")
cursor.execute("UPDATE `tabWorkspace` SET hide_custom = 1 WHERE module = 'Ashan CN Procurement'")
conn.commit()
print("Successfully cleaned database workspace tables!")
conn.close()

