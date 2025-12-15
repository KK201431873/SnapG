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
    QMessageBox,
    QApplication,
    QStyle
)

from panels.image.image_panel import ImagePanel
from panels.process.process_panel import ProcessPanel
from panels.settings.settings_panel import SettingsPanel
from panels.output.output_panel import OutputPanel
from panels.menu.menu_bar import MenuBar

from models import AppState, View, Settings

from save_load import load_state, write_state
from styles.style_manager import get_style_sheet

import sys

class MainWindow(QMainWindow):
    """SnapG Application Window."""

    image_panel: ImagePanel
    process_panel: ProcessPanel
    settings_panel: SettingsPanel
    output_panel: OutputPanel
    menu_bar: MenuBar

    def __init__(self, app_state: AppState):
        super().__init__()
        
        # -- Init panels --
        self.image_panel = ImagePanel(app_state)
        self.process_panel = ProcessPanel(app_state)
        self.settings_panel = SettingsPanel(app_state)
        self.output_panel = OutputPanel(app_state)

        # create background widget (will contain image widget)
        empty_central = QWidget()
        empty_central.setMinimumSize(1, 1)
        self.setCentralWidget(empty_central)
        self.image_panel.setParent(empty_central)
        self.image_panel.lower()
        self.image_panel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        # resize events
        empty_central.installEventFilter(self)
        self._central = empty_central

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
        self.menu_bar.get_exit_action().triggered.connect(self.close)
        self.menu_bar.theme_changed.connect(self.refresh_style)
        self.menu_bar.reset_view.connect(lambda: self.set_dock_state(View.default()))
        # panel visibility signals
        self.menu_bar.process_visible_changed.connect(self.process_dock.setVisible)
        self.menu_bar.settings_visible_changed.connect(self.settings_dock.setVisible)
        self.menu_bar.output_visible_changed.connect(self.output_dock.setVisible)
        # add to app widget
        self.setMenuBar(self.menu_bar)

    def eventFilter(self, obj, event: QEvent):
        if obj is self._central:
            self._resize_image_panel()
        return super().eventFilter(obj, event)
    
    def _resize_image_panel(self):
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

    def refresh_style(self, theme: str):
        """Set the app style sheet according to the given theme."""
        app.setStyleSheet(get_style_sheet(theme))

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
        write_state(self.get_app_state())

    def get_app_state(self) -> AppState:
        """Returns the latest `AppState` object."""
        return AppState(
            view=View(
                theme=self.menu_bar.get_theme(),

                process_panel_visible=self.process_panel.isVisible(),
                settings_panel_visible=self.settings_panel.isVisible(),
                output_panel_visible=self.output_panel.isVisible(),

                process_panel_width=self.process_panel.width(),
                settings_panel_width=self.settings_panel.width(),
                output_panel_height=self.output_panel.height()
            ),
            settings=self.settings_panel.to_settings()
        )

        
app_state: AppState
if __name__=="__main__":
    app = QApplication([])

    # Load state
    app_state = load_state()
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