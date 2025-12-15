from PySide6.QtCore import (
    Qt,
    QSize,
    QEvent
)
from PySide6.QtGui import (
    QIcon
)
from PySide6.QtWidgets import (
    QApplication,
    QTabWidget,
    QLabel,
    QWidget
)

from models import AppState
from pathlib import Path

class PathWidget(QWidget):
    """Dummy widget that contains a Path object"""
    def __init__(self, path: Path):
        super().__init__()
        self.path = path
    
    def get_path(self) -> Path:
        """Return this `PathWidget`'s path."""
        return self.path

class FileTabSelector(QTabWidget):

    def __init__(self, app_state: AppState):
        super().__init__()
        self.setObjectName("FileTabs")

        # config
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setDocumentMode(True)

    def set_files(self, image_files: list[Path], seg_files: list[Path]):
        """Update the current file tabs with the given set of image and segmentation files."""
        if None in image_files or None in seg_files:
            return
        
        _, paths = self._get_tabs_paths()

        # add new image paths
        for image_path in image_files:
            if image_path not in paths:
                self._create_new_tab(image_path)

        # add new segmentation paths
        for seg_path in seg_files:
            if seg_path not in paths:
                self._create_new_tab(seg_path)

        # remove disappeared paths
        for i in range(len(paths)-1, -1, -1):
            path = paths[i]
            if path not in image_files and path not in seg_files:
                self.removeTab(i)

    def set_current_file(self, current_file: Path):
        """Sets the currently selected file tab. Creates a new tab if `current_file` doesn't exist."""
        if current_file is None:
            return
        
        _, paths = self._get_tabs_paths()
        if current_file not in paths:
            index = self._create_new_tab(current_file)
        else:
            index = paths.index(current_file)
        self.setCurrentIndex(index)
    
    def _create_new_tab(self, tab_path: Path) -> int:
        """
        Creates a new tab with the given path.
        Returns:
            index (int): The new tab's index.
        """
        if tab_path is None:
            return -1
        
        widget = PathWidget(tab_path)
        index = self.addTab(widget, tab_path.name)
        self.setTabToolTip(index, tab_path.name)
        return index
    
    def _get_tabs_paths(self) -> tuple[
        list[PathWidget | None], 
        list[Path | None]
    ]:
        """Returns lists containing all existing `PathWidgets` and `Paths`."""
        tabs: list[PathWidget | None] = []
        for i in range(self.count()):
            w = self.widget(i)
            tabs.append(w if isinstance(w, PathWidget) else None)
        paths: list[Path | None] = [pw.get_path() if pw is not None else None for pw in tabs]
        return tabs, paths
