from PySide6.QtCore import (
    QObject, 
    Signal, 
    Slot
)

from imgproc.generate_csv_data import get_csv_lines

class GenerateDataWorker(QObject):
    finished = Signal(list, list)      # out_imgs, csv_lines
    error = Signal(str)

    def __init__(self, segmentations, font_path, timestamp):
        super().__init__()
        self.segmentations = segmentations
        self.font_path = font_path
        self.timestamp = timestamp

    @Slot()
    def run(self):
        try:
            out_imgs, csv_lines = get_csv_lines(
                self.segmentations,
                self.font_path,
                self.timestamp
            )
            self.finished.emit(out_imgs, csv_lines)
        except Exception as e:
            self.error.emit(str(e))
