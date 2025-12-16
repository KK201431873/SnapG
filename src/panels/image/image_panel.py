from PySide6.QtCore import (
    QSize,
    Signal,
    QThread,
    Qt,
    QTimer,
    Slot
)
from PySide6.QtGui import (
    QImage
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QMessageBox,
    QApplication
)

from panels.settings.settings_panel import SettingsPanel
from panels.image.image_view import ImageView
from panels.image.imgproc_worker import ImgProcWorker

from models import AppState, SegmentationData, ContourData, ImagePanelState, Settings, FileMan, logger

from pathlib import Path
from enum import Enum
import numpy.typing as npt
import numpy as np
import traceback
import pickle
import cv2

class Mode(Enum):
    NO_IMAGE = 0
    TUNE = 1
    REVIEW = 2

class ImagePanel(QWidget):
    """Central image viewer and contour selector."""
    
    enqueue_process = Signal(object, object) # original image, settings
    """Emits a command for imgproc worker thread to begin processing."""

    files_changed = Signal(list, list, Path)
    """Emits the current list of images, segmentation files, and the current selected file."""

    stop_worker_signal = Signal()
    """Signal to stop the worker thread."""

    def __init__(self, app_state: AppState, settings_panel: SettingsPanel):
        super().__init__()
        self.settings_panel = settings_panel
        
        # init files lists and state
        self.image_files: list[Path] = [Path(p) for p in app_state.image_panel_state.image_files]
        self.seg_files: list[Path] = [Path(p) for p in app_state.image_panel_state.seg_files]
        current_file_str = app_state.image_panel_state.current_file
        self.current_file: Path | None = Path(current_file_str) if current_file_str != "" else None
        self.last_current_file: Path | None = None # this is for update_image() to cache images after imread
        # image state
        self.current_original_image: npt.NDArray | None = None
        self.display_image: npt.NDArray | None = None
        self.current_seg_data: SegmentationData | None = None
        # logic/config
        self.settings: Settings | None = None
        self.mode: Mode = Mode(app_state.image_panel_state.mode)

        # layout
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        
        # image view
        self.image_view = ImageView(self, app_state)
        vlayout.addWidget(self.image_view)
        
        # image processing thread
        self.processing_thread = QThread(self)
        self.worker = ImgProcWorker()
        self.worker.moveToThread(self.processing_thread)
        # processing status indicator
        self.worker.processingChanged.connect(self._on_processing_changed)
        self.processing = False
        # start and receive signals
        self.enqueue_process.connect(self.worker.enqueue)
        self.worker.finished.connect(self._on_processing_finished)
        self.worker.error.connect(self._on_processing_error)
        self.processing_thread.started.connect(self.worker.start)
        self.processing_thread.start()

        # validate initial state
        if self.current_file is not None: # current file
            valid = self._validate_file(self.current_file, remove=True)
            if not valid:
                self.current_file = None
        for p in self.image_files + self.seg_files: # all opened files
            self._validate_file(p, remove=True)

        # sync other states
        self.update_image()
    
    def emit_files(self):
        """Emits this `ImagePanel`'s `files_changed` signal."""
        self.files_changed.emit(
            self.image_files,
            self.seg_files,
            self.current_file
        )
    
    def get_current_file(self) -> Path | None:
        """Returns the `Path` of the currently displayed file."""
        if self.current_file is not None:
            return Path(self.current_file)
        return None

    def get_display_image(self) -> npt.NDArray | None:
        """Returns the currently displayed image."""
        if self.display_image is not None:
            return np.copy(self.display_image)
        else:
            return None
    
    def add_images(self, image_paths: list[Path]):
        """Add new image files."""
        filtered_paths = list(set([p for p in image_paths if self._validate_file(p, remove=False)])) # cvt to set to remove duplicates
        if len(filtered_paths) > 0:
            for p in filtered_paths:
                if p in self.image_files:
                    self.image_files.remove(p) # remove existing duplicates
            self.image_files += filtered_paths
            self._set_current_file(filtered_paths[-1], is_image=True)
            # request imgproc settings
            self.settings_panel.emit_fields()
    
    def remove_files(self, file_paths: list[Path]):
        """Remove the given files."""
        if not file_paths:
            return

        # store current file data
        old_current = self.current_file
        was_image = old_current in self.image_files if old_current else False

        if old_current:
            if was_image:
                old_index = self.image_files.index(old_current)
            elif old_current in self.seg_files:
                old_index = self.seg_files.index(old_current)
            else:
                old_index = -1
        else:
            old_index = -1

        # remove the given files
        for path in file_paths:
            if path in self.image_files:
                self.image_files.remove(path)
            if path in self.seg_files:
                self.seg_files.remove(path)

        # check if didn't remove current file
        if old_current and old_current not in file_paths:
            self.emit_files()
            return
        
        # handle current file behavior
        file_list = self.image_files if was_image else self.seg_files
        if file_list:
            new_index = min(old_index, len(file_list) - 1)
            self._set_current_file(file_list[new_index], is_image=was_image)
        else:
            self.current_file = None
            self.display_image = None
            self.image_view.clear_image()
            self.emit_files()
    
    def _log_file_name(self):
        """Print the current file name to output."""
        if self.current_file is None:
            logger.clear()
            logger.println("No File Selected")
        else:
            logger.clear()
            logger.print("File: ", bold=True)
            logger.println(self.current_file.name)
    
    def _set_current_file(self, 
                          file_path: Path, 
                          is_image: bool
        ) -> bool:
        """
        Attempts to set the currently viewed file and emits a signal.
        Returns
            kept (bool): Whether the file was kept.
        """
        if file_path == self.current_file:
            self._log_file_name()
            return True

        valid = self._validate_file(file_path, remove=True)
        if not valid:
            self._log_file_name()
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
        
        # emit signal
        self.emit_files()
        self._log_file_name()
        return True

    def _validate_file(self, file_path: Path, remove: bool = False) -> bool:
        """
        Check if the given image or .SEG file is valid.
        Returns:
            valid (bool): The file's validity.
        """
        extension = file_path.suffix.lower()
        valid = file_path.is_file() and FileMan.is_image(extension)
        if valid and extension == ".seg":
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
            if remove:
                if file_path in self.image_files:
                    self.image_files.remove(file_path)
                    self.emit_files()
                if file_path in self.seg_files:
                    self.seg_files.remove(file_path)
                    self.emit_files()
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
            self._log_file_name()
            logger.println("Failed to read Segmentation File:", bold=True, color="red")
            logger.println(traceback.format_exc(), color="red")
            return None
    
    def update_image(self):
        """Updates this panel's `ImageView` using the current file."""
        if self.current_file is None:
            return

        # tune: read image file
        if self.mode == Mode.TUNE:
            if self.last_current_file is None or self.current_file != self.last_current_file:
                try:
                    self.current_original_image = cv2.imread(str(self.current_file))
                except Exception as e:
                    self._log_file_name()
                    logger.println("Failed to read Image File:", bold=True, color="red")
                    logger.println(traceback.format_exc(), color="red")
            self._process_current_image()
        
        # review: get image from seg file
        elif self.mode == Mode.REVIEW:
            self.current_seg_data = self._get_segmentation_data(self.current_file)
            if self.current_seg_data is not None:
                self.current_original_image = self.current_seg_data.image
            self.display_image = self.current_original_image

        # keep track of if file changed
        self.last_current_file = self.current_file

        # set image
        if self.display_image is None:
            return
        self.image_view.set_image(self.display_image)
    
    def _process_current_image(self):
        """Process the current image according to segmentation settings."""
        if self.current_original_image is None or self.settings is None:
            self.display_image = self.current_original_image
            return

        # enqueue image processing on worker thread
        self.worker.enqueue(
            self.current_original_image,
            self.settings
        )
    
    @Slot(bool)
    def _on_processing_changed(self, active: bool):
        """Update processing status indicator."""
        self.processing = active
        self.image_view.set_processing(active)

    def _on_processing_finished(self, image: np.ndarray, seg_data):
        """Receive worker thread results and set display image."""
        self.display_image = image
        self.current_seg_data = seg_data
        self.image_view.set_image(self.display_image)

        # log data
        self._log_file_name()
        logger.println(f"{len(seg_data)} axons found.\n")
        if len(seg_data) == 0:
            return

        mean_g_ratio = round(np.mean([d[1] for d in seg_data]), 3)
        logger.print("Mean G-ratio", underline=True)
        logger.print(": ")
        logger.println(f"{mean_g_ratio}\n", color="gray")

        units = "µm" if self.settings is None else self.settings.scale_units
        mean_inner_dia = np.mean([d[3] for d in seg_data])
        mean_outer_dia = np.mean([d[4] for d in seg_data])
        logger.println("Mean diameters", underline=True)
        if units == "µm":
            mean_inner_dia /= 1000.0
            mean_outer_dia /= 1000.0
        logger.print(f"|   Inner: ")
        logger.println(f"{round(mean_inner_dia, 3)} {units}", color="gray")
        logger.print(f"|   Outer: ")
        logger.println(f"{round(mean_outer_dia, 3)} {units}\n", color="gray")

        logger.println("Detections", underline=True)
        for (
            ID,
            gratio,
            circularity,
            inner_diameter,
            outer_diameter,
            myelin_thickness
        ) in seg_data:
            if units == "µm":
                inner_diameter /= 1000.0
                outer_diameter /= 1000.0
                myelin_thickness /= 1000.0

            logger.println(f"|   Axon {ID}")
            logger.print("|       g-ratio: "); logger.println(f"{round(gratio, 3)}", color="gray")
            logger.print("|       circularity: "); logger.println(f"{round(circularity, 3)}", color="gray")
            logger.print("|       inner diameter: "); logger.println(f"{round(inner_diameter, 3)} {units}", color="gray")
            logger.print("|       outer diameter: "); logger.println(f"{round(outer_diameter, 3)} {units}", color="gray")
            logger.print("|       myelin thickness: "); logger.println(f"{round(myelin_thickness, 3)} {units}", color="gray")
            logger.println("|")

    def _on_processing_error(self, message: str):
        """Handle worker thread errors."""
        self._log_file_name()
        logger.println(f"ERROR While Processing!", bold=True, color="red")
        logger.println(message, color="red")
        QMessageBox.critical(self, "Processing Error", message)
    
    def set_image_view(self, image_panel_state: ImagePanelState):
        """Set the center position and zoom of the `ImageView` to the given values."""
        self.image_view.set_center_zoom(
            image_panel_state.view_center_point, 
            image_panel_state.view_image_width
        )
    
    def get_image_files(self) -> list[Path]:
        """Returns this `ImagePanel`'s image files."""
        return [Path(p) for p in self.image_files]

    def get_seg_files(self) -> list[Path]:
        """Returns this `ImagePanel`'s segmentation files."""
        return [Path(p) for p in self.seg_files]
    
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
    
    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        self.processing_thread.quit()
        QTimer.singleShot(1000, self.processing_thread.wait)
        event.accept()
    