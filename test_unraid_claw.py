import os
import json
import urllib.request

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
CLAW_URL = os.getenv('UNRAIDCLAW_URL', 'http://192.168.8.11:9876')
API_KEY = os.getenv('UNRAIDCLAW_API_KEY', '')

print("Checking UnraidClaw gateway...")
req = urllib.request.Request(f"{CLAW_URL}/containers", headers={"Authorization": f"Bearer {API_KEY}"})
try:
    with urllib.request.urlopen(req) as resp:
        print("UnraidClaw containers:", resp.read().decode('utf-8'))
except Exception as e:
    print("UnraidClaw error:", e)

