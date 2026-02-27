import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QSlider
)
from PySide6.QtCore import Qt
from sgp4.api import Satrec

from src.orbit.collision import analyze_collision
from src.app_desktop.visual import OrbitVisualizer
from src.app_desktop.analytics import RiskGraph
from src.data.tle_fetcher import fetch_tle_group


# ======================================================
# 🎯 Risk Color
# ======================================================

def risk_color(score):
    if score >= 0.8:
        return "#ff3b3b", "CRITICAL"
    elif score >= 0.6:
        return "#ff8800", "HIGH"
    elif score >= 0.3:
        return "#ffd000", "MEDIUM"
    else:
        return "#00ff88", "LOW"


# ======================================================
# 🚀 Mission Control v5
# ======================================================

class CollisionApp(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🚀 Mission Control v5")
        self.setMinimumSize(1400, 850)

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f1a;
                color: white;
                font-family: Arial;
            }

            QPushButton {
                background-color: #1f2a44;
                border: 1px solid #2f3d66;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2f3d66;
            }

            QTextEdit {
                background-color: #111a2b;
                border: 1px solid #2f3d66;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)

        # ======================================================
        # LEFT PANEL
        # ======================================================

        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        main_layout.addLayout(left_panel, 1)

        title_left = QLabel("Satellite Control")
        title_left.setStyleSheet("font-size:18px; font-weight:bold;")
        left_panel.addWidget(title_left)

        self.sat1_label = QLabel("Satellite 1 (ISS)")
        self.sat1_label.setStyleSheet("font-size:15px; font-weight:bold; color:#00eaff;")
        left_panel.addWidget(self.sat1_label)
        self.tle1 = QTextEdit()
        self.tle1.setPlaceholderText("Satellite 1 TLE (2 lines)")
        left_panel.addWidget(self.tle1)

        self.sat2_label = QLabel("Satellite 2 (STARLINK)")
        self.sat2_label.setStyleSheet("font-size:15px; font-weight:bold; color:#ffaa00;")
        left_panel.addWidget(self.sat2_label)
        self.tle2 = QTextEdit()
        self.tle2.setPlaceholderText("Satellite 2 TLE (2 lines)")
        left_panel.addWidget(self.tle2)

        load_iss = QPushButton("🛰 Load ISS")
        load_iss.clicked.connect(self.load_iss)
        left_panel.addWidget(load_iss)

        load_starlink = QPushButton("🌐 Load 2 Starlink")
        load_starlink.clicked.connect(self.load_starlink)
        left_panel.addWidget(load_starlink)

        analyze_btn = QPushButton("🔍 Analyze Collision")
        analyze_btn.clicked.connect(self.run_analysis)
        left_panel.addWidget(analyze_btn)

        left_panel.addWidget(QLabel("Δv Strength (m/s)"))
        self.dv_slider = QSlider(Qt.Horizontal)
        self.dv_slider.setMinimum(1)
        self.dv_slider.setMaximum(100)
        self.dv_slider.setValue(10)
        left_panel.addWidget(self.dv_slider)

        apply_btn = QPushButton("🚀 Apply Maneuver")
        apply_btn.clicked.connect(self.apply_maneuver)
        left_panel.addWidget(apply_btn)

        left_panel.addStretch()

        # ======================================================
        # RIGHT PANEL
        # ======================================================

        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        main_layout.addLayout(right_panel, 3)

        # ---- TITLE ----
        title = QLabel("🚀 AI Collision Avoidance Mission Control")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:26px;
            font-weight:bold;
            padding:10px;
            background-color:#111a2b;
            border:1px solid #2f3d66;
            border-radius:10px;
        """)
        right_panel.addWidget(title)

        # ---- 3D SCENE (ГЛАВНЫЙ ЭЛЕМЕНТ) ----
        self.visualizer = OrbitVisualizer()
        right_panel.addWidget(self.visualizer.native, 6)

        # ---- GRAPH (КОМПАКТНЫЙ) ----
        self.graph = RiskGraph()
        self.graph.setMaximumHeight(220)
        right_panel.addWidget(self.graph, 2)

        # ---- RISK PANEL ----
        self.result_label = QLabel("Waiting for analysis...")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            background-color:#111a2b;
            border:1px solid #2f3d66;
            border-radius:10px;
            padding:12px;
            font-size:22px;
            font-weight:bold;
        """)
        right_panel.addWidget(self.result_label)

        self.last_result = None

    # ======================================================
    # LOAD ISS
    # ======================================================

    def load_iss(self):
        tle_data = fetch_tle_group("stations")
        if tle_data:
            # tle_data[0] = (name, line1, line2)
            name, line1, line2 = tle_data[0]
            self.sat1_label.setText(f"Satellite 1 ({name})")
            self.tle1.setText(f"{line1}\n{line2}")

    # ======================================================
    # LOAD STARLINK
    # ======================================================

    def load_starlink(self):
        tle_data = fetch_tle_group("starlink")
        if len(tle_data) >= 2:
            name1, l1_1, l1_2 = tle_data[0]
            name2, l2_1, l2_2 = tle_data[1]
            self.sat1_label.setText(f"Satellite 1 ({name1})")
            self.sat2_label.setText(f"Satellite 2 ({name2})")
            self.tle1.setText(f"{l1_1}\n{l1_2}")
            self.tle2.setText(f"{l2_1}\n{l2_2}")

    # ======================================================
    # ANALYSIS
    # ======================================================

    def run_analysis(self):
        try:
            t1 = self.tle1.toPlainText().strip().splitlines()
            t2 = self.tle2.toPlainText().strip().splitlines()
            print("TLE1:", t1)
            print("TLE2:", t2)

            if len(t1) < 2 or len(t2) < 2:
                raise ValueError("Both satellites must contain 2 TLE lines")

            sat1 = Satrec.twoline2rv(t1[0], t1[1])
            sat2 = Satrec.twoline2rv(t2[0], t2[1])

            result = analyze_collision(sat1, sat2)
            self.last_result = result

            self.visualizer.update_orbits(
                result["trajectory_1"],
                result["trajectory_2"],
                result["optimized_trajectory"]
            )

            self.graph.plot_distances(
                result["trajectory_1"],
                result["trajectory_2"]
            )

            score = result["hybrid_score"]
            color, level = risk_color(score)

            self.result_label.setText(
                f"Hybrid Risk Score: {score:.2f} | {level}"
            )

            self.result_label.setStyleSheet(f"""
                background-color:#111a2b;
                border:1px solid #2f3d66;
                border-radius:10px;
                padding:12px;
                font-size:22px;
                font-weight:bold;
                color:{color};
            """)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ======================================================
    # APPLY MANEUVER
    # ======================================================

    def apply_maneuver(self):
        if not self.last_result:
            return

        self.visualizer.update_orbits(
            self.last_result["trajectory_1"],
            self.last_result["trajectory_2"],
            self.last_result["optimized_trajectory"]
        )


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CollisionApp()
    window.show()
    sys.exit(app.exec())
