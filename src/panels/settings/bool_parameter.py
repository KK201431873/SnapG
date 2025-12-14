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
    QComboBox,
    QCheckBox
)

class BoolParameter(QFrame):
    """Adjustable fields for segmentation settings."""
    
    def __init__(self,
                 title: str,
                 value: bool
        ):
        super().__init__()
        self.setObjectName("ScaleParameter")
        self.setAutoFillBackground(True)

        # -- init layout --
        hlayout = QHBoxLayout(self)

        # label
        label = QLabel(title)
        hlayout.addWidget(label)

        # units dropdown
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(value)
        hlayout.addWidget(self.checkbox)
        
        # add layout to current widget
        self.setLayout(hlayout)
    
    def get_checkbox(self) -> QCheckBox:
        """Return this parameter's QCheckBox."""
        return self.checkbox



