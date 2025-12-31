import os
from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np

app = Flask(__name__)

# 1. Load Models at Startup
# We load them globally so we don't have to reload them for every single request
print("Loading models...")
clf = joblib.load('models/churn_classifier.joblib')
reg = joblib.load('models/days_regressor.joblib')
print("Models loaded.")

# 2. Define the 'Next Best Action' Logic


def determine_action(prob, days_to_buy, value):
    if prob > 0.8 and value > 2000:
        return f"VIP ALERT: Send Early Access Catalog. (Expected buy in {int(days_to_buy)} days)"
    elif prob > 0.8:
        return "PROMO: Send 'Bundle Discount' to increase basket size."
    elif prob < 0.3 and value > 2000:
        return "RISK: High Value Churn Risk! Trigger Personal Outreach."
    elif prob > 0.5 and days_to_buy < 7:
        return "URGENCY: Send 'Free Shipping for 48 Hours' nudge."
    else:
        return "NURTURE: Add to General Newsletter."

# 3. Define the API Endpoint


@app.route('/predict_action', methods=['POST'])
def predict_action():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Expecting input: {"Recency": 10, "Frequency": 5, "Monetary": 500}
        # Convert to DataFrame (required by XGBoost/Scikit-Learn)
        features = pd.DataFrame(
            [data], columns=['Recency', 'Frequency', 'Monetary'])

        # Make Predictions
        prob_convert = clf.predict_proba(
            features)[0][1]  # Probability of Class 1
        days_estimate = reg.predict(features)[0]

        # Determine Marketing Action
        action = determine_action(
            prob_convert, days_estimate, data['Monetary'])

        # Return Result
        response = {
            "probability_to_convert": round(float(prob_convert), 4),
            "estimated_days_to_buy": round(float(days_estimate), 1),
            "recommended_action": action
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 4. Run the App
if __name__ == '__main__':
    # Uncomment for local testing
    # app.run(debug=True, host='0.0.0.0', port=5001)

    # Get the PORT from Google Cloud, or default to 5001 locally
    port = int(os.environ.get('PORT', 5001))

    # Disable debug mode for production
    app.run(debug=False, host='0.0.0.0', port=port)
