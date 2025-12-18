from PySide6.QtCore import (
    Qt,
    QSize,
    QLocale
)
from PySide6.QtGui import (
    QDoubleValidator,
    QWheelEvent
)
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout, 
    QTextEdit,
    QLabel,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QSizePolicy,
    QLineEdit,
    QComboBox,
    QTabBar,
    QMessageBox,
    QToolButton,
    QTextBrowser
)

from pathlib import Path

class NonScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()

class NonScrollSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def wheelEvent(self, event):
        event.ignore()

class NonScrollSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()

class NonScrollDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()
        
class PathWidget(QWidget):
    """Dummy widget that contains a Path object"""
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
    
    def get_path(self) -> Path:
        """Return this `PathWidget`'s path."""
        return self.path
    
class ScrollableTabBar(QTabBar):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setExpanding(False)
        self.setUsesScrollButtons(True)

    def wheelEvent(self, event: QWheelEvent) -> None:
        # try finding scroll buttons
        buttons = self.findChildren(QToolButton)
        if len(buttons) < 2:
            return super().wheelEvent(event)
        left_btn, right_btn = buttons[0], buttons[1]
        
        # simulate clicking
        if event.angleDelta().y() > 0:
            left_btn.click()
        else:
            right_btn.click()
        event.accept()

class AutoHeightTextBrowser(QTextBrowser):
    def resizeEvent(self, event):
        super().resizeEvent(event)
        doc = self.document()
        self.setFixedHeight(int(doc.size().height()) + 2)