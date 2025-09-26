# Simple/train a synthetic sklearn model and save to models/fraud_model.pkl
import os
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
import numpy as np

OUT = Path(__file__).resolve().parents[1] / "models"
OUT.mkdir(parents=True, exist_ok=True)
X = []
y = []
for i in range(500):
    vec = list((np.random.randint(0, 128, size=5)).tolist())
    mean = float(np.mean(vec))
    var = float(np.var(vec))
    ln = float(np.random.randint(1, 30))
    feat = vec + [mean, var, ln]
    X.append(feat)
    y.append(1 if np.random.random() < 0.15 else 0)

clf = RandomForestClassifier(n_estimators=50, random_state=42)
clf.fit(X, y)
joblib.dump(clf, OUT / "fraud_model.pkl")
print("Saved synthetic model to", str(OUT / "fraud_model.pkl"))
