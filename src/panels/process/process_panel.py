from PySide6.QtCore import (
    QSize,
    Qt
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QPushButton
)

from models import AppState

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self, app_state: AppState):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.choose_images_btn = QPushButton("Choose Images")
        layout.addWidget(self.choose_images_btn)