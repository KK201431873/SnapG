from PySide6.QtCore import (
    QSize,
    Qt,
    QThread
)
from PySide6.QtGui import (
    QCloseEvent,
    QIcon,
    QTextOption
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QPushButton,
    QGroupBox,
    QTextBrowser,
    QFrame,
    QLabel,
    QCheckBox,
    QHBoxLayout,
    QFileDialog,
    QSizePolicy,
    QMessageBox,
    QProgressBar
)

from panels.process.choose_images_dialog import ChooseImagesDialog
from panels.process.batch_worker import BatchWorker
from panels.modified_widgets import NonScrollComboBox, AutoHeightTextBrowser

from models import AppState, ProcessPanelState, Settings, SegmentationData

from datetime import datetime
from pathlib import Path
import numpy.typing as npt
from cv2 import imread
import time
import math
import os

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self, app_state: AppState):
        super().__init__()

        # panel state
        self.chosen_images: list[tuple[Path, bool]] = [
            (Path(path), checked) for path, checked in app_state.process_panel_state.chosen_images
        ]
        self.destination_path: Path | None = None
        destination_path_str = app_state.process_panel_state.destination_path
        if destination_path_str != "":
            try:
                dest_path = Path(destination_path_str)
                if dest_path.is_dir():
                    self.destination_path = dest_path
            except Exception as e:
                self.destination_path = None
        self.settings: Settings = app_state.settings

        # == Gui ==
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # -- data preparation --
        data_prep_group = QGroupBox("Data Preparation")
        data_prep_group.setContentsMargins(2, 2, 2, 2)
        data_prep_group_layout = QVBoxLayout(data_prep_group)
        data_prep_group_layout.setContentsMargins(11, 5, 11, 11)
        layout.addWidget(data_prep_group)

        # chosen images label
        self.chosen_images_label = QLabel("No Images Selected")
        data_prep_group_layout.addWidget(self.chosen_images_label)
        self._update_images_label()

        # choose images button
        self.choose_images_btn = QPushButton("Choose Images")
        self.choose_images_btn.clicked.connect(self._choose_files)
        data_prep_group_layout.addWidget(self.choose_images_btn)

        # -- processing options
        proc_options_group = QGroupBox("Processing Options")
        proc_options_group.setContentsMargins(2, 2, 2, 2)
        proc_options_layout = QVBoxLayout(proc_options_group)
        proc_options_layout.setContentsMargins(11, 5, 11, 11)
        layout.addWidget(proc_options_group)

        # chosen destination path label
        self.choose_dest_label = AutoHeightTextBrowser()
        self.choose_dest_label.setReadOnly(True)
        self.choose_dest_label.setFrameShape(QFrame.Shape.NoFrame)
        self.choose_dest_label.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.choose_dest_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.choose_dest_label.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.choose_dest_label.wheelEvent = (lambda event: event.ignore())
        self.choose_dest_label.setText("No Path Selected")
        proc_options_layout.addWidget(self.choose_dest_label)
        self._update_path_label()

        # choose dest path button
        self.choose_dest_btn = QPushButton("Choose Destination Path")
        self.choose_dest_btn.clicked.connect(self._choose_dest_path)
        proc_options_layout.addWidget(self.choose_dest_btn)

        # multiprocessing checkbox
        use_multiproc_layout = QHBoxLayout()
        proc_options_layout.addLayout(use_multiproc_layout)
        
        # check if multiprocessing is possible
        cpu_count: int | None = os.cpu_count()
        self.max_workers: int = max(0, (cpu_count or 0) - 1)
        self.multiprocessing_enabled: bool = self.max_workers > 0

        if self.multiprocessing_enabled:
            use_multiproc_label = QLabel("Use Multiprocessing (Recommended)")
        else:
            use_multiproc_label = QLabel("System doesn't support multiprocessing!")
            use_multiproc_label.setStyleSheet("QLabel { color: red; }")
        use_multiproc_layout.addWidget(use_multiproc_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.use_multiproc_checkbox = QCheckBox()
        use_multiproc_layout.addWidget(self.use_multiproc_checkbox, alignment=Qt.AlignmentFlag.AlignRight)
        if self.multiprocessing_enabled:
            self.use_multiproc_checkbox.setChecked(app_state.process_panel_state.use_multiprocessing)
        else:
            self.use_multiproc_checkbox.setChecked(False)
            self.use_multiproc_checkbox.setCheckable(False)
            self.use_multiproc_checkbox.setDisabled(True)

        # multiprocessing combobox
        multiproc_workers_widget = QWidget()
        multiproc_workers_layout = QHBoxLayout(multiproc_workers_widget)
        multiproc_workers_layout.setContentsMargins(0, 0, 0, 0)
        proc_options_layout.addWidget(multiproc_workers_widget)
        # set/connect checkbox state
        if self.multiprocessing_enabled:
            multiproc_workers_widget.setDisabled(not app_state.process_panel_state.use_multiprocessing)
            self.use_multiproc_checkbox.stateChanged.connect(
                lambda _: multiproc_workers_widget.setDisabled(not self.use_multiproc_checkbox.isChecked())
            )
        else:
            multiproc_workers_widget.setDisabled(True)

        multiproc_workers_label = QLabel("Number of Workers")
        multiproc_workers_layout.addWidget(multiproc_workers_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.multiproc_cores_combo = NonScrollComboBox()
        self.multiproc_cores_combo.setFixedWidth(100)
        self.multiproc_cores_combo.setToolTip(
            "Number of worker processes.\n"
            "'Max' uses all available CPU cores except one."
        )
        multiproc_workers_layout.addWidget(self.multiproc_cores_combo)
        
        # get worker counts
        self.combo_choice_to_workers: dict[str, int] = { f"{self.max_workers} (max)": self.max_workers }
        self.multiproc_cores_combo.addItem(f"{self.max_workers} (max)")
        for n in range(self.max_workers-1, 0, -1):
            self.multiproc_cores_combo.addItem(str(n))
            self.combo_choice_to_workers[str(n)] = n

        # -- output box --
        output_group = QGroupBox("Processing Output")
        output_group_layout = QVBoxLayout(output_group)
        output_group_layout.setContentsMargins(11, 5, 11, 11)
        layout.addWidget(output_group)
        
        # buttons
        buttons_layout = QHBoxLayout()
        output_group_layout.addLayout(buttons_layout)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(65)

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("StartProcessing")
        self.start_btn.setFixedWidth(60)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("StopProcessing")
        self.stop_btn.setDisabled(True)
        self.stop_btn.setFixedWidth(60)

        # add buttons
        buttons_layout.addWidget(clear_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setVisible(False)  # hidden
        output_group_layout.addWidget(self.progress_bar)

        # eta label
        self.eta_label = QLabel("")
        self.eta_label.setVisible(False)
        output_group_layout.addWidget(self.eta_label)

        # text browser
        self.text_browser = QTextBrowser()
        self.text_browser.setMinimumHeight(200)
        self.text_browser.setHtml(app_state.process_panel_state.output_text)
        clear_btn.clicked.connect(self.text_browser.clear)
        output_group_layout.addWidget(self.text_browser)

        # -- worker thread --
        self.worker_thread = QThread(self)
        self.batch_worker = BatchWorker()
        self.batch_worker.moveToThread(self.worker_thread)

        self.start_btn.clicked.connect(self._start_processing)
        self.stop_btn.clicked.connect(self._stop_processing)
        self.currently_processing = False
        self.start_processing_time = -1
        self.total_images = 0
        self.completed_images = 0

        self.batch_worker.progress.connect(self._update_progress)
        self.batch_worker.error.connect(
            lambda e: self.text_browser.append(f"<span style='color:red'>{e}</span>")
        )
        self.batch_worker.finished.connect(self._on_processing_finished)

        self.worker_thread.start()
    
    def receive_settings(self, settings: Settings):
        """Receive new settings."""
        self.settings = settings
    
    def _update_images_label(self):
        """Updates the images chosen label with the number of selected images."""
        if len(self.chosen_images) == 0:
            self.chosen_images_label.setText("No Images Selected")
            return
        # count selected files
        total_selected = sum([1 for _, checked in self.chosen_images if checked])
        total_unselected = len(self.chosen_images) - total_selected
        self.chosen_images_label.setText(f"{total_selected} images selected ({total_unselected} unselected)")
    
    def _update_path_label(self):
        """Updates the destination path label."""
        if self.destination_path is None:
            self.choose_dest_label.setText("No Path Selected")
            self.choose_dest_label.setToolTip("No Path Selected")
            return
        # cast Path to str
        text = f"<b>Destination</b>: {str(self.destination_path)}"
        self.choose_dest_label.setHtml(text)
        self.choose_dest_label.setToolTip(text)
        self._update_text_browser_height()
    
    def _update_text_browser_height(self):
        """Updates height of destination path display."""
        doc = self.choose_dest_label.document()

        height = int(doc.size().height())
        margins = self.choose_dest_label.contentsMargins()

        total_height = (
            height
            + margins.top()
            + margins.bottom()
            + 2  # small safety padding
        )

        self.choose_dest_label.setFixedHeight(total_height)
        cursor = self.choose_dest_label.textCursor() # scroll to top
        cursor.setPosition(0)
        self.choose_dest_label.setTextCursor(cursor)
    
    def _choose_files(self):
        """Show dialog for selecting image files."""
        dialog = ChooseImagesDialog(
            chosen_images=self.chosen_images,
            parent=self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        # update internal state if user pressed OK
        self.chosen_images = dialog.get_chosen_images()
        self._update_images_label()
    
    def _choose_dest_path(self):
        """Show dialog for selecting destination path."""
        directory = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Destination Path",
            options=QFileDialog.Option.ShowDirsOnly
        )
        if not directory:
            return
        
        dest_path = Path(directory)
        if not dest_path.is_dir():
            return
        
        # update internal state
        self.destination_path = dest_path
        self._update_path_label()
    
    def get_currently_processing(self) -> bool:
        """Returns whether a batch is currently being processed."""
        return self.currently_processing
    
    def _start_processing(self):
        """Attempt to begin image processing."""
        # check if images selected
        raw_image_paths: list[Path] = [p for p, checked in self.chosen_images if checked]
        if len(raw_image_paths) == 0:
            QMessageBox.warning(self, "Start Processing", "Please select images to process.")
            return
        
        # check destination path
        if self.destination_path is None:
            QMessageBox.warning(self, "Start Processing", "Please select a destination path.")
            return
        
        # check if valid images
        filtered_image_paths: list[Path] = []
        invalid_paths = set()
        for p in raw_image_paths:
            valid = p.exists()
            if valid:
                try:
                    img_np = imread(str(p))
                    if img_np is None:
                        valid = False
                    else:
                        filtered_image_paths.append(p)
                except Exception as e:
                    valid = False
            if not valid:
                # let user handle invalid image
                reply = QMessageBox.question(
                    self,
                    "Start Processing",
                    f"Could not read image '{p.name}'. Discard and skip file?",
                    QMessageBox.StandardButton.Abort | QMessageBox.StandardButton.Discard,
                    QMessageBox.StandardButton.Abort
                )
                if reply == QMessageBox.StandardButton.Abort:
                    return
                else:
                    invalid_paths.add(p)
        invalid_paths = list(invalid_paths)
        if len(invalid_paths) > 0:
            # remove invalid files
            self.chosen_images = [
                img for img in self.chosen_images if img[0] not in invalid_paths
            ]
            self._update_images_label()

        # get number of workers
        workers = 1
        if self.use_multiproc_checkbox.isChecked():
            text = self.multiproc_cores_combo.currentText()
            if text not in self.combo_choice_to_workers.keys(): # sanity check
                QMessageBox.warning(self, "Start Processing", f"'{text}' is not a valid number of workers.")
                return
            workers = self.combo_choice_to_workers[text]
        
        # create save dir
        if self.destination_path.is_file(): # sanity check (dest path should be a directory)
            self.destination_path = self.destination_path.parent

        formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = self.destination_path / f"SnapG_seg_{formatted_datetime}"
        save_dir.mkdir(parents=True, exist_ok=True)

        # signal start
        self.batch_worker.start.emit(
            filtered_image_paths,
            self.settings,
            workers,
            save_dir,
        )

        # update gui
        self.start_btn.setDisabled(True)
        self.stop_btn.setDisabled(False)

        self.text_browser.clear()
        plural_imgs = "" if len(filtered_image_paths) == 1 else "s"
        plural_wrkr = "" if workers == 1 else "s"
        self.text_browser.append(f"<b>Processing {len(filtered_image_paths)} image{plural_imgs} with {workers} worker{plural_wrkr}…</b>")
        self.text_browser.append(f"<b>(Started on {datetime.today().strftime('%Y-%m-%d %H:%M:%S')})</b>")
        
        # progress bar & eta
        self.total_images = len(filtered_image_paths)
        self.completed_images = 0
        self.progress_bar.setMaximum(self.total_images)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.eta_label.setVisible(True)
        self.eta_label.setText("Estimating time remaining…")

        # update state
        self.start_processing_time = time.perf_counter()
        self.currently_processing = True
    
    def _update_progress(self, completed_image: Path):
        """Updates output box and progress bar."""
        # output box
        self.text_browser.append(f"Processed {completed_image.name}.")

        # progress bar
        self.completed_images += 1
        self.progress_bar.setValue(self.completed_images)

        # eta
        elapsed = time.perf_counter() - self.start_processing_time
        if self.completed_images > 0:
            avg_time = elapsed / self.completed_images
            remaining = self.total_images - self.completed_images
            eta_seconds = int(avg_time * remaining)

            self.eta_label.setText(
                f"Remaining time: {self._format_remaining_time(eta_seconds)}"
            )
    
    def _stop_processing(self):
        """Send stop request to batch worker and update GUI."""
        self.batch_worker.stop()
        self.start_btn.setDisabled(True)
        self.stop_btn.setDisabled(True)
        self.progress_bar.setVisible(False)
        self.eta_label.setVisible(False)

    def _on_processing_finished(self):
        """Update GUI and internal state."""
        self.start_btn.setDisabled(False)
        self.stop_btn.setDisabled(True)
        elapsed_time = int(time.perf_counter() - self.start_processing_time)
        self.text_browser.append(f"<b>Finished in {self._format_remaining_time(elapsed_time)}.</b>")
        self.progress_bar.setVisible(False)
        self.eta_label.setVisible(False)
        self.currently_processing = False
        
    def _format_remaining_time(self, seconds_remaining: int) -> str:
        """Format number of seconds to [M]m[S]s."""
        seconds_remaining = int(seconds_remaining)
        if seconds_remaining < 60:
            return f"{seconds_remaining}s"
        else:
            minutes = seconds_remaining // 60
            seconds = seconds_remaining % 60
            return f"{minutes}m{f"{seconds}s" if seconds > 0 else ""}"
    
    def to_state(self) -> ProcessPanelState:
        """Return all current fields as an `ProcessPanelState` object."""
        return ProcessPanelState(
            chosen_images=[(str(path), checked) for path, checked in self.chosen_images],
            destination_path="" if self.destination_path is None else str(self.destination_path),
            use_multiprocessing=self.use_multiproc_checkbox.isChecked(),
            output_text=self.text_browser.toHtml()
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Shut down batch worker."""
        if self.batch_worker:
            self.batch_worker.stop()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit() 
        event.accept()