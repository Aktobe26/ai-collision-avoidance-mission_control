import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


class CollisionRiskModel:
    def __init__(self):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier())
        ])

    def train(self, X, y):
        self.model.fit(X, y)

    def predict_proba(self, features):
        """
        features = [distance_km, time_min, rel_velocity, uncertainty]
        """

        # Гарантируем правильную форму (1, n_features)
        features = np.array(features, dtype=float).reshape(1, -1)

        proba = self.model.predict_proba(features)[0][1]
        return float(proba)
