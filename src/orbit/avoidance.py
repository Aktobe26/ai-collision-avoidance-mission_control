import numpy as np


# =========================================
# 🔹 БАЗОВЫЕ ФУНКЦИИ
# =========================================

def compute_min_distance(traj1, traj2):
    distances = np.linalg.norm(traj1 - traj2, axis=1)
    idx = np.argmin(distances)
    return float(distances[idx]), int(idx)


def apply_delta_v_to_trajectory(traj, velocities, delta_v_vector):
    """
    Применяет Δv ко всей траектории (упрощённая модель)
    """
    new_traj = []
    new_vel = []

    for r, v in zip(traj, velocities):
        v_new = v + delta_v_vector
        r_new = r + v_new * 60  # 60 сек ~ 1 мин шаг

        new_traj.append(r_new)
        new_vel.append(v_new)

    return np.array(new_traj), np.array(new_vel)


# =========================================
# 🧠 ИНТЕЛЛЕКТУАЛЬНЫЙ ПОДБОР МАНЁВРА
# =========================================

def optimize_maneuver(traj1, traj2, velocities1,
                      max_delta_v=0.2,
                      steps=10):
    """
    Подбираем:
    - направление
    - величину Δv
    Минимизируем риск (максимизируем дистанцию)
    """

    best_result = None
    best_score = -np.inf

    # Нормируем направления
    directions = [
        np.array([1, 0, 0]),
        np.array([-1, 0, 0]),
        np.array([0, 1, 0]),
        np.array([0, -1, 0]),
        np.array([0, 0, 1]),
        np.array([0, 0, -1])
    ]

    for direction in directions:
        direction = direction / np.linalg.norm(direction)

        for i in range(1, steps + 1):
            delta_v = max_delta_v * (i / steps)
            dv_vector = direction * delta_v

            new_traj, _ = apply_delta_v_to_trajectory(
                traj1, velocities1, dv_vector
            )

            min_dist, _ = compute_min_distance(new_traj, traj2)

            score = min_dist - delta_v * 50  # штраф за топливо

            if score > best_score:
                best_score = score
                best_result = {
                    "delta_v_vector": dv_vector,
                    "delta_v_magnitude": float(np.linalg.norm(dv_vector)),
                    "new_min_distance": float(min_dist),
                    "score": float(score),
                    "optimized_trajectory": new_traj
                }

    return best_result
