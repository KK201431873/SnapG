from PySide6.QtCore import (
    Qt,
    QSize
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMainWindow, 
    QDockWidget, 
    QWidget,
    QScrollArea,
    QFrame,
    QMessageBox,
    QApplication
)

from panels.image.image_panel import ImagePanel
from panels.process.process_panel import ProcessPanel
from panels.settings.settings_panel import SettingsPanel
from panels.output.output_panel import OutputPanel
from panels.menu.menu_bar import MenuBar

from models import AppState, Style, Settings

from save_load import load_state, write_state
from styles.style_manager import get_style_sheet

from typing import cast

class MainWindow(QMainWindow):
    """SnapG Application Window."""

    image_panel: ImagePanel
    process_panel: ProcessPanel
    settings_panel: SettingsPanel
    output_panel: OutputPanel
    menu_bar: MenuBar

    def __init__(self):
        super().__init__()
        
        # Init panels
        self.image_panel = ImagePanel()
        self.process_panel = ProcessPanel()
        self.settings_panel = SettingsPanel(app_state.settings)
        self.output_panel = OutputPanel()
        self.menu_bar = MenuBar(
            app_state,
            self.image_panel,
            self.process_panel,
            self.settings_panel,
            self.output_panel
        )
        self.menu_bar.get_exit_action().triggered.connect(self.close)
        self.menu_bar.theme_changed.connect(self.refresh_style)

        self.create_fixed_dock("Batch Processing", self.process_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.create_fixed_dock("Segmentation Settings", self.settings_panel, Qt.DockWidgetArea.RightDockWidgetArea, scrollable=True)
        self.create_fixed_dock("Output", self.output_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setCentralWidget(self.image_panel)

        # Menu bar
        self.setMenuBar(self.menu_bar)
    
    def create_fixed_dock(self,
                          title: str,
                          widget: QWidget, 
                          area: Qt.DockWidgetArea, 
                          scrollable: bool = False
    ):
        """Create a new QDockWidget fixed in the given location."""
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

    def refresh_style(self, theme: str):
        """Set the app style sheet according to the given theme."""
        app.setStyleSheet(get_style_sheet(theme))
    
    def closeEvent(self, event):
        write_state(self.get_app_state())
    
    def get_app_state(self) -> AppState:
        """Returns the latest `AppState` object."""
        return AppState(
            style=Style(
                theme=self.menu_bar.get_theme()
            ),
            settings=self.settings_panel.to_settings()
        )
        
app_state: AppState
if __name__=="__main__":
    app = QApplication([])

    # Load state
    app_state = load_state()
    app.setStyleSheet(get_style_sheet(app_state.style.theme))

    window = MainWindow()
    window.setMinimumSize(QSize(960,540))
    window.show()
    app.exec()