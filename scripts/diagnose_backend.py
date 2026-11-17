"""
Scam Shield backend diagnostic script.
Signs up a random test user, logs in, POSTs /checks (1 AI call),
GETs /checks, then deletes the test user.
Prints only: status codes + JSON bodies. Never prints tokens, passwords, or keys.
"""

import json
import random
import string
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

def request(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            try:
                body_resp = json.loads(resp.read())
            except Exception:
                body_resp = None
            return status, body_resp
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body_resp = json.loads(e.read())
        except Exception:
            body_resp = None
        return status, body_resp
    except urllib.error.URLError as e:
        print(f"\n[FATAL] Cannot connect to {BASE}. Is FastAPI running?")
        print(f"        Error: {e.reason}")
        sys.exit(1)

# --- Check server is up ---
print("=== STEP 0: Health check ===")
s, b = request("GET", "/health")
print(f"GET /health -> {s}: {b}")
if s != 200:
    print("Server is not healthy. Stopping.")
    sys.exit(1)

# --- DB health ---
print("\n=== STEP 0b: DB health ===")
s, b = request("GET", "/health/db")
print(f"GET /health/db -> {s}: {b}")

# --- Signup ---
suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
email = f"test-diag-{suffix}@example.com"
print(f"\n=== STEP 1: Signup ({email}) ===")
s, b = request("POST", "/auth/signup", {"email": email, "password": "DiagPass123!"})
print(f"POST /auth/signup -> {s}: {json.dumps(b)}")
if s not in (200, 201):
    print("Signup failed. Stopping.")
    sys.exit(1)

# --- Login ---
print("\n=== STEP 2: Login ===")
s, b = request("POST", "/auth/login", {"email": email, "password": "DiagPass123!"})
print(f"POST /auth/login -> {s}: (token_type={b.get('token_type') if b else None})")
if s != 200 or not b or not b.get("access_token"):
    print("Login failed. Stopping.")
    sys.exit(1)
token = b["access_token"]   # kept in memory only, never printed

# --- POST /checks (1 AI call) ---
print("\n=== STEP 3: POST /checks ===")
sample = (
    "URGENT: Your HDFC Bank account has been temporarily locked due to suspicious activity. "
    "Click http://bit.ly/hdfcsecure to verify your identity and restore access immediately. "
    "Failure to act within 2 hours will result in permanent account closure."
)
s, b = request("POST", "/checks", {"message_text": sample}, token=token)
print(f"POST /checks -> {s}")
if b:
    # Print full body but mask nothing (no secrets in response)
    print(json.dumps(b, indent=2, default=str))
check_id = b.get("id") if b and s == 201 else None

# --- GET /checks ---
print("\n=== STEP 4: GET /checks ===")
s, b = request("GET", "/checks", token=token)
print(f"GET /checks -> {s}: {len(b) if isinstance(b, list) else b} items")

# --- Cleanup: delete the test check if created ---
if check_id:
    print(f"\n=== STEP 5a: DELETE /checks/{check_id} ===")
    s, b = request("DELETE", f"/checks/{check_id}", token=token)
    print(f"DELETE /checks/{check_id} -> {s}")

# --- Cleanup: delete test user (try endpoint; note if missing) ---
print("\n=== STEP 5b: DELETE test user ===")
s, b = request("DELETE", "/auth/me", token=token)
if s == 404:
    print(f"NOTE: DELETE /auth/me endpoint does not exist (404). Test user '{email}' remains in DB.")
    print("      It will be cleaned up separately.")
else:
    print(f"DELETE /auth/me -> {s}: {b}")

print("\n=== DIAGNOSIS COMPLETE ===")
