"""Barcha API endpointlarni tekshirish."""
import urllib.request
import json
import sys

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

results = []

def check(name, status, ok_status=200):
    ok = status == ok_status
    results.append((name, ok, status))
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}: {status}")

print("=" * 50)
print("MARKAZ PLATFORMASI - API TEST")
print("=" * 50)

# 1. Director
print("\n--- DIRECTOR ---")
d, s = req("POST", "/auth/login", {"phone": "+998900000002", "password": "admin123"})
check("Login", s)
tok = d.get("access_token", "")

d, s = req("GET", "/director/dashboard", token=tok)
check("Dashboard", s)
print(f"      teachers={d.get('teachers_count')}, students={d.get('students_count')}, courses={d.get('courses_count')}")

d, s = req("GET", "/director/teachers", token=tok)
check("Teachers list", s)

d, s = req("GET", "/director/courses", token=tok)
check("Courses list", s)

d, s = req("GET", "/director/groups", token=tok)
check("Groups list", s)

# 2. Reception
print("\n--- RECEPTION ---")
d, s = req("POST", "/auth/login", {"phone": "+998900000003", "password": "admin123"})
check("Login", s)
tok = d.get("access_token", "")

d, s = req("GET", "/reception/students", token=tok)
check("Students list", s)

d, s = req("GET", "/reception/groups", token=tok)
check("Groups list", s)

# 3. Teacher
print("\n--- TEACHER ---")
d, s = req("POST", "/auth/login", {"phone": "+998900000004", "password": "admin123"})
check("Login", s)
tok = d.get("access_token", "")

d, s = req("GET", "/teacher/my-groups", token=tok)
check("My Groups", s)

# 4. Student
print("\n--- STUDENT ---")
d, s = req("POST", "/auth/login", {"phone": "+998900000005", "password": "admin123"})
check("Login", s)
tok = d.get("access_token", "")

d, s = req("GET", "/student/me", token=tok)
check("Profile", s)

d, s = req("GET", "/student/my-groups", token=tok)
check("My Groups", s)

d, s = req("GET", "/student/attendance", token=tok)
check("Attendance", s)

d, s = req("GET", "/student/tasks", token=tok)
check("Tasks", s)

d, s = req("GET", "/student/bonuses", token=tok)
check("Bonuses", s)

d, s = req("GET", "/student/payments", token=tok)
check("Payments", s)

# 5. SuperAdmin
print("\n--- SUPERADMIN ---")
d, s = req("POST", "/auth/login", {"phone": "+998900000001", "password": "admin123"})
check("Login", s)
tok = d.get("access_token", "")

d, s = req("GET", "/superadmin/stats", token=tok)
check("Stats", s)

d, s = req("GET", "/superadmin/directors", token=tok)
check("Directors", s)

# Summary
print("\n" + "=" * 50)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"NATIJA: {passed} muvaffaqiyatli, {failed} xato")
if failed == 0:
    print("BARCHA TESTLAR MUVAFFAQIYATLI!")
else:
    print("BA'ZI TESTLAR XATO!")
    for name, ok, status in results:
        if not ok:
            print(f"  XATO: {name} -> {status}")
print("=" * 50)
