import numpy as np
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta, timezone
from pathlib import Path
import joblib
from src.orbit.avoidance import optimize_maneuver


# ==========================================================
# 📦 Загрузка ML модели
# ==========================================================

MODEL_PATH = Path("src/risk/collision_risk_model.pkl")

risk_ai = None
if MODEL_PATH.exists():
    risk_ai = joblib.load(MODEL_PATH)


# ==========================================================
# 📏 Distance
# ==========================================================

def distance_km(r1, r2):
    return np.linalg.norm(np.array(r1) - np.array(r2))


# ==========================================================
# 🎲 Monte Carlo
# ==========================================================

def monte_carlo_uncertainty(traj1, traj2, samples=50):

    if len(traj1) == 0:
        return 0.0

    simulations = []

    for _ in range(samples):
        noise1 = np.random.normal(0, 0.1, traj1.shape)
        noise2 = np.random.normal(0, 0.1, traj2.shape)

        d = np.linalg.norm((traj1 + noise1) - (traj2 + noise2), axis=1)
        simulations.append(np.min(d))

    return float(np.std(simulations))


# ==========================================================
# 🧠 Hybrid Risk
# ==========================================================

def final_risk_score(ai_prob, distance, rel_velocity):

    score = (
        ai_prob * 0.6 +
        (1 / (distance + 1)) * 0.3 +
        (rel_velocity / 15) * 0.1
    )

    return float(min(score, 1.0))


# ==========================================================
# 🛰 Analyze
# ==========================================================

def analyze_collision(sat1, sat2, minutes=180, step=2):

    traj1 = []
    traj2 = []
    velocities1 = []
    velocities2 = []

    # ==========================================
    # 🚀 Берём epoch спутника
    # ==========================================

    jd_epoch = sat1.jdsatepoch
    fr_epoch = sat1.jdsatepochF

    for i in range(0, minutes, step):

        # минуты → доля суток
        fr = fr_epoch + (i / 1440.0)
        jd = jd_epoch

        # 🔥 НОРМАЛИЗАЦИЯ JD/FR (ОБЯЗАТЕЛЬНО)
        if fr >= 1.0:
            add_days = int(fr)
            jd += add_days
            fr -= add_days

        try:
            e1, r1, v1 = sat1.sgp4(jd, fr)
            e2, r2, v2 = sat2.sgp4(jd, fr)
        except Exception:
            continue

        if e1 != 0 or e2 != 0:
            continue

        traj1.append(r1)
        traj2.append(r2)
        velocities1.append(v1)
        velocities2.append(v2)

    # ==========================================
    # Если нет точек — fallback орбита
    # ==========================================

    if len(traj1) == 0:

        theta = np.linspace(0, 2*np.pi, 300)
        r = 6771  # ~400 км высота

        traj1 = np.column_stack([
            r*np.cos(theta),
            r*np.sin(theta),
            np.zeros_like(theta)
        ])

        traj2 = traj1 * 1.01

        velocities1 = np.zeros_like(traj1)
        velocities2 = np.zeros_like(traj2)

    else:
        traj1 = np.array(traj1)
        traj2 = np.array(traj2)
        velocities1 = np.array(velocities1)
        velocities2 = np.array(velocities2)

    # ==========================================
    # Минимальное расстояние
    # ==========================================

    distances = np.linalg.norm(traj1 - traj2, axis=1)
    idx = np.argmin(distances)

    min_distance = float(distances[idx])
    time_min = idx * step

    relative_velocity = float(
        np.linalg.norm(velocities1[idx] - velocities2[idx])
    )

    uncertainty = monte_carlo_uncertainty(traj1, traj2)

    # ==========================================
    # ML модель
    # ==========================================

    ai_probability = 0.0
    if risk_ai is not None:
        try:
            features = np.array(
                [[min_distance, time_min, relative_velocity, uncertainty]],
                dtype=float
            )
            ai_probability = float(
                risk_ai.predict_proba(features)[0][1]
            )
        except Exception:
            ai_probability = 0.0

    hybrid_score = final_risk_score(
        ai_probability,
        min_distance,
        relative_velocity
    )

    if min_distance < 1:
        fallback_risk = "CRITICAL"
    elif min_distance < 5:
        fallback_risk = "HIGH"
    elif min_distance < 10:
        fallback_risk = "MEDIUM"
    else:
        fallback_risk = "LOW"

    # ==========================================
    # Манёвр
    # ==========================================

    try:
        maneuver = optimize_maneuver(
            traj1,
            traj2,
            velocities1
        )
    except Exception:
        maneuver = None

    if maneuver:
        improvement = maneuver["new_min_distance"] - min_distance
        optimized_trajectory = maneuver["optimized_trajectory"]
        delta_v = maneuver["delta_v_magnitude"]
        burn_index = maneuver.get("burn_index", None)
    else:
        improvement = 0.0
        optimized_trajectory = None
        delta_v = 0.0
        burn_index = None

    return {
        "trajectory_1": traj1,
        "trajectory_2": traj2,
        "velocities_1": velocities1,
        "velocities_2": velocities2,
        "distance_km": min_distance,
        "time_min": time_min,
        "relative_velocity": relative_velocity,
        "uncertainty": uncertainty,
        "ai_probability": ai_probability,
        "hybrid_score": hybrid_score,
        "fallback_risk": fallback_risk,
        "optimized_trajectory": optimized_trajectory,
        "delta_v": delta_v,
        "burn_index": burn_index,
        "improvement_km": float(improvement)
    }
