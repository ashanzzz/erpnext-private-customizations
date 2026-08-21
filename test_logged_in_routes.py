import os
import requests

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = "http://192.168.8.11:6888"
USER = os.getenv('ERPNEXT_USER', 'Administrator')
PWD = os.getenv('ERPNEXT_PASSWORD', '')

session = requests.Session()

# Login
login_res = session.post(f"{SITE_URL}/api/method/login", data={"usr": USER, "pwd": PWD})
print("Login result:", login_res.status_code, login_res.json() if login_res.status_code == 200 else login_res.text)

# Now visit /
r_root = session.get(f"{SITE_URL}/", allow_redirects=False)
print("\nLogged-in GET / -> Status:", r_root.status_code, "Location:", r_root.headers.get('Location'))

r_root_follow = session.get(f"{SITE_URL}/", allow_redirects=True)
print("Logged-in GET / (follow) -> URL:", r_root_follow.url, "Status:", r_root_follow.status_code)
if "not found" in r_root_follow.text.lower():
    print("Contains 'not found': YES!")
    print(r_root_follow.text[:600])

# Visit /my-business
r_mb = session.get(f"{SITE_URL}/my-business", allow_redirects=True)
print("\nLogged-in GET /my-business -> URL:", r_mb.url, "Status:", r_mb.status_code)
if "not found" in r_mb.text.lower():
    print("Contains 'not found': YES!")
    print(r_mb.text[:600])

# Visit /desk
r_desk = session.get(f"{SITE_URL}/desk", allow_redirects=True)
print("\nLogged-in GET /desk -> URL:", r_desk.url, "Status:", r_desk.status_code)

# Visit /desk/my-business
r_desk_mb = session.get(f"{SITE_URL}/desk/my-business", allow_redirects=True)
print("\nLogged-in GET /desk/my-business -> URL:", r_desk_mb.url, "Status:", r_desk_mb.status_code)

# Visit /app/my-business
r_app_mb = session.get(f"{SITE_URL}/app/my-business", allow_redirects=True)
print("\nLogged-in GET /app/my-business -> URL:", r_app_mb.url, "Status:", r_app_mb.status_code)

