from PySide6.QtCore import (
    QSize,
    Signal,
    QThread,
    Qt,
    QTimer,
    Slot,
    QPoint
)
from PySide6.QtGui import (
    QImage,
    QCloseEvent,
    QKeyEvent
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

from PIL import Image, ImageFont, ImageDraw
from pathlib import Path
from enum import Enum
import numpy.typing as npt
import numpy as np
import traceback
import pickle
import math
import cv2
import os

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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self.image_view.mouse_pressed.connect(self._handle_mouse_pressed)
        vlayout.addWidget(self.image_view)
        # these states are for REVIEW mode
        self.exclude_deselected_contours: bool = False
        self.exclude_all_contours: bool = False
        
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
    
    def add_files(self, file_paths: list[Path]):
        """Add new image or segmentation files"""
        validated_paths = [p for p in file_paths if self._validate_file(p, remove=False)]
        if len(validated_paths) == 0:
            return

        # remove duplicates within the given files
        filtered_paths: list[Path] = [] 
        for p in validated_paths:
            if p not in filtered_paths:
                filtered_paths.append(p)
        if len(filtered_paths) == 0:
            return # something mustve gone really wrong
        
        # remove files that are already opened
        last_duplicate: Path | None = None
        for p in self.image_files + self.seg_files:
            if p in filtered_paths:
                last_duplicate = p
                filtered_paths.remove(p) 
        
        # open the last new file, if empty then open the last duplicate file
        if len(filtered_paths) > 0:
            for p in filtered_paths:
                if FileMan.path_is_image(p):
                    self.image_files.append(p)
                else:
                    self.seg_files.append(p)
            self._set_current_file(filtered_paths[-1], is_image=FileMan.path_is_image(filtered_paths[-1]))
        elif last_duplicate is not None:
            self._set_current_file(last_duplicate, is_image=FileMan.path_is_image(last_duplicate))
        
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
        if file_list and old_index >= 0:
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
            self.emit_files()
            return True

        valid = self._validate_file(file_path, remove=True)
        if not valid:
            self.emit_files()
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
        self._log_file_name()
        self.update_image()
        
        # emit signal
        self.emit_files()
        return True

    def _validate_file(self, file_path: Path, remove: bool = False) -> bool:
        """
        Check if the given image or .SEG file is valid.
        Returns:
            valid (bool): The file's validity.
        """
        extension = file_path.suffix.lower()
        valid = file_path.is_file() and (FileMan.is_image(extension) or extension == ".seg")
        if valid and extension == ".seg":
            # Try reading the .SEG file
            seg_data = SegmentationData.from_file(file_path, self)
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
        self.update_image(read_seg_file=False) # changing settings should only affect TUNE mode, not REVIEW
    
    def update_image(self, read_seg_file: bool = True):
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
                    logger.err(f"update_image(): Failed to read image file: {traceback.format_exc()}", self)
            self._process_current_image()
        
        # review: get image from seg file
        elif self.mode == Mode.REVIEW:
            if read_seg_file:
                self.current_seg_data = SegmentationData.from_file(self.current_file, self)
            if self.current_seg_data is not None:
                self.current_original_image = self.current_seg_data.image
                self.display_image = self._annotate_review_image(self.current_seg_data)
                self._log_file_name()
                self._log_contour_data(
                    self.current_seg_data.contour_data, 
                    units=self.current_seg_data.preferred_units,
                    selected_states=self.current_seg_data.selected_states
                )
            else:
                self.display_image = self.current_original_image

        # keep track of if file changed
        self.last_current_file = self.current_file

        # set image
        if self.display_image is None or self.current_original_image is None:
            logger.err("update_image(): display_image or current_original_image is None, not setting image.", self)
            return
        if self.mode == Mode.REVIEW:
            if self.current_seg_data is None:
                logger.err("update_image(): current_seg_data is None in REVIEW mode, not setting image.", self)
                return
            resolution_divisor = self.current_seg_data.resolution_divisor
        else:
            resolution_divisor = 1
        self.image_view.set_image(
            self.display_image,
            (int(self.current_original_image.shape[1] * resolution_divisor), 
             int(self.current_original_image.shape[0] * resolution_divisor))
        )
    
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

    def _on_processing_finished(self, image: np.ndarray, contour_data_list: list[ContourData] | None, settings: Settings):
        """Receive worker thread results and set display image."""
        if self.mode != Mode.TUNE:
            return
        
        if self.current_original_image is None:
            logger.err("_on_processing_finished(): current_original_image is None. Not displaying image...", self)
            return
        
        self.display_image = image
        self.image_view.set_image(
            self.display_image, 
            (self.current_original_image.shape[1], self.current_original_image.shape[0])
        )

        # log data
        self._log_file_name()
        if contour_data_list is not None:
            self._log_contour_data(
                contour_data_list, 
                settings.scale_units
            )
        
    def _log_contour_data(self, contour_data_list: list[ContourData], units: str, selected_states: list[bool] | None = None):
        """Helper function for logging contour data to the text display."""
        # sort axons
        if selected_states is None:
            selected_cnt: list[ContourData] = contour_data_list
            deselected_cnt: list[ContourData] = []
        else:
            selected_cnt: list[ContourData] = []
            deselected_cnt: list[ContourData] = []
            for i, c in enumerate(contour_data_list):
                if selected_states[i]:
                    selected_cnt.append(c)
                else:
                    deselected_cnt.append(c)

        # log data
        logger.print(f"{len(selected_cnt)} axons {"found" if selected_states is None else "selected"}.")
        if len(deselected_cnt) > 0:
            logger.print(f" ({len(deselected_cnt)} deselected)")
        logger.print("\n\n")
        if len(contour_data_list) == 0:
            return
        
        data_suffix = "" if selected_states is None else "(selected axons)"

        logger.print("Mean G-ratio", underline=True)
        logger.println(":")
        if selected_states is not None and len(selected_cnt) > 0 and len(deselected_cnt) > 0:
            # log selected
            mean_g_ratio = round(np.mean([c.g_ratio for c in selected_cnt]), 3)
            logger.print("|   "); logger.println(f"{mean_g_ratio} {data_suffix}", color="gray")
        # log total
        mean_g_ratio = round(np.mean([c.g_ratio for c in contour_data_list]), 3)
        logger.print("|   "); logger.println(f"{mean_g_ratio} (all axons)\n", color="gray")

        logger.println("Mean diameters", underline=True)
        if selected_states is not None and len(selected_cnt) > 0 and len(deselected_cnt) > 0:
            # log selected
            mean_inner_dia = np.mean([c.inner_diameter for c in selected_cnt])
            mean_outer_dia = np.mean([c.outer_diameter for c in selected_cnt])
            if units == "um":
                mean_inner_dia /= 1000.0
                mean_outer_dia /= 1000.0
            logger.print(f"|   Inner: ")
            logger.println(f"{round(mean_inner_dia, 3)} {units} {data_suffix}", color="gray")
            logger.print(f"|   Outer: ")
            logger.println(f"{round(mean_outer_dia, 3)} {units} {data_suffix}", color="gray")
        # log total
        mean_inner_dia = np.mean([c.inner_diameter for c in contour_data_list])
        mean_outer_dia = np.mean([c.outer_diameter for c in contour_data_list])
        if units == "um":
            mean_inner_dia /= 1000.0
            mean_outer_dia /= 1000.0
        logger.print(f"|   Inner: ")
        logger.println(f"{round(mean_inner_dia, 3)} {units} (all axons)", color="gray")
        logger.print(f"|   Outer: ")
        logger.println(f"{round(mean_outer_dia, 3)} {units} (all axons)\n", color="gray")

        if len(selected_cnt) == 0:
            return

        logger.println(f"Detections {data_suffix}", underline=True)
        for c in selected_cnt:
            inner = c.inner_diameter
            outer = c.outer_diameter
            thick = c.thickness

            if units == "um":
                inner /= 1000.0
                outer /= 1000.0
                thick /= 1000.0

            logger.println(f"|   Axon {c.ID}")
            logger.print("|       g-ratio: "); logger.println(f"{round(c.g_ratio, 3)}", color="gray")
            logger.print("|       circularity: "); logger.println(f"{round(c.circularity, 3)}", color="gray")
            logger.print("|       inner diameter: "); logger.println(f"{round(inner, 3)} {units}", color="gray")
            logger.print("|       outer diameter: "); logger.println(f"{round(outer, 3)} {units}", color="gray")
            logger.print("|       myelin thickness: "); logger.println(f"{round(thick, 3)} {units}", color="gray")
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

    def _handle_mouse_pressed(self, is_in_image: bool, image_point: QPoint):
        """Review mode logic."""
        # Sanity checks
        if self.mode != Mode.REVIEW:
            return
        if not is_in_image:
            return
        if self.current_file is None or self.current_seg_data is None:
            return
        
        # check for clicks on contours
        contour_data = self.current_seg_data.contour_data
        res_div = self.current_seg_data.resolution_divisor
        closest_valid_contour: tuple[int | None, float] = (None, -1)
        for i, contour in enumerate(contour_data):
            M = cv2.moments(contour.inner_contour)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"] * res_div)
            cy = int(M["m01"] / M["m00"] * res_div)
            diameter = cv2.arcLength(contour.inner_contour, closed=True)/(2*math.pi) * res_div
            distance = math.hypot(
                cx - image_point.x(),
                cy - image_point.y()
            )
            if (distance <= diameter) and (closest_valid_contour[0] is None or distance < closest_valid_contour[1]):
                closest_valid_contour = (i, distance)

        # toggle if contour clicked
        if closest_valid_contour[0] is not None:
            index = closest_valid_contour[0]
            self.current_seg_data.selected_states[index] = not self.current_seg_data.selected_states[index]
            self._save_segmentation_atomic(self.current_file, self.current_seg_data)
            self.update_image()
        
    def _save_segmentation_atomic(self, file: Path, seg_data: SegmentationData):
        """Save the given `SegmentationData` at the given `Path` atomically (safely)."""
        tmp_path = file.with_suffix(".seg.tmp")
        with open(tmp_path, "wb") as f:
            pickle.dump(seg_data, f)
            f.flush()
            os.fsync(f.fileno())
        tmp_path.replace(file)

    def _annotate_review_image(self, seg_data: SegmentationData) -> npt.NDArray:
        """Draw colored contours on segmentation image."""
        display_img = seg_data.image.copy()
        if len(display_img.shape) == 2: # grayscale, cvt to color
            display_img = cv2.cvtColor(display_img, cv2.COLOR_GRAY2BGR)
        res_div = seg_data.resolution_divisor
        contour_data = seg_data.contour_data
        selected_states = seg_data.selected_states

        if len(contour_data) != len(selected_states):
            logger.err("_annotate_review_image(): Length of contour data is not equal to length of selected states", self)

        # scale image down for processing speed
        im_h = display_img.shape[0]
        im_w = display_img.shape[1]
        scale_factor = 1.0
        if max(im_h, im_w) > 512:
            scale_factor = 512 / max(im_h, im_w)
            display_img = cv2.resize(display_img, None, fx=scale_factor, fy=scale_factor) 

        def scale_contour(cnt: npt.NDArray, s):
            return (cnt * s).astype(np.int32)

        # draw contours
        for i, c in enumerate(contour_data):
            if (self.exclude_deselected_contours and not selected_states[i]) or self.exclude_all_contours:
                continue  # Hide excluded in preview
            inner = scale_contour(c.inner_contour, scale_factor)
            outer = scale_contour(c.outer_contour, scale_factor)
            M = cv2.moments(inner)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            color = (0, 255, 0) if selected_states[i] else (0, 0, 255)
            cv2.drawContours(display_img, [inner], -1, color, 2)
            cv2.drawContours(display_img, [outer], -1, color, 2)
            cv2.circle(display_img, (cx, cy), 4, (0, 0, 0), -1)

        # draw text
        img_h = display_img.shape[0]
        img_w = display_img.shape[1]
        draw_scale = int(8 * max(img_h, img_w) / 4096)
        line_spacing = 14*draw_scale
        out_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype(AppState.annotation_font_path(), int(15*draw_scale))
        draw = ImageDraw.Draw(out_pil)
        for i, c in enumerate(contour_data):
            if (self.exclude_deselected_contours and not selected_states[i]) or self.exclude_all_contours:
                continue
            inner = scale_contour(c.inner_contour, scale_factor)
            M = cv2.moments(inner)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"] - 6*draw_scale)

            ID = i + 1
            color = (255, 255, 255) if selected_states[i] else (192, 192, 192)
            def draw_shadow_text(dx,dy):
                draw.text((int(cx-5*draw_scale*len(f"#{ID}"))+dx, cy-1/2*line_spacing+dy), f"#{ID}", font=font, fill=color)
            for dx,dy in [(-2,-2),(2,-2),(2,2),(-2,2)]:
                draw_shadow_text(dx,dy)
            color = (0, 0, 255) if selected_states[i] else (64, 64, 64)
            draw.text((int(cx-5*draw_scale*len(f"#{ID}")), cy-1/2*line_spacing), f"#{ID}", font=font, fill=color)
            
        display_img = cv2.cvtColor(np.array(out_pil), cv2.COLOR_RGB2BGR)
        return display_img
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle enabling contour exclusion modes in REVIEW mode."""
        if event.isAutoRepeat():
            return
        
        if self.mode != Mode.REVIEW:
            super().keyPressEvent(event)
            return

        changed = False
        if event.key() == Qt.Key.Key_Shift:
            if not self.exclude_deselected_contours:
                self.exclude_deselected_contours = True
                changed = True

        elif event.key() == Qt.Key.Key_Space:
            if not self.exclude_all_contours:
                self.exclude_all_contours = True
                changed = True

        if changed:
            self.update_image(read_seg_file=False)
        event.accept()
    
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle disabling contour exclusion modes in REVIEW mode."""
        if event.isAutoRepeat():
            return
        
        changed = False
        if event.key() == Qt.Key.Key_Shift:
            if self.exclude_deselected_contours:
                self.exclude_deselected_contours = False
                changed = True

        elif event.key() == Qt.Key.Key_Space:
            if self.exclude_all_contours:
                self.exclude_all_contours = False
                changed = True

        if changed and self.mode == Mode.REVIEW:
            self.update_image(read_seg_file=False)
        event.accept()
    
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
    
    def closeEvent(self, event: QCloseEvent) -> None:
        # save segmentation data
        if self.mode == Mode.REVIEW and self.current_file is not None and self.current_seg_data is not None:
            try:
                self._save_segmentation_atomic(self.current_file, self.current_seg_data)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Segmentation file not found:\n{e}"
                )
                event.ignore()
                return
        # stop worker
        if self.worker:
            self.worker.stop()
        self.processing_thread.quit()
        QTimer.singleShot(1000, self.processing_thread.wait)
        event.accept()
    