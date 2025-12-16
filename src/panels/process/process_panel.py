from PySide6.QtCore import (
    QSize,
    Qt
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QPushButton,
    QGroupBox,
    QTextBrowser,
    QFrame
)

from panels.process.choose_images_dialog import ChooseImagesDialog

from models import AppState

from pathlib import Path

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self, app_state: AppState):
        super().__init__()
        self.chosen_images: list[tuple[Path, bool]] = []

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # choose images button
        self.choose_images_btn = QPushButton("Choose Images")
        self.choose_images_btn.clicked.connect(self._choose_files)
        layout.addWidget(self.choose_images_btn)
        
        # separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # output box
        group = QGroupBox("Processing Output")
        group_layout = QVBoxLayout(group)

        self.text_browser = QTextBrowser()
        self.text_browser.setMinimumHeight(200)
        group_layout.addWidget(self.text_browser)
        
        layout.addWidget(group)
    
    def _choose_files(self):
        """Show dialog for selecting image files."""
        dialog = ChooseImagesDialog(
            chosen_images=self.chosen_images,
            parent=self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        # update internal state if user pressed OK
        self.chosen_images = dialog.get_chosen_images()