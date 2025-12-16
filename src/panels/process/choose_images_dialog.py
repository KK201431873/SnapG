from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QSize
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

class ChooseImagesDialog(QDialog):
    def __init__(
        self,
        chosen_images: list[tuple[Path, bool]],
        parent=None,
    ):
        super().__init__(parent)
        self.chosen_images = chosen_images

        self.setWindowTitle("Choose Image Batch")
        self.setModal(True)
        self.resize(480, 320)

        main_layout = QVBoxLayout(self)

        # file list
        self.list_widget = QListWidget()
        group_box = self._create_file_list("Image Files")
        group_box.setMinimumWidth(200)
        group_box.setMinimumHeight(200)

        main_layout.addWidget(group_box)

        # --- buttons ---
        button_layout = QVBoxLayout()

        # top row
        button_top_layout = QHBoxLayout()
        button_top_layout.addStretch()
        button_layout.addLayout(button_top_layout)

        add_images_btn = QPushButton("Add Images")
        add_images_btn.clicked.connect(self._add_images)

        self.remove_images_btn = QPushButton("Remove Images")
        self.remove_images_btn.setDisabled(True)
        self.remove_images_btn.clicked.connect(self._remove_images)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.list_widget.selectAll)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.list_widget.clearSelection)

        button_top_layout.addWidget(add_images_btn)
        button_top_layout.addWidget(self.remove_images_btn)
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

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)

        button_bottom_layout.addWidget(cancel_btn)
        button_bottom_layout.addWidget(ok_btn)

        main_layout.addLayout(button_layout)
    
    def _update_selection_buttons(self):
        """Enable or disable the (de)select all buttons based on whether the list is empty."""
        if self.list_widget.count() > 0:
            self.select_all_btn.setDisabled(False)
            self.deselect_all_btn.setDisabled(False)
        else:
            self.select_all_btn.setDisabled(True)
            self.deselect_all_btn.setDisabled(True)
    
    def _add_image_path(self, image_path: Path, checked: bool):
        """Adds an image path to the `QListWidget`."""
        item = QListWidgetItem(image_path.name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, image_path)
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

        for path, checked in self.chosen_images:
            self._add_image_path(path, checked)

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
            self.remove_images_btn.setDisabled(True)
        
        # check empty selection
        selection = list_widget.selectedItems()
        if len(selection) == 0:
            disable()
            return
        
        self.remove_images_btn.setDisabled(False)
        
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

    def _add_images(self):
        """Show dialog to select image files."""
        file_names, _ = QFileDialog.getOpenFileNames(
            parent=self, 
            caption="Open Image(s)",
            filter="Images (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif)"
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
                self._add_image_path(path, False)

    def _remove_images(self):
        """Show dialog to remove image files."""
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

    # ---------- public API ----------
    def get_chosen_images(self) -> list[tuple[Path, bool]]:
        """Returns the user-updated list of image selections."""
        result: list[tuple[Path, bool]] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            result.append((
                item.data(Qt.ItemDataRole.UserRole), 
                item.checkState() == Qt.CheckState.Checked
            ))
        return result

