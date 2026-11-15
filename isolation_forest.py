
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Load dataset
data = pd.read_csv("dataset/sensor_data.csv")

features = ["gas_response", "temperature", "humidity"]
X = data[features]

# Standardize sensor features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train Isolation Forest
model = IsolationForest(
    n_estimators=100,
    contamination="auto",
    random_state=42
)

model.fit(X_scaled)

# Predict anomalies
data["anomaly_result"] = model.predict(X_scaled)

data["anomaly_status"] = data["anomaly_result"].map({
    -1: "ANOMALY",
    1: "NORMAL"
})

# Display results
print("\n===== STANDARDIZED ISOLATION FOREST =====")
print(data["anomaly_status"].value_counts())

print("\nComparison with programmed labels:")
print(pd.crosstab(data["status"], data["anomaly_status"]))

# Save output
data.to_csv(
    "dataset/isolation_forest_results_scaled.csv",
    index=False
)

print("\nSaved standardized results successfully.")
