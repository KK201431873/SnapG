from PySide6.QtCore import (
    QSize
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QTextBrowser
)

class OutputPanel(QWidget):
    """Textbox for showing program outputs."""

    def __init__(self):
        super().__init__()

        # add widgets to layout
        self.vlayout = QVBoxLayout(self)
        self.vlayout.addWidget(QTextBrowser())

        # add layout to current widget
        self.setLayout(self.vlayout)