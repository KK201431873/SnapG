from PySide6.QtCore import (
    Qt,
    QSize,
    QEvent,
    Signal,
    QSignalBlocker
)
from PySide6.QtGui import (
    QIcon,
    QWheelEvent,
    QShortcut,
    QKeySequence
)
from PySide6.QtWidgets import (
    QApplication,
    QTabWidget,
    QLabel,
    QWidget,
    QTabBar,
    QMessageBox,
    QToolButton
)

from panels.modified_widgets import PathWidget, ScrollableTabBar

from models import AppState, FileMan
from pathlib import Path

class FileTabSelector(QTabWidget):

    tab_changed = Signal(Path, bool)
    """Emits path of currently opened tab and whether the file is an image."""

    close_file_requested = Signal(Path)
    """Emits path of file to be removed."""

    def __init__(self, app_state: AppState):
        super().__init__()
        self.setObjectName("FileTabs")
        self.last_opened_file: Path | None = None

        # -- config --
        self.setTabBar(ScrollableTabBar(self))
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setDocumentMode(True)

        # minimum width
        self.setStyleSheet("QTabBar::tab { min-width: 125px; min-height: 30px }")

        # dummy tab
        self.addTab(QWidget(), "")
        self.setTabEnabled(0, False)
        self.setTabVisible(0, False)
        self.setCurrentIndex(0)

        # tab state signals
        self.currentChanged.connect(self._broadcast_tab_changed)
        self.tabCloseRequested.connect(self._request_close_tab)
        
        # -- shortcuts --
        # Ctrl+Tab moves to next tab
        next_tab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab.setContext(Qt.ShortcutContext.ApplicationShortcut)
        next_tab.activated.connect(self._next_tab)

        # Ctrl+Shift+Tab moves to previous tab
        prev_tab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab.setContext(Qt.ShortcutContext.ApplicationShortcut)
        prev_tab.activated.connect(self._prev_tab)

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        close_shortcut.activated.connect(lambda: self._request_close_tab(self.currentIndex()))

    def set_files(self, image_files: list[Path], seg_files: list[Path]):
        """Update the current file tabs with the given set of image and segmentation files."""
        with QSignalBlocker(self):
            paths = self._get_tab_paths()

            # add new image paths
            for image_path in image_files:
                if image_path is None:
                    continue
                if image_path not in paths:
                    self._create_new_tab(image_path)

            # add new segmentation paths
            for seg_path in seg_files:
                if seg_path is None:
                    continue
                if seg_path not in paths:
                    self._create_new_tab(seg_path)

            # remove disappeared paths
            for i in range(len(paths) - 1, 0, -1):
                path = paths[i]
                if path not in image_files and path not in seg_files:
                    self.removeTab(i)

    def set_current_file(self, current_file: Path):
        """Sets the currently selected file tab. Creates a new tab if `current_file` doesn't exist."""
        if current_file is None:
            self.setCurrentIndex(0) # dummy tab
            return
        
        paths = self._get_tab_paths()
        if current_file not in paths:
            index = self._create_new_tab(current_file)
        else:
            index = paths.index(current_file)
        self.setCurrentIndex(index)
        self.last_opened_file = current_file
    
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
        extension = tab_path.suffix.lower()
        if extension == ".seg":
            self.setTabIcon(index, QIcon("assets/seg_file_icon.ico"))
        if FileMan.is_image(extension):
            self.setTabIcon(index, QIcon("assets/image_icon.ico"))
        return index
    
    def _get_tab_paths(self) -> list[Path | None]:
        """Returns lists containing all existing `PathWidgets` and `Paths`."""
        tabs: list[PathWidget | None] = []
        for i in range(self.count()):
            w = self.widget(i)
            tabs.append(w if isinstance(w, PathWidget) else None)
        paths: list[Path | None] = [pw.get_path() if pw is not None else None for pw in tabs]
        return paths

    def _broadcast_tab_changed(self, index: int):
        """Receive tab change index and broadcast corresponding file path."""
        paths = self._get_tab_paths()
        if not (1 <= index <= len(paths) - 1):
            return # sanity check
        
        path = paths[index]
        if path is None:
            return
        
        if path == self.last_opened_file:
            return # user just moved the tab

        # broadcast
        is_image = path.suffix.lower() != ".seg"
        self.tab_changed.emit(path, is_image)
    
    def _request_close_tab(self, index: int):
        """Emit signal to tell `ImagePanel` that a tab wants to be closed."""
        def show_close_error():
            QMessageBox.warning(
                self,
                "Close File",
                "There is no file to close."
            )

        paths = self._get_tab_paths()
        if not (1 <= index <= len(paths) - 1):
            show_close_error()
            return # sanity check
        
        path = paths[index]
        if path is None:
            show_close_error()
            return
        
        reply = QMessageBox.question(
            self,
            "Close File",
            f"Close '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # send signal
        if reply == QMessageBox.StandardButton.Yes:
            self.close_file_requested.emit(path)
    
    def _next_tab(self):
        """Go to next tab."""
        if self.count() <= 1:
            return
        self.setCurrentIndex(1 + (min(self.currentIndex(), self.count() - 2)))

    def _prev_tab(self):
        """Go to previous tab."""
        if self.count() <= 1:
            return
        self.setCurrentIndex(1 + (max(self.currentIndex() - 2, 0)))

