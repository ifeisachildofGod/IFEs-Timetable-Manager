
from .imports import *
from .functions_and_uncategorized import *

from widgets.base import BaseWidget, Image


class DropdownLabeledField(QWidget):
    def __init__(
        self,
        title: str,
        content: QWidget,
        expanded: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        
        self.setStyleSheet("""
            /* Header */
            QFrame.dropdown-header {
                /*background-color: #252526;*/
                border: 1px solid #3c3c3c;
                border-radius: 8px;
            }

            QFrame.dropdown-header:hover {
                /*background-color: #2a2d2e;*/
            }

            /* Title */
            QLabel.dropdown-title {
                color: #d4d4d4;
                font-size: 13px;
                font-weight: 500;
            }

            /* Arrow */
            QLabel.dropdown-arrow {
                color: #9cdcfe;
                font-size: 12px;
            }

            /* Content */
            QFrame.dropdown-container {
                border: 1px solid white;
                border-top: none;
                border-radius: 0 0 8px 8px;
                /*background-color: #1e1e1e;*/
            }

                           """)
        
        self._expanded = True
        self.content = content

        # -----------------------
        # Header
        # -----------------------
        self.header = QFrame()
        self.header.setProperty("class", "dropdown-header")
        self.header.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "dropdown-title")

        self.arrow = RotatableLabel("▼", 90)
        self.arrow.setProperty("class", "dropdown-arrow")
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.arrow)

        # -----------------------
        # Content container
        # -----------------------
        self.container = QFrame()
        self.container.setProperty("class", "dropdown-container")

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(10, 8, 10, 10)
        container_layout.addWidget(self.content)
        
        # -----------------------
        # Main layout
        # -----------------------
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.header)
        layout.addWidget(self.container)

        self.container.setMaximumHeight(0 if not self._expanded else 1_000_000)
        self._update_arrow()

        # Click handling
        self.header.mousePressEvent = self._toggle  # type: ignore
        
        self._end = 0
        
        if not expanded:
            self._toggle(None)

    def addWidget(self, widget: QWidget, stretch: int = 0, alignment: Qt.AlignmentFlag | None = None):
        if alignment is not None:
            self.content.layout().addWidget(widget, stretch, alignment)
        else:
            self.content.layout().addWidget(widget, stretch)
    
    # -----------------------
    # Logic
    # -----------------------
    def _toggle(self, event):
        self.setExpanded(not self._expanded)

    def setExpanded(self, value: bool):
        if self._expanded == value:
            return

        self._expanded = value
        self._update_arrow()
        
        self.container.setVisible(self._expanded)

    def _update_arrow(self):
        self.arrow.setAngle(0 if self._expanded else 90)

    def isExpanded(self) -> bool:
        return self._expanded

class RotatableLabel(QLabel):
    mouseclicked = pySignal()
    
    def __init__(self, text, angle: int = 0, parent=None):
        super().__init__(text, parent)
        self.angle = angle  # Angle in degrees to rotate the text
        self.setProperty("class", "Arrow")
    
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.mouseclicked.emit()
    
    def setAngle(self, angle):
        self.angle = angle
        self.update()  # Trigger a repaint
    
    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Save the painter's current state
        painter.save()

        # Translate to the center of the label
        center = self.rect().center()
        painter.translate(center)

        # Rotate the painter
        painter.rotate(self.angle)

        # Translate back and draw the text
        center.setX(center.x() + (2 if self.angle >= 180 else -1))
        painter.translate(-center)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

        # Restore the painter's state
        painter.restore()
