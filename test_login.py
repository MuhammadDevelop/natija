import urllib.request
import json
import urllib.error

req = urllib.request.Request(
    'https://natija-ro6w.onrender.com/api/v1/auth/login',
    data=json.dumps({'phone': '+998931002010', 'password': 'Admin@2024'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    urllib.request.urlopen(req)
    print("Success!")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}:")
    print(e.read().decode())
except Exception as e:
    print(e)
