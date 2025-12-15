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

from pydantic import BaseModel
from pathlib import Path
from enum import Enum

class Mode(Enum):
    NO_IMAGE = 0
    TUNE = 1
    REVIEW = 2

class PathModeWrapper(BaseModel):
    """Wrapper class for `ImagePanel` that contains a Path and a Mode."""
    path: Path | None
    mode: Mode

class ImagePanel(QWidget):
    """Central image viewer and contour selector."""
    
    current_file_changed = Signal(PathModeWrapper)
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
        filtered_paths = [p for p in image_paths if self._validate_image_file(p)]
        if len(filtered_paths) > 0:
            self.image_files += filtered_paths
            self._set_current_file(filtered_paths[-1], is_image=True)
    
    def _clear_current_file(self):
        """Clears the current file and sets mode to `NO_IMAGE`."""
        self.current_file = None
        self.mode = Mode.NO_IMAGE
        self.current_file_changed.emit(
            PathModeWrapper(path=self.current_file, mode=self.mode)
        )
    
    def _set_current_file(self, 
                          file_path: Path, 
                          is_image: bool
        ) -> bool:
        """
        Attempts to set the currently viewed file and emits a signal.
        Returns
            kept (bool): Whether the file was kept.
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
            self.mode = Mode.TUNE
        else:
            if file_path not in self.pkl_files:
                self.pkl_files.append(file_path)
            self.mode = Mode.REVIEW
        
        # update state
        self.current_file = file_path
        self.current_file_changed.emit(
            PathModeWrapper(path=self.current_file, mode=self.mode)
        )
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
    
