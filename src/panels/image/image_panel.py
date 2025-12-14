from PySide6.QtCore import (
    QSize,
    Signal
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QMessageBox
)

from models import AppState

from pathlib import Path

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
    
    def add_images(self, image_paths: list[Path]):
        """Add new image files."""
        for image_path in image_paths:
            self._set_current_file(image_path, is_image=True)
    
    def _set_current_file(self, file_path: Path, is_image: bool):
        """Attempts to set the currently viewed file and emits a signal."""
        keep = self._validate_image_file(file_path)
        if not keep:
            if file_path in self.image_files:
                self.image_files.remove(file_path)
            if file_path in self.pkl_files:
                self.pkl_files.remove(file_path)
            return
        
        # update lists
        if is_image:
            if file_path not in self.image_files:
                self.image_files.append(file_path)
        else:
            if file_path not in self.pkl_files:
                self.pkl_files.append(file_path)
        
        # Render image
        self.current_file = file_path
        self.current_file_changed.emit(self.current_file)
        #TODO: finish

    def _validate_image_file(self, image_path: Path) -> bool:
        """
        Check if the given image file is valid.
        Returns:
            keep (bool): Whether the user wants to keep the file or not.
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'}
        if not image_path.is_file() or image_path.suffix.lower() in image_extensions:
            return QMessageBox(
                QMessageBox.Icon.Warning,
                "Invalid or Missing File", 
                f"File {image_path.absolute()} either does not exit or is not one of the following image types: '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'. Do you want to keep this file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                self
            ).exec() == QMessageBox.StandardButton.Yes
        return True