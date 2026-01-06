import requests
import json

# Test the platform API
base_url = 'http://localhost:5001'

def get_json(url):
    r = requests.get(url)
    print("GET", url, "->", r.status_code, r.headers.get("Content-Type"))
    if r.text:
        print("Body:", r.text[:200])
    try:
        return r.json()
    except Exception:
        return None

health_json = get_json(f"{base_url}/api/health")
print("Parsed JSON:", health_json)

from test_lambda_fl import run_federated_round_on_lambda
print("\nTriggering real FL training...")
round_id, results = run_federated_round_on_lambda(num_clients=3)

print("\n✅ Platform API connected to your FL system!")
print(f"Round {round_id} completed with {len(results)} clients")