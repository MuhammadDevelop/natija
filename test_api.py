"""Barcha login testlari."""
import urllib.request
import json

BASE = "http://localhost:8000/api/v1"

def req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}, e.code

print("=" * 50)
print("LOGIN TESTLARI")
print("=" * 50)

# Login har bir rol uchun
roles = [
    ("SuperAdmin", "+998900000001", "admin123"),
    ("Director",   "+998900000002", "admin123"),
    ("Reception",  "+998900000003", "admin123"),
    ("Teacher1",   "+998900000004", "admin123"),
    ("Teacher2",   "+998900000010", "admin123"),
    ("Student1",   "+998900000005", "admin123"),
    ("Student2",   "+998900000006", "admin123"),
    ("Student3",   "+998900000007", "admin123"),
]

ok = 0
fail = 0
for name, phone, pwd in roles:
    d, s = req("POST", "/auth/login", {"phone": phone, "password": pwd})
    if s == 200:
        print(f"  [OK] {name}: role={d.get('role')}, name={d.get('full_name')}")
        ok += 1
    else:
        print(f"  [FAIL] {name}: status={s}, error={d}")
        fail += 1

# Register test
print("\nREGISTRATION TEST:")
d, s = req("POST", "/auth/register", {"full_name": "Test User", "phone": "+998991112233", "password": "test123"})
if s == 201:
    print(f"  [OK] Register: role={d.get('role')}, name={d.get('full_name')}")
    ok += 1
else:
    print(f"  [FAIL] Register: status={s}, error={d}")
    fail += 1

# Subjects test
print("\nSUBJECTS TEST:")
d, s = req("GET", "/auth/subjects")
if s == 200:
    print(f"  [OK] Subjects: {len(d)} ta fan")
    ok += 1
else:
    print(f"  [FAIL] Subjects: status={s}")
    fail += 1

# Director dashboard test
print("\nDIRECTOR DASHBOARD TEST:")
d, s = req("POST", "/auth/login", {"phone": "+998900000002", "password": "admin123"})
tok = d.get("access_token", "")
d, s = req("GET", "/director/dashboard", token=tok)
if s == 200:
    print(f"  [OK] Dashboard: teachers={d.get('teachers_count')}, students={d.get('students_count')}")
    ok += 1
else:
    print(f"  [FAIL] Dashboard: status={s}")
    fail += 1

print("\n" + "=" * 50)
print(f"NATIJA: {ok} OK, {fail} FAIL")
if fail == 0:
    print("BARCHA TESTLAR MUVAFFAQIYATLI!")
print("=" * 50)
