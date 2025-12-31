import requests
import json

# The URL where your Flask app is running
# Localhost with port 5001 as defined in app.py
# url = 'http://127.0.0.1:5001/predict_action'

# Cloud deployment example: Google Cloud Run (Change to your actual URL)
url = 'https://conversion-api-service-xyz.a.run.app/predict_action'

# # Simulate a Customer Data Payload (RFM)
# # Example 1: A "Whale" who buys often but hasn't in a while
# customer_data = {
#     "Recency": 45,      # hasn't bought in 45 days
#     "Frequency": 12,    # bought 12 times before
#     "Monetary": 2500    # spent $2500 total
# }

# # Send the request
# response = requests.post(url, json=customer_data)

# # Print the automated decision
# print("Status Code:", response.status_code)
# print("API Response:", json.dumps(response.json(), indent=2))

# Example 2: Let's test a "High Value" customer who hasn't bought in a while
customer_data = {
    "Recency": 10,      # Bought 10 days ago (Active)
    "Frequency": 20,    # Bought 20 times (Loyal)
    "Monetary": 5000    # Spent $5000 (Whale)
}

print(f"Sending request to: {url}")

try:
    # Send the request
    response = requests.post(url, json=customer_data)

    # Check for success
    if response.status_code == 200:
        print("\n✅ SUCCESS!")
        print("API Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\n❌ Error {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"\n❌ Connection Error: {e}")
