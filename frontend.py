import streamlit as st
import requests
import json

# --- CONFIGURATION ---
# PASTE YOUR GOOGLE CLOUD RUN URL HERE
API_URL = "https://conversion-api-service-xyz.a.run.app/predict_action"

# --- PAGE SETUP ---
st.set_page_config(page_title="Customer AI Prediction", page_icon="🛍️")

st.title("🛍️ Customer Conversion Predictor")
st.markdown("""
This tool uses **Machine Learning** to predict if a customer will buy in the next 30 days 
and recommends the **Next Best Action**.
""")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Customer Profile")

recency = st.sidebar.slider(
    "Recency (Days since last buy)",
    min_value=0,
    max_value=365,
    value=30,
    help="How many days ago was their last purchase?"
)

frequency = st.sidebar.slider(
    "Frequency (Total # of purchases)",
    min_value=1,
    max_value=100,
    value=5,
    help="How many times have they bought from us historically?"
)

monetary = st.sidebar.number_input(
    "Monetary (Total Lifetime Spend $)",
    min_value=0,
    max_value=50000,
    value=1000,
    step=100
)

# --- PREDICTION LOGIC ---
if st.button("🔮 Predict Customer Action", type="primary"):

    # 1. Prepare Payload
    payload = {
        "Recency": recency,
        "Frequency": frequency,
        "Monetary": monetary
    }

    # 2. Call API with Spinner
    with st.spinner("Asking the AI brain..."):
        try:
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                result = response.json()

                # --- DISPLAY RESULTS ---
                st.divider()

                # Metrics Columns
                col1, col2, col3 = st.columns(3)

                prob = result['probability_to_convert']
                days = result['estimated_days_to_buy']

                with col1:
                    st.metric("Probability", f"{prob:.1%}")

                with col2:
                    st.metric("Days to Buy", f"{days} days")

                with col3:
                    # Logic to color-code the "Risk"
                    if prob > 0.7:
                        st.success("High Intent")
                    elif prob < 0.3:
                        st.error("Churn Risk")
                    else:
                        st.warning("Neutral")

                # The Big Action Banner
                st.subheader("🚀 Recommended Action")
                st.info(f"**{result['recommended_action']}**")

                # Raw JSON (Optional debug)
                with st.expander("See Raw API Response"):
                    st.json(result)

            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Connection Failed: {e}")
            st.caption("Did you paste the correct Cloud Run URL in the script?")
