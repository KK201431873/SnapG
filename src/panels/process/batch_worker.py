from PySide6.QtCore import QObject, Signal, Slot

from imgproc.process_image import process_image

from models import Settings

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import multiprocessing
import traceback

def process_single_image(args):
    """Runs image processing algorithm only."""
    path, settings = args
    return path, process_image(path, settings)

class BatchWorker(QObject):
    progress = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self._stop_requested: bool = False
        self.font_path: Path = Path("assets/JetBrainsMono-Bold.ttf")

    @Slot(list, object, int)
    def run_multi_process(self, 
            image_paths: list[Path], 
            settings: Settings, 
            workers: int
        ):
        self._stop_requested = False

        try:
            with ProcessPoolExecutor(
                max_workers=workers,
                mp_context=multiprocessing.get_context("spawn")
            ) as pool:

                futures = {
                    pool.submit(process_single_image, (p, settings)): p
                    for p in image_paths
                }

                for future in as_completed(futures):
                    if self._stop_requested:
                        break

                    path = futures[future]
                    try:
                        _, result = future.result()
                        self.progress.emit(f"Processed {path.name}")
                    except Exception:
                        self.error.emit(traceback.format_exc())

        except Exception:
            self.error.emit(traceback.format_exc())

        self.finished.emit()

    @Slot()
    def stop(self):
        self._stop_requested = True
