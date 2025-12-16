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

class ChooseImagesDialog(QDialog):
    def __init__(
        self,
        image_states: list[tuple[Path, bool]],
        parent=None,
    ):
        super().__init__(parent)
        self.image_states = image_states

        self.setWindowTitle("Choose Image Batch")
        self.setModal(True)
        self.resize(320, 480)

        main_layout = QVBoxLayout(self)

        # file list
        self.image_list = self._create_file_list("Image Files")
        self.image_list["group"].setMinimumWidth(200)
        self.image_list["group"].setMinimumHeight(200)

        main_layout.addWidget(self.image_list["group"])

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

    def _create_file_list(self, title: str):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)

        for path, checked in self.image_states:
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

    # ---------- public API ----------
    def get_file_states(self) -> list[tuple[Path, bool]]:
        result: list[tuple[Path, bool]] = []
        list_widget: QListWidget = self.image_list["list"]
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            result.append((
                item.data(Qt.ItemDataRole.UserRole), 
                item.checkState() == Qt.CheckState.Checked
            ))
        return result

