from PySide6.QtCore import (
    QSize
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit
)

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(100,100))
        pass