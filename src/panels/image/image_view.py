from PySide6.QtCore import (
    Qt,
    Signal
)
from PySide6.QtGui import (
    QPainter, 
    QPixmap,
    QImage,
    QMouseEvent
)
from PySide6.QtWidgets import (
    QWidget
)

import numpy.typing as npt
import numpy as np

class ImageView(QWidget):

    mouse_pressed = Signal(QMouseEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.update()


    def set_image(self, img: npt.NDArray):
        """Sets the current image to the given NumPy image."""
        qimg = numpy_to_qimage(img)
        self._pixmap = QPixmap.fromImage(qimg)
        self.update()
    
    def clear_image(self):
        """Clears the current image and displays \"No Image Selected\"."""
        self._pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())

        # no image
        if not self._pixmap:
            painter.setPen(self.palette().text().color())
            painter.setFont(self.font())

            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No Image Selected"
            )
            return
        
        # render image
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(
            self.rect(),
            self._pixmap,
            self._pixmap.rect()
        )

    def mousePressEvent(self, event):
        # Propagate mouse event up
        self.mouse_pressed.emit(event)

# -- helpers --
def numpy_to_qimage(img: npt.NDArray) -> QImage:
    """Convert NumPy image to QImage."""
    if img.ndim == 2:
        h, w = img.shape
        return QImage(
            img.data, w, h, w, QImage.Format.Format_Grayscale8
        )

    if img.ndim == 3:
        h, w, c = img.shape
        if c == 3:
            return QImage(
                img.data, w, h, 3 * w, QImage.Format.Format_BGR888
            )
        elif c == 4:
            return QImage(
                img.data, w, h, 4 * w, QImage.Format.Format_RGBA8888
            )

    raise ValueError("Unsupported image format")