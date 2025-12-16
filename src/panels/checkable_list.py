from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QApplication
)
from typing import Any

class CheckableListWidget(QListWidget):
    """A QListWidget that supports Shift+Click and Ctrl+Click for multiple selection with checkboxes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anchor: QListWidgetItem | None = None
        self.anchor_state: Qt.CheckState | None = None
        self.original_states: dict[tuple[str, Any], Qt.CheckState] | None = None
        self.drag_start_position: QPoint | None = None
        self.dragging: bool = False
        self.processing: bool = False  # Prevent recursive signal handling
        
        # Only connect to itemSelectionChanged
        self.itemSelectionChanged.connect(self._handle_selection_change)

    def _handle_selection_change(self):
        """Handle selection changes for extended selection checkbox syncing."""
        if self.processing or self.dragging:
            return
            
        current_selection = self.selectedItems()
        if len(current_selection) == 0:
            self.original_states = None
            self.anchor = None
            self.anchor_state = None
            return

        modifiers = QApplication.keyboardModifiers()
        is_shift = modifiers & Qt.KeyboardModifier.ShiftModifier
        is_ctrl = modifiers & Qt.KeyboardModifier.ControlModifier
        
        # Single click without modifiers - establish new anchor
        if len(current_selection) == 1 and not is_shift and not is_ctrl:
            self.anchor = current_selection[0]
            # Toggle the anchor's check state
            new_state = (Qt.CheckState.Checked if self.anchor.checkState() == Qt.CheckState.Unchecked 
                        else Qt.CheckState.Unchecked)
            self.anchor.setCheckState(new_state)
            self.anchor_state = new_state
            # Store original states for all items
            self.original_states = {
                (self.item(i).text(), self.item(i).data(Qt.ItemDataRole.UserRole)): 
                self.item(i).checkState() 
                for i in range(self.count())
            }
            return

        # Extended selection (Shift or Ctrl+Shift)
        if self.anchor is None or self.original_states is None or self.anchor_state is None:
            return

        self.processing = True
        try:
            # Apply anchor state to all selected items
            for item in current_selection:
                item.setCheckState(self.anchor_state)
            
            # Restore original state to unselected items
            for i in range(self.count()):
                item = self.item(i)
                if item not in current_selection:
                    key = (item.text(), item.data(Qt.ItemDataRole.UserRole))
                    if key in self.original_states:
                        item.setCheckState(self.original_states[key])
        finally:
            self.processing = False

    def mousePressEvent(self, event: QMouseEvent):
        """Store the starting position of the mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self.dragging = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Clear the starting position when the button is released."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = None
            self.dragging = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Detect if user is dragging to scroll (not selecting)."""
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drag_start_position is not None:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            if distance > QApplication.startDragDistance():
                self.dragging = True
        super().mouseMoveEvent(event)