import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_multilingual():
    print("\nTesting Multilingual Input (Hindi)...")
    payload = {"text": "बुखार", "lang": "hi"}
    try:
        response = requests.post(f"{BASE_URL}/validate", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}") # Should match 'fever'
    except Exception as e:
        print(f"Error: {e}")

def test_precautions_display():
    print("\nTesting Precautions Display...")
    # Using confirmed symptom from previous steps
    payload = {"symptoms": ["viral fever"]} # Direct key usage for test
    try:
        # Predict using direct symptoms list bypasses validation for quick check
        # But our predict expects a list of validated symptoms.
        # Let's use the one we know works: 'fever' -> maps to 'viral fever' maybe?
        # Actually predict takes a list of symptoms.
        # Let's send ["fever", "headache", "chills"] which maps to Viral Fever
        payload = {"symptoms": ["fever", "headache", "chills"]}
        response = requests.post(f"{BASE_URL}/predict", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        if 'precautions' in data:
            print(f"Precautions provided: {len(data['precautions'])}")
            print(data['precautions'])
        else:
            print("No precautions found in response.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_multilingual()
    test_precautions_display()
