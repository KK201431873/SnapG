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
    QWidget
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

        list_widget = QWidget()
        list_layout = QHBoxLayout(list_widget)
        list_layout.setStretch(0, 1)
        list_layout.setStretch(1, 1)

        # --- image files ---
        self.image_list = self._create_file_list(
            "Image Files",
            image_files,
        )
        self.image_list["group"].setMinimumWidth(200)
        self.image_list["group"].setMinimumHeight(200)

        # --- segmentation files ---
        self.seg_list = self._create_file_list(
            "Segmentation Files",
            seg_files,
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

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        for path in files:
            item = QListWidgetItem(path.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, path)
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        return {
            "group": group,
            "list": list_widget,
        }

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
