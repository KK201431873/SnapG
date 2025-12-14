from PySide6.QtCore import (
    QSize,
    Signal
)
from PySide6.QtGui import (
    QImage
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QMessageBox
)

from panels.image.image_view import ImageView

from models import AppState

from pathlib import Path
from enum import Enum

class Mode(Enum):
    NO_IMAGE = 0
    TUNE = 1
    REVIEW = 2

class ImagePanel(QWidget):
    """Central image viewer and contour selector."""
    
    current_file_changed = Signal(Path)
    """Emits the currently selected file's `Path`."""

    def __init__(self, app_state: AppState):
        super().__init__()
        
        # init files lists and state
        self.image_files: list[Path] = []
        self.pkl_files: list[Path] = []
        self.current_file: Path | None = None
        self.mode: Mode = Mode.NO_IMAGE

        # layout
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        
        # image view
        self.image_view = ImageView(self)
        vlayout.addWidget(self.image_view)
    
    def add_images(self, image_paths: list[Path]):
        """Add new image files."""
        last_kept_image: Path | None = None
        for image_path in image_paths:
            kept = self._set_current_file(image_path, is_image=True, emit_signal=False)
            if kept:
                last_kept_image = image_path
        # Emit for very last valid image
        if last_kept_image is not None:
            self.current_file_changed.emit(self.current_file)
    
    def _set_current_file(self, 
                          file_path: Path, 
                          is_image: bool, 
                          emit_signal: bool
        ) -> bool:
        """
        Attempts to set the currently viewed file and emits a signal.
        Returns
            kept (bool): Whether the image was kept.
        """
        valid = self._validate_image_file(file_path)
        if not valid:
            if file_path in self.image_files:
                self.image_files.remove(file_path)
            if file_path in self.pkl_files:
                self.pkl_files.remove(file_path)
            return False
        
        # update lists
        if is_image:
            if file_path not in self.image_files:
                self.image_files.append(file_path)
        else:
            if file_path not in self.pkl_files:
                self.pkl_files.append(file_path)
        
        # update state
        self.current_file = file_path
        if emit_signal:
            self.current_file_changed.emit(self.current_file)
        return True

    def _validate_image_file(self, image_path: Path) -> bool:
        """
        Check if the given image file is valid.
        Returns:
            valid (bool): The image file's validity.
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'}
        if not image_path.is_file() or image_path.suffix.lower() in image_extensions:
            QMessageBox(
                QMessageBox.Icon.Warning,
                "Invalid or Missing File", 
                f"File {image_path.absolute()} either does not exit or is not one of the following image types: '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'.",
                QMessageBox.StandardButton.Ok,
                self
            ).exec()
            return False
        return True
    
