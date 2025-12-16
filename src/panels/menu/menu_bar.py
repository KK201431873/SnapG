from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    SignalInstance
)
from PySide6.QtGui import (
    QAction,
    QKeySequence
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
from panels.menu.remove_files_dialog import RemoveFilesDialog

class MenuBar(QMenuBar):

    theme_changed = Signal(str)
    """Emits color theme changes."""

    process_visible_changed = Signal(bool)
    """Emits `ProcessPanel`'s visibility."""

    settings_visible_changed = Signal(bool)
    """Emits `SettingsPanel`'s visibility."""

    output_visible_changed = Signal(bool)
    """Emits `OutputPanel`'s visibility."""

    reset_view_triggered = Signal()
    """Emits when user requests reset view."""

    open_settings_triggered = Signal()
    """Emits when the user requests to open a settings file."""

    open_images_triggered = Signal()
    """Emits when the user requests to open image files."""

    save_settings_triggered = Signal()
    """Emits when the user requests to save the current settings."""

    save_image_view_triggered = Signal()
    """Emits when the user requests to save the currently displayed image."""

    close_files_triggered = Signal(list)
    """Emits list of `Path`s when user requests to close multiple files."""

    def __init__(self, 
                 app_state: AppState,
                 image_panel: ImagePanel,
                 process_dock: QDockWidget,
                 settings_dock: QDockWidget,
                 output_dock: QDockWidget
        ):
        super().__init__()
        self.setObjectName("AppMenuBar")

        # -- private fields --
        self.theme = app_state.view.theme
        self.image_panel = image_panel
        self.process_dock = process_dock
        self.settings_dock = settings_dock
        self.output_dock = output_dock

        # === the actual menu ==
        # -- file --
        self.file_menu = self.addMenu("File")

        # open
        self.open_file_menu = self.file_menu.addMenu("Open...")

        open_settings_action = QAction("Settings file", self)
        open_settings_action.triggered.connect(self.open_settings_triggered.emit)

        open_image_action = QAction("Image file(s)", self)
        open_image_action.triggered.connect(self.open_images_triggered.emit)
        
        open_seg_action = QAction("Segmentation file(s)", self)

        self.open_file_menu.addActions([
            open_settings_action, 
            open_image_action, 
            open_seg_action
        ])
        # Ctrl+O shortcut
        open_menu_shortcut = QAction(self)
        open_menu_shortcut.setShortcut(QKeySequence("Ctrl+O"))
        open_menu_shortcut.triggered.connect(
            lambda: self._popup_submenu(self.open_file_menu)
        )
        self.addAction(open_menu_shortcut)

        # save
        self.save_file_menu = self.file_menu.addMenu("Save...")

        save_settings_action = QAction("Current settings", self)
        save_settings_action.triggered.connect(self.save_settings_triggered.emit)

        save_image_view_action = QAction("Current image view", self)
        save_image_view_action.triggered.connect(self.save_image_view_triggered.emit)

        self.save_file_menu.addActions([
            save_settings_action, 
            save_image_view_action
        ])
        # Ctrl+S shortcut
        save_menu_shortcut = QAction(self)
        save_menu_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        save_menu_shortcut.triggered.connect(
            lambda: self._popup_submenu(self.save_file_menu)
        )
        self.addAction(save_menu_shortcut)

        # close files
        close_files_action = QAction("Close multiple files", self)
        close_files_action.triggered.connect(self._handle_close_files)
        self.file_menu.addAction(close_files_action)

        # exit
        self.file_menu.addSeparator()

        self.exit_action = QAction("Exit", self)
        self.file_menu.addAction(self.exit_action)

        # -- view --
        view_menu = self.addMenu("View")
        
        # panel visibility
        view_theme_menu = view_menu.addMenu("Panels")
        # process
        self.view_process_action = QAction("Batch Processing", self)
        self.view_process_action.setCheckable(True)
        self.view_process_action.triggered.connect(lambda: self._update_process_visibility(toggle=True))
        # settings
        self.view_settings_action = QAction("Segmentation Settings", self)
        self.view_settings_action.setCheckable(True)
        self.view_settings_action.triggered.connect(lambda: self._update_settings_visibility(toggle=True))
        # output
        self.view_output_action = QAction("Output", self)
        self.view_output_action.setCheckable(True)
        self.view_output_action.triggered.connect(lambda: self._update_output_visibility(toggle=True))

        view_theme_menu.addAction(self.view_process_action)
        view_theme_menu.addAction(self.view_settings_action)
        view_theme_menu.addAction(self.view_output_action)
        # sync menu actions with actual visibility
        self.process_dock.visibilityChanged.connect(
            self.view_process_action.setChecked
        )
        self.settings_dock.visibilityChanged.connect(
            self.view_settings_action.setChecked
        )
        self.output_dock.visibilityChanged.connect(
            self.view_output_action.setChecked
        )

        # color themes
        view_theme_menu = view_menu.addMenu("Color theme")

        self.view_theme_light_action = QAction("Light", self)
        self.view_theme_light_action.setCheckable(True)
        self.view_theme_light_action.triggered.connect(lambda: self._update_theme('light'))

        self.view_theme_dark_action = QAction("Dark", self)
        self.view_theme_dark_action.setCheckable(True)
        self.view_theme_dark_action.triggered.connect(lambda: self._update_theme('dark'))

        #TODO: fix dark color theme
        self.view_theme_dark_action.setDisabled(True)

        view_theme_menu.addActions([
            self.view_theme_light_action,
            self.view_theme_dark_action
        ])
        self._update_theme(self.theme)

        # reset view
        view_menu.addSeparator()
        self.reset_view_action = QAction("Reset view", self)
        self.reset_view_action.triggered.connect(self.reset_view_triggered.emit)
        view_menu.addAction(self.reset_view_action)
    
    def _popup_submenu(self, submenu: QMenu):
        """Show the given menu."""
        # open File menu
        file_action = self.file_menu.menuAction()
        file_rect = self.actionGeometry(file_action)
        file_pos = self.mapToGlobal(file_rect.bottomLeft())

        self.file_menu.popup(file_pos)

        # open submenu
        submenu_action = submenu.menuAction()
        self.file_menu.setActiveAction(submenu_action)
    
    def _handle_close_files(self):
        """Show dialog for selecting files to close."""
        image_files = self.image_panel.get_image_files()
        seg_files = self.image_panel.get_seg_files()
        if not image_files and not seg_files:
            return 
        
        dialog = RemoveFilesDialog(
            image_files=image_files,
            seg_files=seg_files,
            parent=self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        images_to_remove = dialog.selected_image_files()
        segs_to_remove = dialog.selected_seg_files()
        if not images_to_remove and not segs_to_remove:
            return
        
        self.close_files_triggered.emit(images_to_remove + segs_to_remove)
    
    def _update_process_visibility(self, toggle: bool = False):
        """Update the `ProcessPanel`'s visibility, action, and emit signal."""
        if toggle:
            visible = not self.process_dock.isVisible()
        else:
            visible = self.process_dock.isVisible()

        self.process_dock.setVisible(visible)
        self.view_process_action.setChecked(visible)
        self.process_visible_changed.emit(visible)
    
    def _update_settings_visibility(self, toggle: bool = False):
        """Update the `SettingsPanel`'s visibility, action, and emit signal."""
        if toggle:
            visible = not self.settings_dock.isVisible()
        else:
            visible = self.settings_dock.isVisible()

        self.settings_dock.setVisible(visible)
        self.view_settings_action.setChecked(visible)
        self.settings_visible_changed.emit(visible)
    
    def _update_output_visibility(self, toggle: bool = False):
        """Update the `OutputPanel`'s visibility, action, and emit signal."""
        if toggle:
            visible = not self.output_dock.isVisible()
        else:
            visible = self.output_dock.isVisible()
            
        self.output_dock.setVisible(visible)
        self.view_output_action.setChecked(visible)
        self.output_visible_changed.emit(visible)

    def _update_theme(self, theme: str):
        """Set theme, update the check marks in each action and emit signal."""
        self.theme = theme
        self.view_theme_light_action.setChecked(self.theme == 'light')
        self.view_theme_dark_action.setChecked(self.theme == 'dark')
        self.theme_changed.emit(self.theme)
    
    def get_theme(self) -> str:
        """Return the application's color theme."""
        return self.theme
    
    def get_exit_action(self) -> QAction:
        """Return the `MenuBar`'s exit action"""
        return self.exit_action