# ==============================
# train_model.py (FINAL VERSION)
# ==============================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import sys
import traceback

print("🚀 Starting CKD model training...", flush=True)

try:
    # 1️⃣ Load dataset
    DATA_PATH = "CKD_Preprocessed.csv"
    print(f"📂 Loading dataset from: {DATA_PATH}", flush=True)
    data = pd.read_csv(DATA_PATH)
    print(f"✅ Dataset loaded. Shape: {data.shape}", flush=True)

    # 2️⃣ Define features and target
    features = [
        'Age (yrs)',
        'Blood Pressure (mm/Hg)',
        'Specific Gravity',
        'Albumin',
        'Sugar',
        'Blood Glucose Random (mgs/dL)',
        'Blood Urea (mgs/dL)',
        'Serum Creatinine (mgs/dL)',
        'Hemoglobin (gms)',
        'Hypertension: yes',
        'Diabetes Mellitus: yes',
        'Anemia: yes'
    ]
    target = 'Chronic Kidney Disease: yes'

    # 3️⃣ Check columns
    missing = [c for c in features + [target] if c not in data.columns]
    if missing:
        raise ValueError(f"❌ Missing columns: {missing}")

    X = data[features]
    y = data[target].astype(int)
    print("✅ Features and target extracted.", flush=True)

    # 4️⃣ (NO MANUAL UPSAMPLING ANYMORE)

    # 5️⃣ Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"🧩 Data split: Train={len(X_train)}, Test={len(X_test)}", flush=True)

    # 6️⃣ Training pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=200,
            class_weight='balanced',  # Correct config
            random_state=42
        ))
    ])

    # 7️⃣ Train model
    pipeline.fit(X_train, y_train)
    print("✅ Model training complete!", flush=True)

    # 8️⃣ Evaluate
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n🔹 Accuracy: {acc*100:.2f}%")
    print("🔹 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
    print("🔹 Classification Report:\n", classification_report(y_test, y_pred))

    # 9️⃣ Save model
    joblib.dump(pipeline, "model.pkl")
    print("💾 Model saved as model.pkl")

    # 🔟 Feature Importance
    rf = pipeline.named_steps['rf']
    importances = rf.feature_importances_
    feat_imp = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
    print("\n🔹 Top Feature Importances:")
    for f, imp in feat_imp:
        print(f"{f}: {imp:.4f}")

    print("\n🎉 Training finished successfully.", flush=True)

except Exception as e:
    print("❌ Training failed due to error:", flush=True)
    traceback.print_exc(file=sys.stdout)
