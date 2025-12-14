from PySide6.QtCore import (
    Qt,
    QSize
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
    QSizePolicy
)

class NonScrollSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def wheelEvent(self, event):
        event.ignore()

class NonScrollSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()

class NonScrollDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event):
        event.ignore()

class SliderParameter(QFrame):
    """Adjustable fields for segmentation settings."""
    
    def __init__(self, 
                 name: str, 
                 value: int | float,
                 valstep: int | float,
                 bounds: tuple[int, int] | tuple[float, float],
                 units: str = ""
        ):
        super().__init__()
        self.setObjectName("Parameter")
        self.setAutoFillBackground(True)
        is_float = any(isinstance(x, float) for x in (value, valstep, *bounds))

        # -- init layout --
        hlayout = QHBoxLayout(self)

        # label
        label = QLabel(name)
        hlayout.addWidget(label)

        # slider
        self.slider = NonScrollSlider(Qt.Orientation.Horizontal, self)
        if is_float:
            scale = int(1/valstep)
            self.slider.setRange(
                int(bounds[0] * scale),
                int(bounds[1] * scale)
            )
            self.slider.setSingleStep(1)
            self.slider.setValue(int(value * scale))
        else:
            scale = 1
            self.slider.setRange(int(bounds[0]), int(bounds[1]))
            self.slider.setSingleStep(int(valstep))
            self.slider.setValue(int(value))
        hlayout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignVCenter)

        # spinbox
        if is_float:
            self.spin = NonScrollDoubleSpinBox()
            self.spin.setRange(*bounds)
            self.spin.setSingleStep(valstep)
            self.spin.setValue(value)
        else:
            self.spin = NonScrollSpinBox()
            self.spin.setRange(int(bounds[0]), int(bounds[1]))
            self.spin.setSingleStep(int(valstep))
            self.spin.setValue(int(value))
        self.spin.setSuffix(f" {units}")
        self.spin.setFixedSize(QSize(100, 25))
        hlayout.addWidget(self.spin)
        
        # add layout to current widget
        self.setLayout(hlayout)

        # -- event handling --
        self.slider.valueChanged.connect(
            lambda v: self.spin.setValue(v / scale)
        )

        self.spin.valueChanged.connect(
            lambda v: self.slider.setValue(int(v * scale))
        )
    
    def get_slider(self) -> QSlider:
        """Return this parameter's QSlider."""
        return self.slider
    
    def get_spin_box(self) -> QSpinBox | QDoubleSpinBox:
        """Return this parameter's QSpinBox."""
        return self.spin


