from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    QMutex,
    QTimer,
    QWaitCondition
)

from imgproc.process_image import process_image

from models import Settings

from pathlib import Path
import numpy as np
import traceback
import cv2


class ImgProcWorker(QObject):
    finished = Signal(object, object, object) # image, segmentation data, settings
    error = Signal(str)
    processingChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._wait = QWaitCondition()

        self._image = None
        self._settings = None
        self._has_job = False
        self._stop_requested = False
        self.font_path = Path("assets/JetBrainsMono-Bold.ttf")

    @Slot()
    def start(self):
        """Main worker loop — runs in worker thread."""
        while True:
            self._mutex.lock()
            while not self._has_job and not self._stop_requested:
                self._wait.wait(self._mutex, 10)

            if self._stop_requested:
                self._mutex.unlock()
                break

            image = self._image
            settings = self._settings
            self._has_job = False
            self._mutex.unlock()
            
            # Tell ImagePanel processing has started
            self.processingChanged.emit(True)

            try:
                if image is not None and settings is not None:
                    self._process(image, settings)
            finally:
                # finish processing message
                self.processingChanged.emit(False)

    def enqueue(self, image, settings):
        self._mutex.lock()
        self._image = image.copy()
        self._settings = settings
        self._has_job = True
        self._wait.wakeOne()
        self._mutex.unlock()

    @Slot()
    def stop(self):
        self._mutex.lock()
        self._stop_requested = True
        self._wait.wakeOne()
        self._mutex.unlock()
    
    def _process(self, image: np.ndarray, settings: Settings):
        try:
            if settings.show_original:
                result = image
                contour_data_list = None # None means don't analyze data
            else:
                resized = cv2.resize(
                    image,
                    None,
                    fx=1 / settings.resolution_divisor,
                    fy=1 / settings.resolution_divisor
                )
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

                nm_per_pixel = (
                    settings.scale
                    if settings.scale_units == "nm"
                    else settings.scale * 1000
                )

                result, contour_data_list = process_image(
                    resized,
                    settings.resolution_divisor,
                    settings.show_threshold,
                    settings.show_text,
                    nm_per_pixel,
                    settings.threshold,
                    settings.radius,
                    settings.dilate,
                    settings.erode,
                    settings.min_size,
                    settings.max_size,
                    settings.convexity,
                    settings.circularity,
                    settings.thickness_percentile,
                    lambda: self._stop_requested,
                    self.font_path,
                    timed=True
                )

            self.finished.emit(result, contour_data_list, settings)

        except Exception as e:
            self.error.emit(traceback.format_exc())
            traceback.print_exc()
            
