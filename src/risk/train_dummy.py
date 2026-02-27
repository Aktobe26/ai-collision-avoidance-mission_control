import numpy as np
import collections
import joblib
from src.risk.risk_model import CollisionRiskModel

np.random.seed(42)

X, y = [], []

for _ in range(3000):
    distance = np.random.uniform(0.1, 2000)
    time = np.random.uniform(1, 360)
    velocity = np.random.uniform(1, 15)
    uncertainty = np.random.uniform(0.1, 5)

    risk = int(
        distance < 20 and
        time < 120 and
        velocity > 5
    )

    X.append([distance, time, velocity, uncertainty])
    y.append(risk)

print("Распределение классов:", collections.Counter(y))

model = CollisionRiskModel()
model.train(X, y)

# 💾 сохраняем модель
joblib.dump(model, "src/risk/collision_risk_model.pkl")

print("✅ ML-модель сохранена: collision_risk_model.pkl")
