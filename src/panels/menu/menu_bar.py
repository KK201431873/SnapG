from PySide6.QtCore import (
    Qt,
    QSize,
    Signal
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

    theme_changed = Signal(str)

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

        self.exit_action = QAction("Exit", self)
        file_menu.addAction(self.exit_action)

        # -- view --
        view_menu = self.addMenu("View")
        view_theme_menu = view_menu.addMenu("Choose color theme...")

        self.view_theme_light_action = QAction("Light", self)
        self.view_theme_light_action.setCheckable(True)
        self.view_theme_light_action.triggered.connect(self._set_light_theme)

        self.view_theme_dark_action = QAction("Dark", self)
        self.view_theme_dark_action.setCheckable(True)
        self.view_theme_dark_action.triggered.connect(self._set_dark_theme)

        #TODO: fix dark color theme
        self.view_theme_dark_action.setDisabled(True)

        view_theme_menu.addActions([
            self.view_theme_light_action,
            self.view_theme_dark_action
        ])
        self._update_theme()

    
    def _set_light_theme(self):
        """Set the theme to `light`."""
        self.theme = 'light'
        self._update_theme()
    
    def _set_dark_theme(self):
        """Set the theme to `dark`."""
        self.theme = 'dark'
        self._update_theme()

    def _update_theme(self):
        """Update the check marks in each color theme menu action and emit signal."""
        self.view_theme_light_action.setChecked(self.theme == 'light')
        self.view_theme_dark_action.setChecked(self.theme == 'dark')
        self.theme_changed.emit(self.theme)
    
    def get_theme(self) -> str:
        """Return the application's color theme."""
        return self.theme
    
    def get_exit_action(self) -> QAction:
        """Return the `MenuBar`'s exit action"""
        return self.exit_action