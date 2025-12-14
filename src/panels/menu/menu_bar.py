from PySide6.QtCore import (
    Qt,
    QSize
)
from PySide6.QtGui import (
    QAction
)
from PySide6.QtWidgets import (
    QMenuBar,
    QMenu,
    QMainWindow,
    QMainWindow, 
    QDockWidget, 
    QWidget,
    QScrollArea,
    QFrame
)

from models import AppState

from panels.image.image_panel import ImagePanel
from panels.process.process_panel import ProcessPanel
from panels.settings.settings_panel import SettingsPanel
from panels.output.output_panel import OutputPanel

class MenuBar(QMenuBar):
    def __init__(self, 
                 app_state: AppState,
                 image_panel: ImagePanel,
                 process_panel: ProcessPanel,
                 settings_panel: SettingsPanel,
                 output_panel: OutputPanel
        ):
        super().__init__()
        self.setObjectName("AppMenuBar")

        # -- private fields --
        self.theme = app_state.style.theme
        self.image_panel = image_panel
        self.process_panel = process_panel
        self.settings_panel = settings_panel
        self.output_panel = output_panel

        # === the actual menu ==
        # -- file --
        file_menu = self.addMenu("File")
        open_file_menu = file_menu.addMenu("Open...")

        open_settings_action = QAction("Settings file", self)
        open_tif_action = QAction("TIF/TIFF file(s)", self)
        open_pkl_action = QAction("Annotated PKL file(s)", self)

        open_file_menu.addActions([
            open_settings_action, 
            open_tif_action, 
            open_pkl_action
        ])

        save_file_menu = file_menu.addMenu("Save...")

        save_settings_action = QAction("Current settings", self)
        save_image_view_action = QAction("Current image view", self)

        save_file_menu.addActions([
            save_settings_action, 
            save_image_view_action
        ])

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(parent.close)
        file_menu.addAction(exit_action)

        # -- view --
        view_menu = self.addMenu("View")
        view_theme_menu = view_menu.addMenu("Choose color theme...")

        view_theme_light_action = QAction("Light", self)

        view_theme_menu.addActions([
            view_theme_light_action
        ])
    
    def get_theme(self) -> str:
        """Return the application's color theme."""
        return self.theme