from PySide6.QtCore import QObject, Signal, Slot

from imgproc.process_image import process_image

from models import Settings, SegmentationData

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from cv2 import imread, cvtColor, COLOR_BGR2GRAY, resize
from threading import Event
import numpy.typing as npt
import multiprocessing
import traceback
import pickle

def process_single_image(
    args: tuple[Path, npt.NDArray, Settings, Event]
) -> SegmentationData:
    """Runs image processing algorithm. Only uses local state and does not access mutable global data."""

    # extract args
    path: Path = args[0]
    image: npt.NDArray = args[1]
    settings: Settings = args[2]
    stop_event = args[3]

    # get scale
    nm_per_pixel = (
        settings.scale
        if settings.scale_units == "nm"
        else settings.scale * 1000
    )

    # process
    img_gray = cvtColor(image, COLOR_BGR2GRAY)
    _, contour_data_list = process_image( # don't use out_img
        img_gray,
        settings.resolution_divisor,
        False, # don't show threshold
        False, # don't show text,
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
        stop_event=stop_event,
        font_path=None, # no font means don't draw anything
        timed=False
    )
    if contour_data_list is None:
        contour_data_list = []
    
    if stop_event.is_set(): # STOPCHECK!!
        return SegmentationData(
            img_filename=path.name,
            image=image,
            resolution_divisor=settings.resolution_divisor,
            contour_data=[],
            selected_states=[],
            preferred_units=settings.scale_units
        )

    # convert result to SegmentationData
    return SegmentationData(
        img_filename=path.name,
        image=image,
        resolution_divisor=settings.resolution_divisor,
        contour_data=contour_data_list,
        selected_states=[True for _ in contour_data_list],
        preferred_units=settings.scale_units
    )

class BatchWorker(QObject):
    start = Signal(list, Settings, int, Path)
    progress = Signal(Path)
    finished = Signal()
    error = Signal(str)

    pool: ProcessPoolExecutor | None = None

    def __init__(self):
        super().__init__()
        self._stop_requested: bool = False
        self._manager = multiprocessing.Manager()
        self._stop_event = self._manager.Event()
        self.start.connect(self.run)

    @Slot(list, Settings, int, Path)
    def run(self, 
            image_paths: list[Path], 
            settings: Settings, 
            workers: int,
            save_dir: Path
        ):
        """Begin processing given images using multiprocessing."""
        self._stop_requested = False
        
        self._manager = multiprocessing.Manager()
        self._stop_event = self._manager.Event()

        # load images
        images: list[tuple[Path, npt.NDArray]] = []
        for p in image_paths:
            img_np = imread(str(p))
            if img_np is not None:
                img_shrunk = resize(
                    img_np,
                    None,
                    fx=1 / settings.resolution_divisor,
                    fy=1 / settings.resolution_divisor
                )
                images.append((p, img_shrunk))

        # begin processing
        formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            with ProcessPoolExecutor(
                max_workers=workers,
                mp_context=multiprocessing.get_context("spawn")
            ) as pool:
                self.pool = pool

                futures = {
                    pool.submit(
                        process_single_image, 
                        (path, image, settings, self._stop_event)
                    ): path
                    for path, image in images
                }

                for future in as_completed(futures):
                    if self._stop_requested:
                        pool.shutdown(wait=True, cancel_futures=True)
                        break

                    path = futures[future]
                    try:
                        segmentation_data: SegmentationData = future.result()

                        # save seg file
                        img_name = path.stem
                        imgproc_out_path = save_dir / f"{img_name}_{formatted_datetime}.seg"
                        with open(imgproc_out_path, "wb") as f:
                            pickle.dump(segmentation_data, f)
                        
                        self.progress.emit(path)
                    except Exception:
                        self.error.emit(traceback.format_exc())

        except Exception:
            self.error.emit(traceback.format_exc())

        self.finished.emit()

    @Slot()
    def stop(self):
        self._stop_requested = True
        if self._stop_event is not None:
            self._stop_event.set()
        if self.pool is not None:
            self.pool.shutdown(wait=False, cancel_futures=True)
