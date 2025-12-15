from PySide6.QtCore import (
    QSize,
    Signal
)
from PySide6.QtGui import (
    QImage
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QMessageBox
)

from panels.settings.settings_panel import SettingsPanel
from panels.image.image_view import ImageView

from imgproc.process_image import process_image

from models import AppState, SegmentationData, ContourData, ImagePanelState, Settings

from pathlib import Path
from enum import Enum
import numpy.typing as npt
import numpy as np
import pickle
import cv2

class Mode(Enum):
    NO_IMAGE = 0
    TUNE = 1
    REVIEW = 2

class ImagePanel(QWidget):
    """Central image viewer and contour selector."""

    def __init__(self, app_state: AppState, settings_panel: SettingsPanel):
        super().__init__()
        self.settings_panel = settings_panel
        
        # init files lists and state
        self.image_files: list[Path] = [Path(p) for p in app_state.image_panel_state.image_files]
        self.seg_files: list[Path] = [Path(p) for p in app_state.image_panel_state.seg_files]
        current_file_str = app_state.image_panel_state.current_file
        self.current_file: Path | None = Path(current_file_str) if current_file_str != "" else None
        self.current_original_image: npt.NDArray | None = None
        self.display_image: npt.NDArray | None = None
        self.current_seg_data: SegmentationData | None = None
        self.settings: Settings | None = None
        self.mode: Mode = Mode(app_state.image_panel_state.mode)

        # layout
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        
        # image view
        self.image_view = ImageView(self, app_state)
        vlayout.addWidget(self.image_view)

        # sync other states
        self.update_image()
    
    def add_images(self, image_paths: list[Path]):
        """Add new image files."""
        filtered_paths = list(set([p for p in image_paths if self._validate_file(p)])) # set to remove duplicates
        if len(filtered_paths) > 0:
            for p in filtered_paths:
                self.image_files.remove(p) # remove duplicates
            self.image_files += filtered_paths
            self._set_current_file(filtered_paths[-1], is_image=True)
            # request imgproc settings
            self.settings_panel.emit_fields()
    
    def _set_current_file(self, 
                          file_path: Path, 
                          is_image: bool
        ) -> bool:
        """
        Attempts to set the currently viewed file and emits a signal.
        Returns
            kept (bool): Whether the file was kept.
        """
        valid = self._validate_file(file_path)
        if not valid:
            if file_path in self.image_files:
                self.image_files.remove(file_path)
            if file_path in self.seg_files:
                self.seg_files.remove(file_path)
            return False
        
        # update lists
        if is_image:
            if file_path not in self.image_files:
                self.image_files.append(file_path)
            self.mode = Mode.TUNE
        else:
            if file_path not in self.seg_files:
                self.seg_files.append(file_path)
            self.mode = Mode.REVIEW
        
        # update state
        self.current_file = file_path
        self.update_image()
        return True

    def _validate_file(self, file_path: Path) -> bool:
        """
        Check if the given image or .SEG file is valid.
        Returns:
            valid (bool): The file's validity.
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.seg'}
        valid = file_path.is_file() and file_path.suffix.lower() in image_extensions
        if valid and file_path.suffix.lower() == ".seg":
            # Try reading the .SEG file
            seg_data = self._get_segmentation_data(file_path)
            valid &= seg_data != None
        # notify user if not valid
        if not valid:
            QMessageBox(
                QMessageBox.Icon.Warning,
                "Invalid or Missing File", 
                f"File {file_path.absolute()} is either corrupt, does not exist, or is not one of the following file types: '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.seg'.",
                QMessageBox.StandardButton.Ok,
                self
            ).exec()
        return valid

    def receive_settings(self, settings: Settings):
        """Receive new settings and update image."""
        self.settings = settings
        self.update_image()
    
    def _get_segmentation_data(self, file_path: Path) -> SegmentationData | None:
        """
        Attempts to extract segmentation data from the given .SEG file.
        Returns:
            segmentation_data (SegmentationData | None): data, if the file is valid, otherwise `None`.
        """ 
        try:
            with open(file_path, "rb") as f:
                file_data = pickle.load(f)
            data = [item[1] for item in file_data.items()]
            # expected data
            img_filename: str = data[0]
            image: npt.NDArray = data[1]
            resolution_divisor: float = data[2]
            contour_data_raw: list[tuple[
                int, # ID
                npt.NDArray, # inner_contour
                npt.NDArray, # outer_contour
                float, # g_ratio
                float, # circularity
                float, # thickness
                float, # inner_diameter
                float # outer_diameter
            ]] = data[3]
            selected_states: list[bool] = data[4]
            # process contour_data_raw
            contour_data: list[ContourData] = []
            for ID, inner_contour, outer_contour, g_ratio, circularity, thickness, inner_diameter, outer_diameter in contour_data_raw:
                contour_data.append(ContourData(
                    ID=ID,
                    inner_contour=inner_contour,
                    outer_contour=outer_contour,
                    g_ratio=g_ratio,
                    circularity=circularity,
                    thickness=thickness,
                    inner_diameter=inner_diameter,
                    outer_diameter=outer_diameter
                ))
            return SegmentationData(
                img_filename=img_filename,
                image=image,
                resolution_divisor=resolution_divisor,
                contour_data=contour_data,
                selected_states=selected_states
            )
        except Exception as e:
            return None
    
    def update_image(self):
        """Updates this panel's `ImageView` using the current file."""
        if self.current_file is None:
            return
        
        # retrieve image
        if self.mode == Mode.TUNE:
            self.current_original_image = cv2.imread(str(self.current_file))
            self._process_current_image()
        elif self.mode == Mode.REVIEW:
            self.current_seg_data = self._get_segmentation_data(self.current_file)
            if self.current_seg_data is not None:
                self.current_original_image = self.current_seg_data.image
            self.display_image = self.current_original_image

        # set image
        if self.display_image is None:
            return
        self.image_view.set_image(self.display_image)
    
    def _process_current_image(self):
        """Process the current image according to segmentation settings."""
        if self.current_original_image is not None:
            # check settings exists
            if self.settings is None:
                self.display_image = self.current_original_image
                return
            
            # check show original
            settings = self.settings
            if settings.show_original:
                self.display_image = self.current_original_image
                return 
            
            # process image
            resized_image = cv2.resize(
                self.current_original_image, 
                None, 
                fx=1/settings.resolution_divisor, 
                fy=1/settings.resolution_divisor
            )
            resized_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
            nm_per_pixel = settings.scale if settings.scale_units == "nm" else settings.scale/1000
            processed_image, data = process_image(
                resized_image,
                settings.resolution_divisor,
                settings.show_threshold,
                nm_per_pixel,
                settings.threshold,
                settings.radius,
                settings.dilate,
                settings.erode,
                settings.min_size,
                settings.max_size,
                settings.convexity,
                settings.circularity
            )
            self.display_image = processed_image
    
    def set_image_view(self, image_panel_state: ImagePanelState):
        """Set the center position and zoom of the `ImageView` to the given values."""
        self.image_view.set_center_zoom(
            image_panel_state.view_center_point, 
            image_panel_state.view_image_width
        )
    
    def to_state(self) -> ImagePanelState:
        """Return all current fields as an `ImagePanelState` object."""
        return ImagePanelState(
            image_files=[str(p) for p in self.image_files],
            seg_files=[str(p) for p in self.seg_files],
            current_file=str(self.current_file) if self.current_file is not None else "",
            mode=self.mode.value,
            view_center_point=self.image_view.get_center_point(),
            view_image_width=self.image_view.get_image_width()
        )
    
