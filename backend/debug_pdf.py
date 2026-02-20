import requests

def test_pdf_api():
    print("Testing PDF API...")
    url = "http://127.0.0.1:5000/api/report"
    
    msg_data = {
        "user_name": "Test User",
        "prediction_data": {
            "disease": "Viral Fever",
            "description": {
                "en": "Viral fever is common.",
                "hi": "वायरल फीवर आम है।",
                "ta": "வைரஸ் காய்ச்சல்."
            },
            "precautions": [
                {"en": "Rest", "hi": "आराम", "ta": "ஓய்வு"},
                {"en": "Fluids", "hi": "तरल पदार्थ", "ta": "திரவங்கள்"},
                {"en": "Meds", "hi": "दवाएं", "ta": "மருந்துகள்"}
            ],
            "severity": "Medium",
            "confidence": 95.5
        }
    }
    
    try:
        response = requests.post(url, json=msg_data)
        if response.status_code == 200:
            with open("api_report.pdf", "wb") as f:
                f.write(response.content)
            print("API PDF generated successfully: api_report.pdf")
        else:
            print(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    test_pdf_api()
