from PySide6.QtCore import (
    Qt,
    QSize
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QLabel
)

from panels.settings.scale_parameter import ScaleParameter
from panels.settings.parameter import Parameter

class SettingsPanel(QWidget):
    """Adjustable fields for segmentation settings."""

    
    def __init__(self):
        super().__init__()

        # init vertical layout
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(1, 0, 0, 0)

        # params
        self.vlayout.addWidget(ScaleParameter(0))
        self.new_param("Threshold", 0, 1, (0, 255))
        self.new_param("Radius", 0, 1, (0, 20))
        self.new_param("Dilate", 0, 1, (0, 50))
        self.new_param("Erode", 0, 1, (0, 50))
        self.new_param("Min size", 0, 1000, (0, 200000))
        self.new_param("Max size", 0, 1000, (0, 1000000))
        self.new_param("Convexity", 0, 0.01, (0, 1))
        self.new_param("Circularity", 0, 0.01, (0, 1))
        
        # add layout to current widget
        self.setLayout(self.vlayout)

    def new_param(self, 
                 name: str, 
                 value: int | float,
                 valstep: int | float,
                 bounds: tuple[int, int] | tuple[float, float],
                 units: str = ""
        ):
        self.vlayout.addWidget(Parameter(name, value, valstep, bounds, units=units))