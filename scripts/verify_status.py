import requests

tests = [
    ("Frontend Web UI", "http://localhost:3000"),
    ("Backend Root API", "http://127.0.0.1:8001/"),
    ("Backend Health Check", "http://127.0.0.1:8001/api/health"),
    ("Swagger API Docs", "http://127.0.0.1:8001/docs"),
    ("Hospital Dashboard API", "http://127.0.0.1:8001/api/dashboard/hospital"),
    ("Insurance Dashboard API", "http://127.0.0.1:8001/api/dashboard/insurance"),
    ("Patient List API", "http://127.0.0.1:8001/api/patients?limit=5"),
    ("Patient Detail API (P-1000)", "http://127.0.0.1:8001/api/patients/P-1000"),
    ("Patient Journey Events API", "http://127.0.0.1:8001/api/patients/P-1000/journey"),
    ("ML Model Metadata API", "http://127.0.0.1:8001/api/model/info"),
]

print(f"{'Service / Endpoint':<30} | {'Status Code':<12} | {'Result Detail'}")
print("-" * 80)
all_ok = True
for name, url in tests:
    try:
        r = requests.get(url, timeout=5)
        detail = "OK"
        if r.headers.get("content-type", "").startswith("application/json"):
            data = r.json()
            if "patients" in data and isinstance(data["patients"], list):
                detail = f"{len(data['patients'])} patients retrieved"
            elif "total_patients" in data:
                detail = f"Total Patients: {data['total_patients']}"
            elif "events" in data:
                detail = f"{len(data['events'])} journey events loaded"
            elif "status" in data:
                detail = f"Status: {data['status']}"
            elif "name" in data:
                detail = f"Patient: {data['name']}, Risk: {data.get('risk')}"
        status_str = f"HTTP {r.status_code}"
        print(f"{name:<30} | {status_str:<12} | {detail}")
        if r.status_code != 200:
            all_ok = False
    except Exception as e:
        print(f"{name:<30} | FAILED       | {e}")
        all_ok = False

print("-" * 80)
if all_ok:
    print("ALL SERVICES AND ENDPOINTS ARE WORKING PERFECTLY! (10/10)")
else:
    print("SOME CHECKS FAILED.")
