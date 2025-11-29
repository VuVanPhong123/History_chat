import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "question": "Vua Quang Trung là ai?",
        "session_id": "python_test"
    }
)

print("Status Code:", response.status_code)
print("Response:", response.json())