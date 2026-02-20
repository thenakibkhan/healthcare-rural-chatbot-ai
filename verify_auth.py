import requests
import json

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def test_auth_flow():
    print("Testing Auth Flow...")
    
    # 1. Register
    email = "testuser_logout@example.com"
    password = "password123"
    name = "Test User Logout"
    
    reg_payload = {"name": name, "email": email, "password": password}
    try:
        resp = SESSION.post(f"{BASE_URL}/auth/register", json=reg_payload)
        print(f"Register: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Register Failed: {e}")
        try: print(resp.text)
        except: pass

    # 2. Login
    login_payload = {"email": email, "password": password}
    try:
        resp = SESSION.post(f"{BASE_URL}/auth/login", json=login_payload)
        print(f"Login: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"Login Failed: {e}")
        try: print(resp.text)
        except: pass

    # 3. Access Protected Route (Chat History) - Should Succeed
    try:
        resp = SESSION.get(f"{BASE_URL}/api/chat/history")
        print(f"Get History (LoggedIn): {resp.status_code}")
    except Exception as e:
        print(f"Get History Failed: {e}")
        try: print(resp.text)
        except: pass

    # 4. Logout
    try:
        resp = SESSION.get(f"{BASE_URL}/auth/logout") # It's a GET in my implementation plan? Wait, let's check auth.py
        # Actually I didn't check auth.py for logout method. Standard is often GET for simple apps or POST.
        # Let's try GET first as per common Flask-Login patterns, or check file.
        print(f"Logout: {resp.status_code}")
    except Exception as e:
        print(f"Logout Failed: {e}")
        try: print(resp.text)
        except: pass

    # 5. Access Protected Route (Chat History) - Should Fail (401 or 302 to login)
    try:
        resp = SESSION.get(f"{BASE_URL}/api/chat/history")
        print(f"Get History (LoggedOut): {resp.status_code}")
        if resp.status_code == 401 or resp.status_code == 302 or "login" in resp.url:
             print("SUCCESS: Access denied after logout.")
        else:
             print("FAILURE: Still able to access history.")
    except Exception as e:
        print(f"Get History Check Failed: {e}")
        try: print(resp.text)
        except: pass

if __name__ == "__main__":
    test_auth_flow()
