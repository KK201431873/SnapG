from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QGroupBox,
    QWidget,
    QCheckBox
)

class RemoveFilesDialog(QDialog):
    def __init__(
        self,
        image_files: list[Path],
        seg_files: list[Path],
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Close Files")
        self.setModal(True)
        self.resize(640, 480)

        main_layout = QVBoxLayout(self)

        # list
        list_widget = QWidget()
        list_layout = QHBoxLayout(list_widget)
        list_layout.setStretch(0, 1)
        list_layout.setStretch(1, 1)

        # --- image files ---
        image_files_cp = image_files.copy()
        image_files_cp.sort()
        self.image_list = self._create_file_list(
            "Image Files",
            image_files_cp,
        )
        self.image_list["group"].setMinimumWidth(200)
        self.image_list["group"].setMinimumHeight(200)

        # --- segmentation files ---
        seg_files_cp = seg_files.copy()
        seg_files_cp.sort()
        self.seg_list = self._create_file_list(
            "Segmentation Files",
            seg_files_cp,
        )
        self.seg_list["group"].setMinimumWidth(200)
        self.seg_list["group"].setMinimumHeight(200)

        list_layout.addWidget(self.image_list["group"])
        list_layout.addWidget(self.seg_list["group"])

        main_layout.addWidget(list_widget)

        # --- buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

        main_layout.addLayout(button_layout)

    # ---------- helpers ----------

    def _create_file_list(self, title: str, files: list[Path]):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        # multi-checkbox
        multi_checkbox = QCheckBox("No Items Selected")
        layout.addWidget(multi_checkbox)
        multi_checkbox.setTristate(True)
        multi_checkbox.setDisabled(True)

        # list
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        for path in files:
            item = QListWidgetItem(path.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, path)
            list_widget.addItem(item)

        layout.addWidget(list_widget)
        
        # connect list to multi-checkbox and vice versa
        multi_checkbox.stateChanged.connect(
            lambda state: self._apply_multi_checkbox(state, multi_checkbox, list_widget)
        )

        list_widget.itemSelectionChanged.connect(
            lambda: self._update_multi_checkbox(multi_checkbox, list_widget)
        )

        return {
            "group": group,
            "list": list_widget,
        }

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
        """Connect list to multi-checkbox."""
        multi_checkbox.blockSignals(True)

        def disable(): # internal helper
            multi_checkbox.setCheckState(Qt.CheckState.Unchecked)
            multi_checkbox.setText("No Items Selected")
            multi_checkbox.setDisabled(True)
            multi_checkbox.blockSignals(False)
        
        # check empty selection
        selection = list_widget.selectedItems()
        if len(selection) == 0:
            disable()
            return
        
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

    # ---------- public API ----------

    def selected_image_files(self) -> list[Path]:
        return self._checked_files(self.image_list["list"])

    def selected_seg_files(self) -> list[Path]:
        return self._checked_files(self.seg_list["list"])

    def _checked_files(self, list_widget: QListWidget) -> list[Path]:
        result: list[Path] = []

        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                result.append(item.data(Qt.ItemDataRole.UserRole))

        return result
