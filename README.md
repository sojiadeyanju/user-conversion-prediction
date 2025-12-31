# 🛍️ End-to-End Customer Conversion Prediction System

This project is a full-stack Machine Learning application that predicts customer purchasing behavior using the **UCI Online Retail II dataset**. It identifies **who** is likely to convert, **when** they will buy next, and automatically recommends the **next best marketing action**.

**Project Architecture:**
`Excel Data` → `Python Training (XGBoost)` → `Flask API` → `Docker Container` → `Google Cloud Run` → `Streamlit Dashboard`

---

## 📂 Project Structure

```text
conversion-prediction/
├── models/                     # Saved ML models (Created by train.py)
│   ├── churn_classifier.joblib # XGBClassifier (Who)
│   └── days_regressor.joblib   # XGBRegressor (When)
├── app.py                      # Flask API for serving predictions
├── train.py                    # Script to load data, train models, and save them
├── frontend.py                 # Streamlit Dashboard for user interaction
├── test_api.py                 # Script to test the API (Local or Cloud)
├── Dockerfile                  # Instructions to build the container
├── .dockerignore               # Prevents large files from bloating the image
├── user_conversion.ipynb       # Jupyter Notebook
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation


```

---

## 🛠️ Prerequisites

* **Python 3.9+**
* **Docker Desktop** (for containerization)
* **Google Cloud SDK** (for deployment)
* **Dataset:** Download the `online_retail_II.xlsx` file from the [UCI ML Repository](https://archive.ics.uci.edu/ml/datasets/Online+Retail+II) and place it in the root folder.

---

## 🚀 Phase 1: Local Setup & Training

### 1. Install Dependencies

It is recommended to use a virtual environment.

```bash
# Create virtual env
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install libraries
pip install -r requirements.txt

```

### 2. Train the Models

Run the training script to process the raw Excel data, engineer RFM features, and train the XGBoost models.

```bash
python train.py

```

* **Output:** Creates `models/churn_classifier.joblib` and `models/days_regressor.joblib`.
* *Note:* Models are compressed (`compress=3`) to ensure the Docker image remains small.

---

## 🐳 Phase 2: Docker Containerization

### 1. Build the Image

We use a multi-stage build (or optimized single stage) to keep the image size under 1GB.

```bash
docker build -t conversion-api .

```

### 2. Run the Container Locally

```bash
docker run -p 5001:5001 conversion-api

```

The API is now active at `http://localhost:5001/predict_action`.

---

## ☁️ Phase 3: Cloud Deployment (Google Cloud Run)

### 1. Tag & Push to Artifact Registry

Replace `your-project-id` with your actual GCP Project ID.

```bash
# 1. Login to Google Cloud
gcloud auth login
gcloud config set project your-project-id

# 2. Configure Docker Auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Tag the image
docker tag conversion-api us-central1-docker.pkg.dev/your-project-id/my-models/conversion-api

# 4. Push to Cloud
docker push us-central1-docker.pkg.dev/your-project-id/my-models/conversion-api

```

### 2. Deploy Service

```bash
gcloud run deploy conversion-api-service \
    --image us-central1-docker.pkg.dev/your-project-id/my-models/conversion-api \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi

```

**Result:** You will receive a public URL (e.g., `https://conversion-api-service-xyz.a.run.app`).

---

## 💻 Phase 4: Usage

### 1. Frontend Dashboard (Streamlit)

To visualize the model's predictions with an interactive UI:

1. Open `frontend.py`.
2. Update `API_URL` with your **Cloud Run URL** (or localhost if testing locally).
3. Run the app:
```bash
streamlit run frontend.py

```



### 2. API Usage (cURL / Postman)

**Endpoint:** `POST /predict_action`

**Payload:**

```json
{
    "Recency": 10,
    "Frequency": 5,
    "Monetary": 500
}

```

**Response:**

```json
{
    "probability_to_convert": 0.85,
    "estimated_days_to_buy": 5.2,
    "recommended_action": "VIP ALERT: Send Early Access Catalog."
}

```

---

## 📝 Important Notes & Troubleshooting

* **Image Size:** If the Docker image is >1.5GB, ensure your `.dockerignore` file includes `.venv`, `data/`, and `.git/`.
* **XGBoost Version:** The project uses `xgboost==1.7.6` in `requirements.txt` to avoid installing massive NVIDIA GPU drivers inside the Docker container. **Ensure your local environment matches this version** when running `train.py`.
* **Port Config:** `app.py` is configured to listen on port `5001` locally, but dynamically switches to the `PORT` environment variable (default 8080) when deployed to Google Cloud.