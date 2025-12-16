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
    QWidget
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
        self.image_list = self._create_file_list("Image Files")
        self.image_list["group"].setMinimumWidth(200)
        self.image_list["group"].setMinimumHeight(200)

        main_layout.addWidget(self.image_list["group"])

        # --- buttons ---
        button_layout = QVBoxLayout()

        # top row
        button_top_layout = QHBoxLayout()
        button_top_layout.addStretch()
        button_layout.addLayout(button_top_layout)

        add_images_btn = QPushButton("Add Images")
        add_images_btn.clicked.connect(self._add_images)

        remove_images_btn = QPushButton("Remove Images")
        # add_images_btn.clicked.connect(self._remove_images)

        select_all_btn = QPushButton("Select All")
        # add_images_btn.clicked.connect(self._select_all)

        deselect_all_btn = QPushButton("Deselect All")
        # add_images_btn.clicked.connect(self._deselect_all)

        button_top_layout.addWidget(add_images_btn)
        button_top_layout.addWidget(remove_images_btn)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Raised)
        button_top_layout.addWidget(separator)
        button_top_layout.addWidget(select_all_btn)
        button_top_layout.addWidget(deselect_all_btn)

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

    def _create_file_list(self, title: str):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        for path, checked in self.chosen_images:
            item = QListWidgetItem(path.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, path)
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        return {
            "group": group,
            "list": list_widget,
        }

    def _add_images(self):
        """Show dialog to select image files."""


    # ---------- public API ----------
    def get_chosen_images(self) -> list[tuple[Path, bool]]:
        result: list[tuple[Path, bool]] = []
        list_widget: QListWidget = self.image_list["list"]
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            result.append((
                item.data(Qt.ItemDataRole.UserRole), 
                item.checkState() == Qt.CheckState.Checked
            ))
        return result

