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
    QMainWindow,
    QMainWindow, 
    QDockWidget, 
    QWidget,
    QScrollArea,
    QFrame,
    QFileDialog,
    QApplication,
    QStyle,
    QVBoxLayout
)

from panels.image.image_panel import ImagePanel
from panels.process.process_panel import ProcessPanel
from panels.settings.settings_panel import SettingsPanel
from panels.output.output_panel import OutputPanel
from panels.menu.menu_bar import MenuBar
from panels.filetabs.file_tabs import FileTabSelector

from models import AppState, View, Settings

from save_load import load_state, write_state
from styles.style_manager import get_style_sheet

from datetime import datetime
from pathlib import Path
import sys

class MainWindow(QMainWindow):
    """SnapG Application Window."""

    image_panel: ImagePanel
    process_panel: ProcessPanel
    settings_panel: SettingsPanel
    output_panel: OutputPanel
    menu_bar: MenuBar
    file_tabs: FileTabSelector

    def __init__(self, app_state: AppState):
        super().__init__()
        
        # -- Init panels --
        self.process_panel = ProcessPanel(app_state)
        self.settings_panel = SettingsPanel(app_state)
        self.output_panel = OutputPanel(app_state)
        self.image_panel = ImagePanel(app_state, self.settings_panel)
        self.settings_panel.settings_changed.connect(self.image_panel.receive_settings)
        self.settings_panel.emit_fields() # update ImagePanel

        # File tabs
        self.file_tabs = FileTabSelector(app_state)
        self.image_panel.files_changed.connect(self.update_file_tabs)
        self.file_tabs.tab_changed.connect(self.image_panel._set_current_file)
        self.file_tabs.close_file_requested.connect(self.on_close_file_requested)
        self.image_panel.emit_files()

        # create background widget (will contain image widget)
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        # stack file tabs above image panel
        central_layout.addWidget(self.file_tabs)
        central_layout.addWidget(self.image_panel, 1)
        # z management
        self.setCentralWidget(central)
        self._central = central

        # docks
        self.process_dock = self.create_fixed_dock("Batch Processing", self.process_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.settings_dock = self.create_fixed_dock("Segmentation Settings", self.settings_panel, Qt.DockWidgetArea.RightDockWidgetArea, scrollable=True)
        self.output_dock = self.create_fixed_dock("Output", self.output_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
        # load in previous dock state
        self.set_dock_state(app_state.view)

        # -- Menu bar --
        self.menu_bar = MenuBar(
            app_state,
            self.image_panel,
            self.process_dock,
            self.settings_dock,
            self.output_dock
        )
        # File signals
        self.menu_bar.open_settings_triggered.connect(self.open_settings_file)
        self.menu_bar.open_images_triggered.connect(self.open_image_files)
        self.menu_bar.save_settings_triggered.connect(self.save_settings_to_file)
        self.menu_bar.close_files_triggered.connect(self.close_multiple_files)
        self.menu_bar.get_exit_action().triggered.connect(self.close)
        # View signals
        self.menu_bar.theme_changed.connect(self.refresh_style)
        self.menu_bar.reset_view_triggered.connect(self.reset_view)
        self.menu_bar.process_visible_changed.connect(self.process_dock.setVisible)
        self.menu_bar.settings_visible_changed.connect(self.settings_dock.setVisible)
        self.menu_bar.output_visible_changed.connect(self.output_dock.setVisible)
        # add to app widget
        self.setMenuBar(self.menu_bar)

    def eventFilter(self, obj, event: QEvent):
        if obj is self._central:
            self.resize_image_panel()
        return super().eventFilter(obj, event)
    
    def resize_image_panel(self):
        menu_height = self.menuBar().height() if self.menuBar() else 0

        x_offset = -self.process_dock.width() if self.process_dock.isVisible() else \
                    self.style().pixelMetric(QStyle.PixelMetric.PM_SplitterWidth) - 1
        self.image_panel.setGeometry(
            x_offset,
            menu_height,
            self.width(),
            self.height() - menu_height
        )
    
    def create_fixed_dock(self,
                          title: str,
                          widget: QWidget, 
                          area: Qt.DockWidgetArea, 
                          scrollable: bool = False
    ) -> QDockWidget:
        """Create and return a new QDockWidget fixed in the given location."""
        dock = QDockWidget(title, self)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setObjectName(widget.__class__.__name__)
        
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setObjectName(widget.__class__.__name__)

        if scrollable:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            dock.setWidget(scroll)
        else:
            dock.setWidget(widget)

        self.addDockWidget(area, dock)
        return dock

    def update_file_tabs(self, image_files: list[Path], seg_files: list[Path], current_file: Path):
        """Connects `ImagePanel`'s `files_changed` signal to `FileTabSelector` and syncs state."""
        self.file_tabs.set_files(image_files, seg_files)
        self.file_tabs.set_current_file(current_file)
    
    def on_close_file_requested(self, path: Path):
        """Relay a file close request from `FileTabSelector` to `ImagePanel`."""
        self.image_panel.remove_files([path])
    
    def open_image_files(self):
        """Show file dialog to open image files."""
        file_names, _ = QFileDialog.getOpenFileNames(
            parent=self, 
            caption="Open Image(s)",
            filter="Images (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif)"
        )
        file_paths = [Path(s) for s in file_names]
        self.image_panel.add_images(file_paths)

    def open_settings_file(self):
        """Show file dialog to open settings file."""
        file_name, _ = QFileDialog.getOpenFileName(
            parent=self, 
            caption="Open Settings",
            filter="SNPG Files (*.snpg)",
            selectedFilter="SNPG Files (*.snpg)"
        )
        state, valid = load_state(path=Path(file_name))
        if valid:
            self.settings_panel.set_settings(state.settings)

    def save_settings_to_file(self):
        """Show file dialog to save settings to a file."""
        formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name, _ = QFileDialog.getSaveFileName(
            parent=self, 
            caption="Save Settings",
            dir=f"{formatted_datetime}.snpg",
            filter="SNPG Files (*.snpg)",
            selectedFilter="SNPG Files (*.snpg)"
        )
        if file_name:
            write_state(self.get_app_state(), Path(file_name))
    
    def close_multiple_files(self, file_paths: list[Path]):
        """Close multiple user-requested files."""
        self.image_panel.remove_files(file_paths)

    def refresh_style(self, theme: str):
        """Set the app style sheet according to the given theme."""
        app.setStyleSheet(get_style_sheet(theme))

    def reset_view(self):
        """Reset docks and image panel view to defaults."""
        default_state = AppState.default()
        self.set_dock_state(default_state.view)
        self.image_panel.set_image_view(default_state.image_panel_state)

    def set_dock_state(self, view: View):
        """Set docks to the given view."""
        # visibilities
        self.process_dock.setVisible(view.process_panel_visible)
        self.settings_dock.setVisible(view.settings_panel_visible)
        self.output_dock.setVisible(view.output_panel_visible)
        # sizes
        self.resizeDocks(
            [self.process_dock, self.settings_dock],
            [view.process_panel_width, view.settings_panel_width],
            Qt.Orientation.Horizontal
        )
        self.resizeDocks(
            [self.output_dock], [view.output_panel_height], Qt.Orientation.Vertical
        )

    def closeEvent(self, event):
        self.image_panel.closeEvent(event)
        write_state(self.get_app_state())

    def get_app_state(self) -> AppState:
        """Returns the latest `AppState` object."""
        return AppState(
            view=View(
                theme=self.menu_bar.get_theme(),

                process_panel_visible=self.process_dock.isVisible(),
                settings_panel_visible=self.settings_dock.isVisible(),
                output_panel_visible=self.output_dock.isVisible(),

                process_panel_width=self.process_dock.width(),
                settings_panel_width=self.settings_dock.width(),
                output_panel_height=self.output_dock.height()
            ),
            settings=self.settings_panel.to_settings(),
            image_panel_state=self.image_panel.to_state()
        )

        
app_state: AppState
if __name__=="__main__":
    app = QApplication([])

    # Load state
    app_state, _ = load_state()
    app.setStyleSheet(get_style_sheet(app_state.view.theme))

    window = MainWindow(app_state)
    window.setMinimumSize(QSize(960,540))

    # Window aesthetics
    window.setWindowTitle("SnapG")
    window.setWindowIcon(QIcon("assets/favicon.ico"))
    if sys.platform == "win32":
        # Windows 11 taskbar icon fix
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "SnapG.App.1"
        )

    window.show()
    app.exec()