import requests
import json

# Test the registration endpoint
url = "http://127.0.0.1:5000/register"
headers = {'Content-Type': 'application/json'}

# Try with a new unique username and email
payload = {
    "username": "testuser123",
    "email": "testuser123@example.com",
    "password": "password123"
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")