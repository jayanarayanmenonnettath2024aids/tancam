import requests
import json

base_url = "http://localhost:5006/api"

try:
    login_res = requests.post(f"{base_url}/auth/login", json={"email":"admin@unifyops.com","password":"admin123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("=== NLP Query Test ===")
    query_res = requests.post(f"{base_url}/query", json={"query":"top 5 customers by value"}, headers=headers)
    print(json.dumps(query_res.json(), indent=2))

    print("\n=== Compliance Alerts Test ===")
    alerts_res = requests.get(f"{base_url}/compliance/alerts", headers=headers)
    print(json.dumps(alerts_res.json(), indent=2))

    print("\n=== Pipeline Status Test ===")
    status_res = requests.get(f"{base_url}/pipeline/status", headers=headers)
    print(json.dumps(status_res.json(), indent=2))

except Exception as e:
    print("Error:", e)
