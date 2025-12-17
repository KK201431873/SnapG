from PySide6.QtCore import (
    Qt,
    QSize,
    QLocale
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

from panels.modified_widgets import NonScrollComboBox

class ScaleParameter(QFrame):
    """Adjustable fields for segmentation settings."""
    
    def __init__(self,
                 value: float,
                 scale_units: str
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
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        validator.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.field = QLineEdit()
        self.field.setMaximumWidth(100)
        self.field.setValidator(validator)
        self.field.setText(str(value))
        hlayout.addWidget(self.field)

        # units dropdown
        self.units = NonScrollComboBox()
        self.units.setFixedWidth(50)
        self.units.addItem("µm")
        self.units.addItem("nm")
        if scale_units in ["µm", "nm"]:
            self.units.setCurrentText(scale_units)

        hlayout.addWidget(self.units)
        
        # add layout to current widget
        self.setLayout(hlayout)

    def get_field_widget(self) -> QLineEdit:
        """Return this parameter's QLineEdit"""
        return self.field
    
    def get_combo_box_widget(self) -> QComboBox:
        """Return this parameter's QComboBox"""
        return self.units


