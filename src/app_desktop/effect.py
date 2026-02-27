import numpy as np
from vispy import scene
from vispy.scene import visuals


class CollisionEffect:
    def __init__(self, parent):
        self.parent = parent

        # Вспышка
        self.flash = visuals.Markers(
            parent=parent,
            face_color=(1, 0.2, 0.2, 1),
            size=40
        )

        # Обломки
        self.debris = visuals.Markers(
            parent=parent,
            face_color=(1, 0.8, 0.3, 0.9),
            size=4
        )

        self.active = False
        self.t = 0
        self.center = np.zeros(3)

    def trigger(self, position):
        self.center = np.array(position)
        self.t = 0
        self.active = True

        self.flash.set_data(np.array([self.center]))

        # генерируем обломки
        debris = []
        for _ in range(150):
            direction = np.random.normal(size=3)
            direction /= np.linalg.norm(direction)
            debris.append(self.center + direction * np.random.uniform(0.01, 0.05))

        self.debris_points = np.array(debris)

    def update(self):
        if not self.active:
            return

        self.t += 1

        scale = 1 + self.t * 0.08
        self.flash.set_data(
            np.array([self.center]),
            size=40 * scale,
            face_color=(1, 0.2, 0.2, max(0, 1 - self.t * 0.05))
        )

        self.debris_points += np.random.normal(scale=0.002, size=self.debris_points.shape)
        self.debris.set_data(self.debris_points)

        if self.t > 40:
            self.flash.set_data(np.empty((0, 3)))
            self.debris.set_data(np.empty((0, 3)))
            self.active = False
