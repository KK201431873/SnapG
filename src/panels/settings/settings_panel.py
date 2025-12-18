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
    QLabel,
    QGroupBox
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
        self.vlayout.setSpacing(10)

        # params
        self.scale_prm_widget = ScaleParameter(settings.scale, settings.scale_units)
        self.scale_prm_widget.get_field_widget().textChanged.connect(self.emit_fields)
        self.scale_prm_widget.get_combo_box_widget().activated.connect(self.emit_fields)
        self.res_divisor_prm_widget = self.new_slider("Image Res. Divisor", settings.resolution_divisor, 0.01, (1, 50))

        self.show_orig_prm_widget = self.new_checkbox("Show Original", settings.show_original)
        self.show_thresh_prm_widget = self.new_checkbox("Show Threshold", settings.show_threshold)
        self.show_text_prm_widget = self.new_checkbox("Show Text", settings.show_text)

        self.thresh_prm_widget = self.new_slider("Threshold", settings.threshold, 1, (0, 255))
        self.radius_prm_widget = self.new_slider("Radius", settings.radius, 1, (0, 20))
        self.dilate_prm_widget = self.new_slider("Dilate", settings.dilate, 1, (0, 50))
        self.erode_prm_widget = self.new_slider("Erode", settings.erode, 1, (0, 50))
        self.min_size_prm_widget = self.new_slider("Min size", settings.min_size, 0.001, (0.000, 1.000))
        self.max_size_prm_widget = self.new_slider("Max size", settings.max_size, 0.001, (0.000, 1.000))
        self.convexity_prm_widget = self.new_slider("Convexity", settings.convexity, 0.01, (0, 1))
        self.circularity_prm_widget = self.new_slider("Circularity", settings.circularity, 0.01, (0, 1))
        self.thick_percent_prm_widget = self.new_slider("Thickness %ile", settings.thickness_percentile, 1, (0, 100))
        
        # image controls
        image_controls_box = QGroupBox("Image Controls")
        image_controls_layout = QVBoxLayout(image_controls_box)
        image_controls_layout.setContentsMargins(0, 5, 0, 5)
        self.vlayout.addWidget(image_controls_box)

        self.scale_prm_widget.setToolTip("Distance Per Pixel: Conversion from image pixel distance to real distance. Scales with Image Resolution Divider.")
        self.res_divisor_prm_widget.setToolTip("Image Resolution Divisor: How much to downscale the image by. For example, a value of 4 would shrink a 4096x4096 image to 1024x1024 before feeding it into the segmentation algorithm.")
        self.show_orig_prm_widget.setToolTip("Show Original: Whether to show the original image file. Useful for visually validating contours and thresholds.")
        self.show_thresh_prm_widget.setToolTip("Show Threshold: Whether to show the thresholded binary (black and white) image. Useful for tuning OpenCV parameters.")
        self.show_text_prm_widget.setToolTip("Show Text: Whether to show axon numbers and g-ratios on the image. Useful for checking data in the Output panel.")

        image_controls_layout.addWidget(self.scale_prm_widget)
        image_controls_layout.addWidget(self.res_divisor_prm_widget)
        image_controls_layout.addWidget(self.show_orig_prm_widget)
        image_controls_layout.addWidget(self.show_thresh_prm_widget)
        image_controls_layout.addWidget(self.show_text_prm_widget)

        # opencv parameters
        opencv_parameters_box = QGroupBox("OpenCV Parameters")
        opencv_parameters_layout = QVBoxLayout(opencv_parameters_box)
        opencv_parameters_layout.setContentsMargins(0, 5, 0, 5)
        self.vlayout.addWidget(opencv_parameters_box)
        
        self.thresh_prm_widget.setToolTip("Threshold: The minimum brightness value for a pixel to be part of an axon's interior. Ranges from 0 (black) to 1 (white).")
        self.radius_prm_widget.setToolTip("Radius: The size of the circular smoothing kernel, in pixels. Greater values reduce noise and lower values increase detail.")
        self.dilate_prm_widget.setToolTip("Dilate: How much to expand the white threshold region by, in pixels. Can be used with Erode to close small black gaps in the threshold image (morphological closing).")
        self.erode_prm_widget.setToolTip("Erode: How much to contract the white threshold region by, in pixels. Can be used with Dilate to close small black gaps in the threshold image (morphological closing)")
        self.min_size_prm_widget.setToolTip("Min Size: The minimum contour bounding box size as a proportion of the entire image in order to be classified as an axon. Ranges from 0 (nothing) to 1 (the whole image).")
        self.max_size_prm_widget.setToolTip("Max Size: The maximum contour bounding box size as a proportion of the entire image in order to be classified as an axon. Ranges from 0 (nothing) to 1 (the whole image).")
        self.convexity_prm_widget.setToolTip("Convexity: The minimum convexity for a contour to be classified as an axon. Convexity is calculated by (contour area) / (convex hull area). Ranges from 0 (a thin line) to 1 (perfectly convex)")
        self.circularity_prm_widget.setToolTip("Circularity: The minimum circularity for a contour to be classified as an axon. Circularity is calculated by 4pi * (contour area) / (contour perimeter) ^ 2. Ranges from 0 (a thin line) to 1 (perfect circle)")
        self.thick_percent_prm_widget.setToolTip("Thickness Percentile: Used to extract myelin thickness from a numerical distribution. Higher values tend to thicker myelin estimations, while lower values tend to thinner myelin. Ranges from 0 to 100.")

        opencv_parameters_layout.addWidget(self.thresh_prm_widget)
        opencv_parameters_layout.addWidget(self.radius_prm_widget)
        opencv_parameters_layout.addWidget(self.dilate_prm_widget)
        opencv_parameters_layout.addWidget(self.erode_prm_widget)
        opencv_parameters_layout.addWidget(self.min_size_prm_widget)
        opencv_parameters_layout.addWidget(self.max_size_prm_widget)
        opencv_parameters_layout.addWidget(self.convexity_prm_widget)
        opencv_parameters_layout.addWidget(self.circularity_prm_widget)
        opencv_parameters_layout.addWidget(self.thick_percent_prm_widget)
        
        # add layout to current widget
        self.setLayout(self.vlayout)

        # -- connect signal --
        self.settings_changed.connect(self.receive_settings)
    
    def new_checkbox(self,
                     name: str,
                     value: bool
        ) -> BoolParameter:
        """Creates a new `BoolParameter` widget with the given values."""
        bool_parameter = BoolParameter(name, value)
        bool_parameter.get_checkbox().stateChanged.connect(self.emit_fields)
        return bool_parameter


    def new_slider(self, 
                 name: str, 
                 value: int | float,
                 valstep: int | float,
                 bounds: tuple[int, int] | tuple[float, float],
                 units: str = ""
        ) -> SliderParameter:
        """Creates a new `SliderParameter` widget with the given values."""
        slider_parameter = SliderParameter(name, value, valstep, bounds, units=units)
        slider_parameter.get_slider().valueChanged.connect(self.emit_fields)
        slider_parameter.get_spin_box().valueChanged.connect(self.emit_fields)
        return slider_parameter
    
    def emit_fields(self):
        """Emits signal containing all settings fields."""
        try:
            current_settings = self.to_settings() # might error because text fields could be empty which can't be converted to numbers
            self.settings_changed.emit(current_settings)
        except Exception as e:
            pass

    def set_settings(self, settings: Settings):
        """Set current parameter values to the given settings."""
        self.scale_prm_widget.get_field_widget().setText(str(settings.scale))
        self.scale_prm_widget.get_combo_box_widget().setCurrentText(settings.scale_units)
        self.res_divisor_prm_widget.get_spin_box().setValue(settings.resolution_divisor) # type: ignore
        self.show_orig_prm_widget.get_checkbox().setChecked(settings.show_original)
        self.show_thresh_prm_widget.get_checkbox().setChecked(settings.show_threshold)
        self.show_text_prm_widget.get_checkbox().setChecked(settings.show_text)
        self.thresh_prm_widget.get_spin_box().setValue(settings.threshold)
        self.radius_prm_widget.get_spin_box().setValue(settings.radius)
        self.dilate_prm_widget.get_spin_box().setValue(settings.dilate)
        self.erode_prm_widget.get_spin_box().setValue(settings.erode)
        self.min_size_prm_widget.get_spin_box().setValue(settings.min_size) # type: ignore
        self.max_size_prm_widget.get_spin_box().setValue(settings.max_size) # type: ignore
        self.convexity_prm_widget.get_spin_box().setValue(settings.convexity) # type: ignore
        self.circularity_prm_widget.get_spin_box().setValue(settings.circularity) # type: ignore
        self.thick_percent_prm_widget.get_spin_box().setValue(settings.thickness_percentile)
    
    def to_settings(self) -> Settings:
        """Return all current field values as a `Settings` object."""
        try:
            scale = float(self.scale_prm_widget.get_field_widget().text())
        except Exception as e:
            scale = 1.0
        return Settings(
            scale = scale,
            scale_units = self.scale_prm_widget.get_combo_box_widget().currentText(),
            resolution_divisor=self.res_divisor_prm_widget.get_spin_box().value(),
            show_original = self.show_orig_prm_widget.get_checkbox().isChecked(),
            show_threshold = self.show_thresh_prm_widget.get_checkbox().isChecked(),
            show_text = self.show_text_prm_widget.get_checkbox().isChecked(),
            threshold = int(self.thresh_prm_widget.get_spin_box().value()),
            radius = int(self.radius_prm_widget.get_spin_box().value()),
            dilate = int(self.dilate_prm_widget.get_spin_box().value()),
            erode = int(self.erode_prm_widget.get_spin_box().value()),
            min_size = self.min_size_prm_widget.get_spin_box().value(),
            max_size = self.max_size_prm_widget.get_spin_box().value(),
            convexity = self.convexity_prm_widget.get_spin_box().value(),
            circularity = self.circularity_prm_widget.get_spin_box().value(),
            thickness_percentile = int(self.thick_percent_prm_widget.get_spin_box().value())
        )
        
    def receive_settings(self, settings: Settings):
        """Logic for disabling/enabling Show Threshold checkbox."""
        if settings.show_original:
            self.show_thresh_prm_widget.setDisabled(True)
            self.show_text_prm_widget.setDisabled(True)
        else:
            if settings.show_threshold:
                self.show_thresh_prm_widget.setDisabled(False)
                self.show_text_prm_widget.setDisabled(True)
            else:
                self.show_thresh_prm_widget.setDisabled(False)
                self.show_text_prm_widget.setDisabled(False)
