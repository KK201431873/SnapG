from PySide6.QtCore import (
    QSize,
    Slot
)
from PySide6.QtGui import (
    QTextCursor, 
    QTextCharFormat, 
    QColor, 
    QFont
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, 
    QTextEdit,
    QTextBrowser
)

from models import AppState, logger

class OutputPanel(QWidget):
    """Textbox for showing program outputs."""

    def __init__(self, app_state: AppState):
        super().__init__()

        # add widgets to layout
        self.vlayout = QVBoxLayout(self)
        self.text_browser = QTextBrowser()
        self.vlayout.addWidget(self.text_browser)

        # add layout to current widget
        self.setLayout(self.vlayout)

        # connect Logger
        logger.printTriggered.connect(self.print)
        logger.clearTriggered.connect(self.clear)
    
    @Slot(str, bool, bool, bool, str)
    def print(self, 
              s: str, 
              bold: bool = False,
              italic: bool = False,
              underline: bool = False,
              color: str = "black"
        ):
        """Append the given string to the `OutputPanel`'s text display."""
        cursor = self.text_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        fmt.setFontPointSize(12)
        fmt.setFontItalic(italic)
        fmt.setFontUnderline(underline)
        fmt.setForeground(QColor(color))

        cursor.setCharFormat(fmt)
        cursor.insertText(s)

        # self.text_browser.setTextCursor(cursor)
        # self.text_browser.ensureCursorVisible()

    @Slot()
    def clear(self):
        """Clear the `OutputPanel`'s text display."""
        self.text_browser.clear()