from PySide6.QtCore import (
    Qt,
    QSize
)
from PySide6.QtGui import (
    QDoubleValidator
)
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout, 
    QTextEdit,
    QLabel,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QSizePolicy,
    QLineEdit,
    QComboBox
)

class ScaleParameter(QFrame):
    """Adjustable fields for segmentation settings."""
    
    def __init__(self,
                 value: float
        ):
        super().__init__()
        self.setObjectName("ScaleParameter")
        self.setAutoFillBackground(True)

        # -- init layout --
        hlayout = QHBoxLayout(self)

        # label
        label = QLabel("Dist. per px")
        hlayout.addWidget(label)

        # number field
        field = QLineEdit()
        field.setFixedWidth(100)
        field.setValidator(QDoubleValidator())
        field.setText(str(value))
        hlayout.addWidget(field)

        # units dropdown
        units = QComboBox()
        units.setFixedWidth(50)
        units.addItem("µm")
        units.addItem("nm")

        hlayout.addWidget(units)
        
        # add layout to current widget
        self.setLayout(hlayout)



