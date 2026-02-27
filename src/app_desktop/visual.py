import numpy as np
from vispy import scene
from vispy.scene import visuals
from vispy.app import Timer


class OrbitVisualizer:

    @property
    def native(self):
        return self.canvas.native

    def __init__(self):

        # ==========================================
        # 🌌 Canvas
        # ==========================================

        self.canvas = scene.SceneCanvas(
            keys='interactive',
            bgcolor='#020412',
            show=True
        )

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'
        self.view.camera.fov = 45

        # ==========================================
        # 🌍 EARTH
        # ==========================================

        self.earth_radius = 6371

        self.earth = visuals.Sphere(
            radius=self.earth_radius,
            rows=120,
            cols=120,
            method='latitude',
            parent=self.view.scene,
            color=(0.1, 0.35, 0.9, 1),
            shading='smooth'
        )

        # Атмосферное свечение
        self.atmosphere = visuals.Sphere(
            radius=self.earth_radius * 1.03,
            rows=60,
            cols=60,
            parent=self.view.scene,
            color=(0.2, 0.5, 1.0, 0.08)
        )

        self.view.camera.distance = self.earth_radius * 4

        # ==========================================
        # ⭐ Звёздный фон
        # ==========================================

        stars = np.random.uniform(-80000, 80000, (2000, 3))
        self.starfield = visuals.Markers(parent=self.view.scene)
        self.starfield.set_data(
            stars,
            face_color=(1, 1, 1, 0.8),
            size=2
        )

        # ==========================================
        # 🛰 Satellites
        # ==========================================

        self.sat1 = visuals.Sphere(
            radius=200,
            parent=self.view.scene,
            color='white'
        )

        self.sat2 = visuals.Sphere(
            radius=200,
            parent=self.view.scene,
            color='orange'
        )


        # ==========================================
        # 🏷 Labels (FIXED 3D VERSION)
        # ==========================================

        self.label1 = visuals.Text(
            "Satellite 1",
            color='white',
            parent=self.view.scene,
            font_size=48,
            bold=True,
            method='gpu',
            anchor_x='center',
            anchor_y='bottom'
        )

        self.label2 = visuals.Text(
            "Satellite 2",
            color='orange',
            parent=self.view.scene,
            font_size=48,
            bold=True,
            method='gpu',
            anchor_x='center',
            anchor_y='bottom'
        )
        # ==========================================
        # 🛰 Orbits
        # ==========================================

        self.orbit1 = None
        self.orbit2 = None
        self.optimized = None

        # ==========================================
        # Animation
        # ==========================================

        self.traj1 = None
        self.traj2 = None
        self.anim_index = 0
        self.anim_length = 0

        self.timer = Timer(interval=0.03, connect=self.animate, start=False)

        # Плавное вращение Земли
        self.earth_angle = 0
        self.earth_timer = Timer(interval=0.05, connect=self.rotate_earth, start=True)

    # =================================================

    def rotate_earth(self, event):

        self.earth_angle += 0.2
        self.earth.transform = scene.transforms.MatrixTransform()
        self.earth.transform.rotate(self.earth_angle, (0, 1, 0))

        self.atmosphere.transform = scene.transforms.MatrixTransform()
        self.atmosphere.transform.rotate(self.earth_angle, (0, 1, 0))

        self.canvas.update()

    # =================================================

    def animate(self, event):

        if self.traj1 is None:
            return

        if self.anim_index >= self.anim_length:
            self.timer.stop()
            return

        p1 = self.traj1[self.anim_index]
        p2 = self.traj2[self.anim_index]

        self.sat1.transform = scene.transforms.STTransform(
            translate=p1
        )

        self.sat2.transform = scene.transforms.STTransform(
            translate=p2
        )

        self.anim_index += 1
        self.canvas.update()

        # Обновляем подписи
        # Смещаем подписи ближе к камере по Z, чтобы они всегда были видимы
        cam_dist = self.view.camera.distance
        offset = np.array([0, 800, cam_dist * 0.7])
        self.label1.pos = p1 + offset
        self.label2.pos = p2 + offset
    # =================================================

    def update_orbits(self, traj1, traj2, optimized=None):
        # Динамически обновлять текст подписей из названий, только имя в скобках
        import inspect
        frame = inspect.currentframe()
        while frame:
            local_vars = frame.f_locals
            if 'window' in local_vars:
                try:
                    import re
                    name1 = local_vars['window'].sat1_label.text()
                    name2 = local_vars['window'].sat2_label.text()
                    # Извлечь только имя в скобках
                    m1 = re.search(r'\((.*?)\)', name1)
                    m2 = re.search(r'\((.*?)\)', name2)
                    self.label1.text = m1.group(1) if m1 else name1
                    self.label2.text = m2.group(1) if m2 else name2
                except Exception:
                    pass
                break
            frame = frame.f_back

        if self.orbit1:
            self.orbit1.parent = None
        if self.orbit2:
            self.orbit2.parent = None
        if self.optimized:
            self.optimized.parent = None

        if traj1 is None or len(traj1) == 0:
            return

        traj1 = np.array(traj1)
        traj2 = np.array(traj2)

        # Авто-масштаб камеры
        max_distance = np.max(np.linalg.norm(traj1, axis=1))
        self.view.camera.distance = max_distance * 2.2

        # Орбита 1
        self.orbit1 = visuals.Line(
            pos=traj1,
            color='cyan',
            width=2,
            parent=self.view.scene
        )

        # Орбита 2
        self.orbit2 = visuals.Line(
            pos=traj2,
            color='orange',
            width=2,
            parent=self.view.scene
        )

        # Оптимизированная
        if optimized is not None and len(optimized) > 0:
            self.optimized = visuals.Line(
                pos=np.array(optimized),
                color='red',
                width=3,
                parent=self.view.scene
            )

        self.traj1 = traj1
        self.traj2 = traj2
        self.anim_index = 0
        self.anim_length = min(len(traj1), len(traj2))

        self.timer.start()
        self.canvas.update()