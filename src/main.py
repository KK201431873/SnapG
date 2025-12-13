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
    QFrame
)

from panels.image.image_panel import ImagePanel
from panels.process.process_panel import ProcessPanel
from panels.settings.settings_panel import SettingsPanel
from panels.output.output_panel import OutputPanel

from app_state import load_save_state

class MainWindow(QMainWindow):
    """SnapG Application Window."""

    image_panel: QWidget
    process_panel: QWidget
    settings_panel: QWidget
    output_panel: QWidget

    def __init__(self):
        super().__init__()
        
        # Init panels
        self.image_panel = ImagePanel()
        self.process_panel = ProcessPanel()
        self.settings_panel = SettingsPanel()
        self.output_panel = OutputPanel()

        ## Set up docks
        self.create_fixed_dock("Batch Processing", self.process_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.create_fixed_dock("Segmentation Settings", self.settings_panel, Qt.DockWidgetArea.RightDockWidgetArea, scrollable=True)
        self.create_fixed_dock("Output", self.output_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setCentralWidget(self.image_panel)
    
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

if __name__=="__main__":
    app = QApplication([])

    window = MainWindow()
    window.setMinimumSize(QSize(960,540))
    load_save_state(app, verbose=False)
    
    window.show()
    app.exec()