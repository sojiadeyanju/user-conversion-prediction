import pandas as pd
import numpy as np
import datetime as dt
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import os

# --- CONFIGURATION ---
DATA_PATH = 'data/online_retail_II.xlsx'  # Path to your dataset
MODELS_DIR = 'models'                # Directory to save models
HOLDOUT_DAYS = 90                    # Days to hold out for testing/target calculation


def load_and_clean_data(filepath):
    """Loads data and performs basic cleaning."""
    print(f"Loading data from {filepath}...")

    # Check if file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Could not find {filepath}. Please ensure the dataset is in the project folder.")

    # Load Data (handling Excel or CSV)
    if filepath.endswith('.xlsx'):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    # Basic Cleaning
    df = df.dropna(subset=['Customer ID'])  # We need ID to track users
    df = df[df['Quantity'] > 0]            # Remove returns/cancellations
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['TotalSum'] = df['Quantity'] * df['Price']

    print(f"Data loaded: {len(df)} transactions found.")
    return df


def feature_engineering(df):
    """Transforms raw transactions into RFM features (one row per customer)."""
    print("Engineering features...")

    # We simulate a 'current date' based on the dataset to create targets
    cutoff_date = df['InvoiceDate'].max() - dt.timedelta(days=HOLDOUT_DAYS)

    # Split: History (Features) vs Future (Target)
    history_df = df[df['InvoiceDate'] <= cutoff_date]
    future_df = df[df['InvoiceDate'] > cutoff_date]

    # --- 1. Create Features (RFM) ---
    print("Calculating RFM features...")
    # Group by CustomerID
    features = history_df.groupby('Customer ID').agg({
        'InvoiceDate': lambda x: (cutoff_date - x.max()).days,  # Recency
        'Invoice': 'nunique',                                  # Frequency
        'TotalSum': 'sum',                                       # Monetary
        'Quantity': 'mean'                                      # Avg Basket Size
    }).rename(columns={
        'InvoiceDate': 'Recency',
        'Invoice': 'Frequency',
        'TotalSum': 'Monetary',
        'Quantity': 'AvgBasketSize'
    })

    # --- 2. Create Targets ---
    print("Calculating targets...")
    targets = future_df.groupby('Customer ID').agg({'InvoiceDate': 'min'})
    targets['NextPurchaseDay'] = (targets['InvoiceDate'] - cutoff_date).dt.days

    # Merge Targets into Features
    # logic: left join keeps all historical customers, even if they didn't buy in future
    data = features.merge(targets['NextPurchaseDay'],
                          on='Customer ID', how='left')

    # Target 1: Who? (Binary: Did they buy in the holdout period?)
    data['WillConvert'] = data['NextPurchaseDay'].notnull().astype(int)

    # Target 2: When? (Regression: Days to purchase)
    # Fill non-converters with a high number (e.g., 999) to indicate "far future"
    data['DaysToNextPurchase'] = data['NextPurchaseDay'].fillna(999)

    # Fill NaN values (customers with no history in the period - rarely happens here)
    data = data.fillna(0)

    print(f"Feature engineering complete. Dataset shape: {data.shape}")
    return data


def train_models(data):
    """Trains the Classifier (Who) and Regressor (When)."""
    print("Training models...")

    # Inputs
    features_cols = ['Recency', 'Frequency', 'Monetary']
    X = data[features_cols]
    y_who = data['WillConvert']
    y_when = data['DaysToNextPurchase']

    # Split
    X_train, X_test, y_train_who, y_test_who, y_train_when, y_test_when = train_test_split(
        X, y_who, y_when, test_size=0.2, random_state=42
    )

    # --- Model 1: WHO (Classifier) ---
    print("Training Classifier (Who)...")
    clf = XGBClassifier(n_estimators=100, learning_rate=0.05,
                        max_depth=3, eval_metric='logloss')
    clf.fit(X_train, y_train_who)

    # Quick Eval
    preds_who = clf.predict(X_test)
    acc = accuracy_score(y_test_who, preds_who)
    print(f"Classifier Accuracy: {acc:.2%}")

    # --- Model 2: WHEN (Regressor) ---
    print("Training Regressor (When)...")
    # Only train on people who actually converted (to learn the timing pattern)
    mask_train = y_train_when < 999
    reg = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=3)
    reg.fit(X_train[mask_train], y_train_when[mask_train])

    # Quick Eval (only on converters)
    mask_test = y_test_when < 999
    if mask_test.sum() > 0:
        preds_when = reg.predict(X_test[mask_test])
        mae = mean_absolute_error(y_test_when[mask_test], preds_when)
        print(f"Regressor MAE (Avg Error in Days): {mae:.1f} days")

    return clf, reg


def save_models(clf, reg):
    """Saves models with compression to keep Docker image small."""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    print(f"Saving models to {MODELS_DIR}...")

    # IMPORTANT: compress=3 reduces file size significantly
    joblib.dump(clf, os.path.join(
        MODELS_DIR, 'churn_classifier.joblib'), compress=3)
    joblib.dump(reg, os.path.join(
        MODELS_DIR, 'days_regressor.joblib'), compress=3)

    print("Models saved successfully.")


if __name__ == "__main__":
    try:
        # 1. Load
        # NOTE: Ensure you have 'online_retail_II.xlsx' in the folder,
        # or change this to a sample CSV generation script if you don't have data yet.
        df = load_and_clean_data(DATA_PATH)

        # 2. Engineer
        data = feature_engineering(df)

        # 3. Train
        clf, reg = train_models(data)

        # 4. Save
        save_models(clf, reg)

    except Exception as e:
        print(f"\nERROR: {e}")
