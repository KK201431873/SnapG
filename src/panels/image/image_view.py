from PySide6.QtCore import (
    Qt,
    Signal,
    QRect,
    QPoint
)
from PySide6.QtGui import (
    QPainter, 
    QPixmap,
    QImage,
    QMouseEvent,
    QWheelEvent,
    QGuiApplication,
    QFont,
    QFontMetrics
)
from PySide6.QtWidgets import (
    QWidget,
    QApplication
)

from models import AppState, logger

import numpy.typing as npt
import numpy as np

def clamp(x, lower, upper):
    """Clamps the given `x` between the `lower` and `upper` bounds."""
    return max(lower, min(upper, x))

class ImageView(QWidget):

    mouse_pressed = Signal(bool, QPoint)

    def __init__(self, parent, app_state: AppState):
        super().__init__(parent)
        # image state
        self.pixmap: QPixmap | None = None
        self.scaled_pixmap: QPixmap | None = None
        self.base_img_dims: tuple[int, int] | None = None
        self.center_point: tuple[int, int] = app_state.image_panel_state.view_center_point
        self.image_width: int = app_state.image_panel_state.view_image_width
        self._processing: bool = False

        # user control state
        self.drag_start_position: QPoint | None = None
        self.drag_start_image_position: tuple[int, int] = (0, 0)
        self.drag_active: bool = False

        # update UI
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_scaled_pixmap()
        self.update()

    def set_center_zoom(self, new_center_point: tuple[int, int], new_image_width: int):
        """Set the center point and zoom/image width to the given values."""
        self.center_point = new_center_point
        self.image_width = new_image_width
        self._update_scaled_pixmap()
        self.update()

    def set_image(self, img: npt.NDArray, base_img_dims: tuple[int, int]):
        """Sets the current image to the given NumPy image, and takes the base image dimensions."""
        qimg = numpy_to_qimage(img)
        self.pixmap = QPixmap.fromImage(qimg)
        self.base_img_dims = base_img_dims
        self._update_scaled_pixmap()
        self.update()
    
    def clear_image(self):
        """Clears the current image and displays \"No Image Selected\"."""
        self.pixmap = None
        self.base_img_dims = None
        self._update_scaled_pixmap()
        self.update()
    
    def set_processing(self, active: bool):
        """Update state of processing indicator."""
        self._processing = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())

        # no image
        if self.pixmap == None or self.scaled_pixmap == None:
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
        scrn_w, scrn_h = self.size().toTuple()
        im_w, im_h = self.scaled_pixmap.rect().size().toTuple()
        top_left = QPoint(
            scrn_w // 2 + self.center_point[0] - im_w // 2, scrn_h // 2 + self.center_point[1] - im_h // 2
        )
        bottom_right = QPoint(
            scrn_w // 2 + self.center_point[0] + im_w // 2, scrn_h // 2 + self.center_point[1] + im_h // 2
        )
        painter.drawPixmap(
            QRect(top_left, bottom_right),
            self.scaled_pixmap,
            self.scaled_pixmap.rect()
        )

        # processing status indicator
        if self._processing:
            font = QFont("Arial", 30)
            text = "Processing…"
            bbox = QFontMetrics(font).boundingRect(text)
            bb_w, bb_h = bbox.size().toTuple()

            margin = 20
            painter.setOpacity(0.4)
            painter.fillRect(
                QRect(
                    QPoint(
                        scrn_w // 2 - bb_w // 2 - margin,
                        scrn_h // 2 - bb_h // 2 - margin
                    ),
                    QPoint(
                        scrn_w // 2 + bb_w // 2 + margin,
                        scrn_h // 2 + bb_h // 2 + margin
                    )
                ), 
                Qt.GlobalColor.black
            )

            painter.setOpacity(1.0)
            painter.setFont(font)
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                text
            )
    
    def _update_scaled_pixmap(self):
        """Creates and caches a resized pixmap based on user-controlled zoom."""
        if not self.pixmap:
            self.scaled_pixmap = None
            return

        im_w = self.image_width
        im_h = int(im_w * self.pixmap.height() / self.pixmap.width())

        self.scaled_pixmap = self.pixmap.scaled(
            im_w, im_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    
    def _clear_drag(self):
        """Clears right-click drag event data."""
        self.drag_start_position = None
        self.drag_start_image_position = (0, 0)
        self.drag_active = False
    
    def _in_image(self, point: QPoint) -> tuple[bool, QPoint]:
        """
        Convert a global point to rescaled image-relative coordinates.
        Returns:
            is_in_image (bool): Whether the point is within the image.
            image_point (QPoint): The rescaled image-relative coordinates of the point.
        """
        if self.pixmap is None or self.scaled_pixmap is None or self.base_img_dims is None:
            logger.err("_in_image(): called when pixmap, scaled_pixmap, or base_img_dims is None.", self)
            return False, QPoint()
        # get top left corner
        scrn_w, scrn_h = self.size().toTuple()
        im_w, im_h = self.scaled_pixmap.rect().size().toTuple()
        top_left = QPoint(
            scrn_w // 2 + self.center_point[0] - im_w // 2, scrn_h // 2 + self.center_point[1] - im_h // 2
        )

        # check if point in image
        image_point = point - top_left
        is_in_image = (
            0 <= image_point.x() <= im_w and
            0 <= image_point.y() <= im_h
        )

        # rescale coordinates
        image_point = QPoint(
            int(image_point.x() * self.base_img_dims[0] / im_w),
            int(image_point.y() * self.base_img_dims[1] / im_h)
        )
        return is_in_image, image_point

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.pixmap is None or self.scaled_pixmap is None:
            self._clear_drag()
            return super().mousePressEvent(event)
        
        # handle pan start
        if event.button() == Qt.MouseButton.RightButton:
            self.drag_start_position = event.pos()
            self.drag_start_image_position = self.center_point
            self.drag_active = True
        elif event.button() == Qt.MouseButton.LeftButton:
            is_in_image, image_point = self._in_image(event.pos())
            # Propagate mouse event up
            self.mouse_pressed.emit(is_in_image, image_point)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.pixmap is None or self.scaled_pixmap is None:
            self._clear_drag()
            return super().mouseMoveEvent(event)

        # handle pan move
        if event.buttons() & Qt.MouseButton.RightButton and self.drag_start_position is not None:
            self.drag_active = True
            displacement = event.pos() - self.drag_start_position
            cx, cy = self.drag_start_image_position

            self.center_point = (
                cx + displacement.x(),
                cy + displacement.y()
            )
            self._clamp_center_position()
            self.update()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.pixmap is None or self.scaled_pixmap is None:
            self._clear_drag()
            return super().mouseReleaseEvent(event)
        
        # handle pan stop
        if event.button() == Qt.MouseButton.RightButton:
            self._clear_drag()
        else:
            super().mouseReleaseEvent(event)
    
    def _clamp_center_position(self):
        """Clamps the image's center position to within the widget area."""
        if self.pixmap is None or self.scaled_pixmap is None:
            return
        cx, cy = self.center_point
        im_w, im_h = self.scaled_pixmap.size().toTuple()
        scrn_w, scrn_h = self.size().toTuple()
        margin = 30 # so the user can still see the image
        min_x = -scrn_w // 2 - im_w // 2 + margin
        min_y = -scrn_h // 2 - im_h // 2 + margin
        max_x = scrn_w // 2 + im_w // 2 - margin
        max_y = scrn_h // 2 + im_h // 2 - margin
        self.center_point = (
            clamp(cx, min_x, max_x),
            clamp(cy, min_y, max_y)
        )

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.pixmap is None or self.scaled_pixmap is None:
            return

        old_width = self.image_width

        # zoom limits
        screen_width = QGuiApplication.primaryScreen().geometry().width()
        maximum_zoom = 2 * screen_width
        minimum_zoom = 50

        # mouse position relative to widget center
        mouse_pos = event.position().toPoint()
        scrn_w, scrn_h = self.size().toTuple()
        mouse_rel = QPoint(
            mouse_pos.x() - scrn_w // 2,
            mouse_pos.y() - scrn_h // 2
        )

        # zoom factor
        delta = event.angleDelta().y()
        zoom_factor = 1.0 + delta / 1200
        zoom_factor = clamp(zoom_factor, 0.8, 1.25)

        new_width = int(clamp(
            old_width * zoom_factor,
            minimum_zoom,
            maximum_zoom
        ))

        if new_width == old_width:
            return

        # shift center point
        scale = new_width / old_width
        cx, cy = self.center_point
        mx, my = mouse_rel.x(), mouse_rel.y()
        self.center_point = (
            int(mx + (cx - mx) * scale),
            int(my + (cy - my) * scale)
        )
        self.image_width = new_width

        self._update_scaled_pixmap()
        self._clamp_center_position()
        self.update()
    
    def get_center_point(self) -> tuple[int, int]:
        """Get the current image's center point."""
        return self.center_point
    
    def get_image_width(self) -> int:
        """Get the current image's width."""
        return self.image_width

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