from PySide6.QtCore import (
    Qt
)
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QLabel
)

class BusyDialog(QDialog):
    def __init__(self, text="Working…", parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setFixedSize(260, 90)

        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)