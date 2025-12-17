from PySide6.QtCore import (
    QSize,
    Qt
)
from PySide6.QtGui import (
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
    QSizePolicy
)

from panels.process.choose_images_dialog import ChooseImagesDialog
from panels.modified_widgets import NonScrollComboBox, AutoHeightTextBrowser

from models import AppState, ProcessPanelState

from pathlib import Path
import math
import os

class ProcessPanel(QWidget):
    """Batch image processing operations."""

    def __init__(self, app_state: AppState):
        super().__init__()
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
        self.choose_dest_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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
        self.multiproc_cores_combo.addItem(f"{self.max_workers} (max)")
        for n in range(self.max_workers-1, 0, -1):
            self.multiproc_cores_combo.addItem(str(n))

        # -- output box --
        output_group = QGroupBox("Processing Output")
        output_group_layout = QVBoxLayout(output_group)
        output_group_layout.setContentsMargins(11, 5, 11, 11)
        layout.addWidget(output_group)
        
        # buttons
        buttons_layout = QHBoxLayout()
        output_group_layout.addLayout(buttons_layout)

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("StartProcessing")

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("StopProcessing")
        self.stop_btn.setDisabled(True)

        # add horizontal space
        space_widget = QWidget()
        space_widget.setFixedWidth(100)
        buttons_layout.addWidget(space_widget)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.start_btn)

        # text browser
        self.text_browser = QTextBrowser()
        self.text_browser.setMinimumHeight(200)
        output_group_layout.addWidget(self.text_browser)
    
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
    
    def to_state(self) -> ProcessPanelState:
        """Return all current fields as an `ProcessPanelState` object."""
        return ProcessPanelState(
            chosen_images=[(str(path), checked) for path, checked in self.chosen_images],
            destination_path="" if self.destination_path is None else str(self.destination_path),
            use_multiprocessing=self.use_multiproc_checkbox.isChecked()
        )