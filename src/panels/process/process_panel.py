from PySide6.QtCore import (
    QSize
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit
)

from models import AppState

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self, app_state: AppState):
        super().__init__()