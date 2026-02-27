import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class RiskGraph(FigureCanvasQTAgg):

    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 3))
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        self.ax.set_title("Distance vs Time")
        self.ax.set_xlabel("Time (min)")
        self.ax.set_ylabel("Distance (km)")
        self.ax.grid(True)

    def plot_distances(self, traj1, traj2):

        if len(traj1) == 0:
            return

        distances = np.linalg.norm(traj1 - traj2, axis=1)
        times = np.arange(len(distances))

        self.ax.clear()
        self.ax.plot(times, distances)
        self.ax.set_title("Distance vs Time")
        self.ax.set_xlabel("Time (min)")
        self.ax.set_ylabel("Distance (km)")
        self.ax.grid(True)
        self.draw()
