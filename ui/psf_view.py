import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PSFView(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 5))
        super().__init__(self.fig)

        self.ax = self.fig.add_subplot(111)
        self.cbar = None       # ← ХРАНИМ COLORBAR
        self.im = None

        self.ax.set_title("Функция рассеяния точки (ФРТ)")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")

        self.fig.tight_layout()

    def show_psf(self, psf):
        n = psf.shape[0]
        extent = [-n//2, n//2, -n//2, n//2]

        if self.im is None:
            # первый раз
            self.im = self.ax.imshow(
                psf,
                cmap="inferno",
                origin="lower",
                extent=extent
            )
            self.cbar = self.fig.colorbar(
                self.im, ax=self.ax, fraction=0.046
            )
        else:
            # обновление
            self.im.set_data(psf)
            self.im.set_extent(extent)
            self.im.set_clim(psf.min(), psf.max())

        self.draw_idle()


