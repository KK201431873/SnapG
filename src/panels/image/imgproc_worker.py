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

import numpy as np
import cv2


class ImgProcWorker(QObject):
    finished = Signal(object, object) # image, segmentation data
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._wait = QWaitCondition()

        self._image = None
        self._settings = None
        self._has_job = False
        self._stop_requested = False

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

            if image is not None and settings is not None:
                self._process(image, settings)

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
                seg_data = None
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
                    else settings.scale / 1000
                )

                result, seg_data = process_image(
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
                    stop_flag=lambda: self._stop_requested
                )

            self.finished.emit(result, seg_data)

        except Exception as e:
            self.error.emit(str(e))
