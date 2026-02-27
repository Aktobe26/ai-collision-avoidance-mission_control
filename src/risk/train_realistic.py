import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


MODEL_PATH = Path("src/risk/collision_risk_model.pkl")


def generate_dataset(n_samples=20000):

    distances = np.random.uniform(0.1, 2000, n_samples)
    time_min = np.random.uniform(0, 180, n_samples)
    rel_velocity = np.random.uniform(0, 15, n_samples)
    uncertainty = np.random.uniform(0, 100, n_samples)

    X = np.column_stack([
        distances,
        time_min,
        rel_velocity,
        uncertainty
    ])

    # Реалистичная формула риска
    risk_score = (
        (1 / (distances + 1)) * 5 +
        (rel_velocity / 15) * 2 +
        (uncertainty / 100) * 1
    )

    y = (risk_score > 1.2).astype(int)

    return X, y


def train():
    X, y = generate_dataset()

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4
        ))
    ])

    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)

    print("✅ Реальная ML модель обучена и сохранена.")


if __name__ == "__main__":
    train()
