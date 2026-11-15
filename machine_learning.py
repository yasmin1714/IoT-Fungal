
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# 1. Load dataset
data = pd.read_csv("dataset/sensor_data.csv")

# 2. Convert timestamp
data["timestamp"] = pd.to_datetime(data["timestamp"])

# 3. Select input features and target
features = ["gas_response", "temperature", "humidity"]
X = data[features]
y = data["status"]

# 4. Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# 5. Train Random Forest
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced"
)

model.fit(X_train, y_train)

# 6. Predict
predictions = model.predict(X_test)

# 7. Evaluate
print("\n===== RANDOM FOREST RESULTS =====")
print("Accuracy:", accuracy_score(y_test, predictions))

print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

# 8. Feature importance
print("\nFeature Importance:")
for name, importance in zip(features, model.feature_importances_):
    print(f"{name}: {importance:.4f}")
