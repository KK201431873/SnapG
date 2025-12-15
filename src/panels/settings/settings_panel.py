from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    SIGNAL
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QLabel
)

from panels.settings.scale_parameter import ScaleParameter
from panels.settings.bool_parameter import BoolParameter
from panels.settings.slider_parameter import SliderParameter

from models import AppState, Settings

from pathlib import Path

class SettingsPanel(QWidget):
    """Adjustable fields for segmentation settings."""

    settings_changed = Signal(Settings)
    
    def __init__(self, app_state: AppState):
        super().__init__()
        settings = app_state.settings
        self.resize(QSize(400, self.height()))

        # init vertical layout
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(1, 0, 0, 0)

        # params
        self.scale_prm_widget = ScaleParameter(settings.scale, settings.scale_units)
        self.scale_prm_widget.get_field_widget().textChanged.connect(self.emit_fields)
        self.scale_prm_widget.get_combo_box_widget().activated.connect(self.emit_fields)
        self.res_divisor_prm_widget = self.new_param("Image Res. Divisor", settings.resolution_divisor, 0.01, (0, 10))

        self.show_orig_prm_widget = BoolParameter("Show Original", settings.show_original)
        self.show_orig_prm_widget.get_checkbox().stateChanged.connect(self.emit_fields)

        self.show_thresh_prm_widget = BoolParameter("Show Threshold", settings.show_threshold)
        self.show_thresh_prm_widget.get_checkbox().stateChanged.connect(self.emit_fields)

        self.thresh_prm_widget = self.new_param("Threshold", settings.threshold, 1, (0, 255))
        self.radius_prm_widget = self.new_param("Radius", settings.radius, 1, (0, 20))
        self.dilate_prm_widget = self.new_param("Dilate", settings.dilate, 1, (0, 50))
        self.erode_prm_widget = self.new_param("Erode", settings.erode, 1, (0, 50))
        self.min_size_prm_widget = self.new_param("Min size", settings.min_size, 1_000, (0, 200_000))
        self.max_size_prm_widget = self.new_param("Max size", settings.max_size, 1_000, (0, 1_000_000))
        self.convexity_prm_widget = self.new_param("Convexity", settings.convexity, 0.01, (0, 1))
        self.circularity_prm_widget = self.new_param("Circularity", settings.circularity, 0.01, (0, 1))
        self.thick_percent_prm_widget = self.new_param("Thickness %ile", settings.thickness_percentile, 1, (0, 100))
        
        # show visually
        self.vlayout.addWidget(self.scale_prm_widget)
        self.vlayout.addWidget(self.res_divisor_prm_widget)
        self.vlayout.addWidget(self.show_orig_prm_widget)
        self.vlayout.addWidget(self.show_thresh_prm_widget)
        self.vlayout.addWidget(self.thresh_prm_widget)
        self.vlayout.addWidget(self.radius_prm_widget)
        self.vlayout.addWidget(self.dilate_prm_widget)
        self.vlayout.addWidget(self.erode_prm_widget)
        self.vlayout.addWidget(self.min_size_prm_widget)
        self.vlayout.addWidget(self.max_size_prm_widget)
        self.vlayout.addWidget(self.convexity_prm_widget)
        self.vlayout.addWidget(self.circularity_prm_widget)
        self.vlayout.addWidget(self.thick_percent_prm_widget)
        
        # add layout to current widget
        self.setLayout(self.vlayout)

        # -- connect signal --
        self.settings_changed.connect(self.receive_settings)

        # emit once
        self.emit_fields()

    def new_param(self, 
                 name: str, 
                 value: int | float,
                 valstep: int | float,
                 bounds: tuple[int, int] | tuple[float, float],
                 units: str = ""
        ) -> SliderParameter:
        """Creates a new SliderParameter widget with the given values."""
        slider_parameter = SliderParameter(name, value, valstep, bounds, units=units)
        slider_parameter.get_slider().valueChanged.connect(self.emit_fields)
        slider_parameter.get_spin_box().valueChanged.connect(self.emit_fields)
        return slider_parameter
    
    def emit_fields(self):
        """Emits custom signal containing all settings fields."""
        self.settings_changed.emit(self.to_settings())

    def set_settings(self, settings: Settings):
        """Set current parameter values to the given settings."""
        self.scale_prm_widget.get_field_widget().setText(str(settings.scale))
        self.scale_prm_widget.get_combo_box_widget().setCurrentText(settings.scale_units)
        self.res_divisor_prm_widget.get_spin_box().setValue(settings.resolution_divisor) # type: ignore
        self.show_orig_prm_widget.get_checkbox().setChecked(settings.show_original)
        self.show_thresh_prm_widget.get_checkbox().setChecked(settings.show_threshold)
        self.thresh_prm_widget.get_spin_box().setValue(settings.threshold)
        self.radius_prm_widget.get_spin_box().setValue(settings.radius)
        self.dilate_prm_widget.get_spin_box().setValue(settings.dilate)
        self.erode_prm_widget.get_spin_box().setValue(settings.erode)
        self.min_size_prm_widget.get_spin_box().setValue(settings.min_size)
        self.max_size_prm_widget.get_spin_box().setValue(settings.max_size)
        self.convexity_prm_widget.get_spin_box().setValue(settings.convexity) # type: ignore
        self.circularity_prm_widget.get_spin_box().setValue(settings.circularity) # type: ignore
        self.thick_percent_prm_widget.get_spin_box().setValue(settings.thickness_percentile)
    
    def to_settings(self) -> Settings:
        """Return all current field values as a `Settings` object."""
        return Settings(
            scale = float(self.scale_prm_widget.get_field_widget().text()),
            scale_units = self.scale_prm_widget.get_combo_box_widget().currentText(),
            resolution_divisor=self.res_divisor_prm_widget.get_spin_box().value(),
            show_original = self.show_orig_prm_widget.get_checkbox().isChecked(),
            show_threshold = self.show_thresh_prm_widget.get_checkbox().isChecked(),
            threshold = int(self.thresh_prm_widget.get_spin_box().value()),
            radius = int(self.radius_prm_widget.get_spin_box().value()),
            dilate = int(self.dilate_prm_widget.get_spin_box().value()),
            erode = int(self.erode_prm_widget.get_spin_box().value()),
            min_size = int(self.min_size_prm_widget.get_spin_box().value()),
            max_size = int(self.max_size_prm_widget.get_spin_box().value()),
            convexity = self.convexity_prm_widget.get_spin_box().value(),
            circularity = self.circularity_prm_widget.get_spin_box().value(),
            thickness_percentile = int(self.thick_percent_prm_widget.get_spin_box().value())
        )
        
    def receive_settings(self, settings: Settings):
        """Logic for disabling/enabling Show Threshold checkbox."""
        if settings.show_original:
            self.show_thresh_prm_widget.setDisabled(True)
        else:
            self.show_thresh_prm_widget.setDisabled(False)
