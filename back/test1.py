import requests

url = "http://127.0.0.1:5000/portfolio/buy-stocks"  # Update if needed
response = requests.get(url)

print("Status Code:", response.status_code)
print("Response Text:", response.text)

try:
    data = response.json()
    print("JSON Response:", data)
except requests.exceptions.JSONDecodeError:
    print("Error: Response is not JSON format.")
