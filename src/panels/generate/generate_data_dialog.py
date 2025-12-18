from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QSize,
    QThread,
    Slot,
    QUrl
)
from PySide6.QtGui import (
    QCloseEvent,
    QDesktopServices
)
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QGroupBox,
    QWidget,
    QCheckBox,
    QFileDialog,
    QMessageBox
)

from panels.generate.busy_dialog import BusyDialog
from panels.generate.generate_data_worker import GenerateDataWorker

from models import AppState, SegmentationData, ContourData, logger

from datetime import datetime
import numpy.typing as npt
import cv2

class GenerateDataDialog(QDialog):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)
        self.chosen_files: list[tuple[Path, bool]] = []
        self._dest_path: Path | None = None
        self._formatted_datetime: str | None = None

        self.setWindowTitle("Generate Segmentation Data")
        self.setModal(True)
        self.resize(480, 320)

        main_layout = QVBoxLayout(self)

        # file list
        self.list_widget = QListWidget()
        def _handle_item_changed(_):
            self.chosen_files = self._get_chosen_files()
        self.list_widget.itemChanged.connect(_handle_item_changed)

        # --- buttons ---
        button_layout = QVBoxLayout()

        # top row
        button_top_layout = QHBoxLayout()
        button_top_layout.addStretch()
        button_layout.addLayout(button_top_layout)

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self._add_files_dialog)

        self.remove_files_btn = QPushButton("Remove Files")
        self.remove_files_btn.setDisabled(True)
        self.remove_files_btn.clicked.connect(self._remove_files_dialog)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.list_widget.selectAll)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.list_widget.clearSelection)

        # Create list box here because it needs buttons to be initialized
        group_box = self._create_file_list("Segmentation Files")
        group_box.setMinimumWidth(200)
        group_box.setMinimumHeight(200)

        # first add list box, then add buttons
        main_layout.addWidget(group_box)

        button_top_layout.addWidget(add_files_btn)
        button_top_layout.addWidget(self.remove_files_btn)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Raised)
        button_top_layout.addWidget(separator)
        button_top_layout.addWidget(self.select_all_btn)
        button_top_layout.addWidget(self.deselect_all_btn)
        
        self._update_selection_buttons()

        # bottom row
        button_bottom_layout = QHBoxLayout()
        button_bottom_layout.addStretch()
        button_layout.addLayout(button_bottom_layout)

        cancel_btn = QPushButton("Close")
        cancel_btn.clicked.connect(self.hide)

        ok_btn = QPushButton("Generate")
        ok_btn.clicked.connect(self._generate_data)

        button_bottom_layout.addWidget(cancel_btn)
        button_bottom_layout.addWidget(ok_btn)

        main_layout.addLayout(button_layout)
        
    def _get_chosen_files(self) -> list[tuple[Path, bool]]:
        """Returns the user-updated list of file selections."""
        result: list[tuple[Path, bool]] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            result.append((
                item.data(Qt.ItemDataRole.UserRole), 
                item.checkState() == Qt.CheckState.Checked
            ))
        return result
    
    def _update_selection_buttons(self):
        """Enable or disable the (de)select all buttons based on whether the list is empty."""
        if self.list_widget.count() > 0:
            self.select_all_btn.setDisabled(False)
            self.deselect_all_btn.setDisabled(False)
        else:
            self.select_all_btn.setDisabled(True)
            self.deselect_all_btn.setDisabled(True)
    
    def _add_file_path(self, file_path: Path, checked: bool):
        """Adds a file path to the `QListWidget`."""
        item = QListWidgetItem(file_path.name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.list_widget.addItem(item)
        self._update_selection_buttons()
    
    def _create_file_list(self, title: str) -> QGroupBox:
        """Helper to create the file list"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        # multi-checkbox
        multi_checkbox = QCheckBox("No Items Selected")
        layout.addWidget(multi_checkbox)
        multi_checkbox.setTristate(True)
        multi_checkbox.setDisabled(True)

        # list
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        for path, checked in self.chosen_files:
            self._add_file_path(path, checked)

        layout.addWidget(self.list_widget)
        
        # connect list to multi-checkbox and vice versa
        multi_checkbox.stateChanged.connect(
            lambda state: self._apply_multi_checkbox(state, multi_checkbox, self.list_widget)
        )
        self.list_widget.itemSelectionChanged.connect(
            lambda: self._update_multi_checkbox(multi_checkbox, self.list_widget)
        )
        return group

    def _apply_multi_checkbox(self, state_int: int, multi_checkbox: QCheckBox, list_widget: QListWidget):
        """Multi-checkbox updates all selected list items."""
        state = Qt.CheckState(state_int)
        if state == Qt.CheckState.PartiallyChecked:
            return

        multi_checkbox.setTristate(False)
        target_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked \
            else Qt.CheckState.Unchecked

        for item in list_widget.selectedItems():
            item.setCheckState(target_state)

    def _update_multi_checkbox(self, multi_checkbox: QCheckBox, list_widget: QListWidget):
        """Connect list to multi-checkbox. Also updates GUI buttons."""
        multi_checkbox.blockSignals(True)

        def disable(): # internal helper
            multi_checkbox.setCheckState(Qt.CheckState.Unchecked)
            multi_checkbox.setText("No Items Selected")
            multi_checkbox.setDisabled(True)
            multi_checkbox.blockSignals(False)
            self.remove_files_btn.setDisabled(True)
        
        # check empty selection
        selection = list_widget.selectedItems()
        if len(selection) == 0:
            disable()
            return
        
        self.remove_files_btn.setDisabled(False)
        
        # determine selection state
        has_checked = False
        has_unchecked = False
        for item in selection:
            has_checked |= item.checkState() == Qt.CheckState.Checked
            has_unchecked |= item.checkState() == Qt.CheckState.Unchecked
            if has_checked and has_unchecked:
                break

        # sanity check
        if not has_checked and not has_unchecked:
            disable()
            return

        # update checkbox
        multi_checkbox.setDisabled(False)
        if has_checked and has_unchecked:
            multi_checkbox.setTristate(True)
            multi_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            multi_checkbox.setText("Check Selected")
        elif has_checked:
            multi_checkbox.setTristate(False)
            multi_checkbox.setCheckState(Qt.CheckState.Checked)
            multi_checkbox.setText("Uncheck Selected")
        else:
            multi_checkbox.setTristate(False)
            multi_checkbox.setCheckState(Qt.CheckState.Unchecked)
            multi_checkbox.setText("Check Selected")
        
        multi_checkbox.blockSignals(False)

    def _add_files_dialog(self):
        """Show dialog to select segmentation files."""
        file_names, _ = QFileDialog.getOpenFileNames(
            parent=self, 
            caption="Open Segmentation File(s)",
            filter="SEG Files (*.seg)"
        )
        # get current paths
        current_paths: list[Path] = []
        for i in range(self.list_widget.count()):
            path = self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            current_paths.append(path)

        # add new paths (no duplicates)
        file_paths = [Path(s) for s in file_names]
        for path in file_paths:
            if path not in current_paths:
                self._add_file_path(path, False)

    def _remove_files_dialog(self):
        """Show dialog to remove files."""
        selection = self.list_widget.selectedItems()

        # should never happen (button gets disabled)
        if len(selection) == 0:
            QMessageBox.warning(
                self,
                "Remove Files",
                "Please select files to remove."
            )
            return

        # Double check with user
        reply = QMessageBox.question(
            self,
            "Remove Files",
            f"Are you sure you want to remove {len(selection)} files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # remove and delete items
        if reply == QMessageBox.StandardButton.Yes:
            for item in selection:
                index = self.list_widget.row(item)
                removed_item = self.list_widget.takeItem(index)
                del removed_item
            self._update_selection_buttons()
        
    def _generate_data(self):
        """Validate files and request worker to generate data from segmentation files."""
        # check if images selected
        raw_image_paths: list[Path] = [p for p, checked in self.chosen_files if checked] 
        if len(raw_image_paths) == 0:
            QMessageBox.warning(self, "Generate Data", "Please choose segmentation files to generate data for.")
            return
        
        # choose destination path
        directory = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Generate Data: Select Destination Folder",
            options=QFileDialog.Option.ShowDirsOnly
        )
        if not directory:
            return
        
        dest_path = Path(directory)
        if not dest_path.is_dir(): # sanity check
            QMessageBox.warning(self, "Generate Data", "Chosen path is not a directory.")
            logger.err("_generate_data(): Chosen path is not a directory.", self)
            return
        
        # check if valid files
        filtered_segmentations: list[SegmentationData] = []
        invalid_paths = set()
        for p in raw_image_paths:
            valid = p.exists()
            if valid:
                seg_data = SegmentationData.from_file(p, self)
                if seg_data is None:
                    valid = False
                else:
                    filtered_segmentations.append(seg_data)
            if not valid:
                # let user handle invalid file
                reply = QMessageBox.question(
                    self,
                    "Generate Data",
                    f"Could not read file '{p.name}'. Discard and skip?",
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
            for item in invalid_paths:
                try:
                    index = self.list_widget.row(item)
                    removed_item = self.list_widget.takeItem(index)
                    del removed_item
                except Exception as e:
                    logger.err("_generate_data(): Tried to remove invalid file that did not exist in list.", self)
            self.chosen_files = [
                img for img in self.chosen_files if img[0] not in invalid_paths
            ]
            self._update_selection_buttons()
        # check if no data left
        if len(filtered_segmentations) == 0:
            QMessageBox.warning(self, "Generate Data", "No segmentation data left to process.")
            return

        # generate
        formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

        # busy dialog
        self.busy_dialog = BusyDialog("Generating segmentation data…", self)
        self.busy_dialog.show()

        # threading
        self.worker_thread = QThread(self)
        self.worker = GenerateDataWorker(
            filtered_segmentations,
            AppState.annotation_font_path(),
            formatted_datetime
        )
        self.worker.moveToThread(self.worker_thread)

        # connect signals
        self._dest_path = dest_path
        self._formatted_datetime = formatted_datetime

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_generate_finished)
        self.worker.error.connect(self._on_generate_error)

        # cleanup
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()
    
    @Slot(list, list)
    def _on_generate_finished(
        self,
        out_imgs: list[tuple[str, npt.NDArray]],
        csv_lines: list[str]
    ):
        """Receive data from worker and write to destination path."""
        self.busy_dialog.hide()
        
        dest_path = self._dest_path
        formatted_datetime = self._formatted_datetime
        if dest_path is None or formatted_datetime is None:
            return # sanity check

        save_dir = dest_path / f"SnapG_segmentation_data_{formatted_datetime}"
        save_dir.mkdir(parents=True, exist_ok=True)

        csv_filepath = save_dir / f"SnapG_segmentation_data_{formatted_datetime}.csv"
        with open(csv_filepath, "w") as f:
            f.writelines(csv_lines)

        image_dir = save_dir / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        for filename, image in out_imgs:
            cv2.imwrite(str(image_dir / filename), image)

        QMessageBox.information(
            self,
            "Generate Data",
            "Segmentation data was generated successfully."
        )
        
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(save_dir)))
    
    def _on_generate_error(self, message: str):
        """Handle worker errors."""
        self.busy_dialog.hide()
        QMessageBox.critical(self, "Generate Data Error", message)

    # -- closing --
    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
