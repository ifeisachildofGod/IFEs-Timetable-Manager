
from .imports import *
from .functions_and_uncategorized import *


class TabViewWidget(QWidget):
    def __init__(self, bar_orientation: Literal["vertical", "horizontal"] = "horizontal"):
        super().__init__()
        self.bar_orientation = bar_orientation
        
        assert self.bar_orientation in ("vertical", "horizontal"), f"Invalid orientation: {self.bar_orientation}"
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        tab_layout_type = QHBoxLayout if self.bar_orientation == "horizontal" else QVBoxLayout
        main_layout_type = QHBoxLayout if self.bar_orientation == "vertical" else QVBoxLayout
        
        container = QWidget()
        layout = main_layout_type()
        container.setLayout(layout)
        
        self.current_tab = None
        self.tab_src_changed_func_mapping = {}
        
        self.tab_buttons: list[QPushButton] = []
        
        tab_widget = QWidget()
        tab_widget.setContentsMargins(0, 0, 0, 0)
        
        self.tab_layout = tab_layout_type()
        tab_widget.setLayout(self.tab_layout)
        
        self.stack = QStackedWidget()
        
        if self.bar_orientation == "vertical":
            self.tab_layout.addStretch()
        
        self.setContentsMargins(0, 0, 0, 0)
        tab_widget.setContentsMargins(0, 0, 0, 0)
        self.stack.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(tab_widget)
        layout.addWidget(self.stack)
        
        main_layout.addWidget(container)
    
    def add(self, tab_name: str, widget: QWidget, func: Callable[[int, ], None] = None):
        tab_button = QPushButton(tab_name)
        
        self.tab_buttons.append(tab_button)
        
        tab_button.setCheckable(True)
        tab_button.clicked.connect(self._make_tab_clicked_func(len(self.tab_buttons) - 1, func))
        tab_button.setProperty("class", "HorizontalTab" if self.bar_orientation == "horizontal" else "VerticalTab")
        tab_button.setContentsMargins(0, 0, 0, 0)
        
        self.tab_layout.insertWidget(len(self.tab_buttons) - 1, tab_button)
        self.stack.insertWidget(len(self.tab_buttons), widget)
        widget.setContentsMargins(0, 0, 0, 0)
        
        self.tab_buttons[0].click()
    
    def get(self, tab_name: str, default: Any = ...):
        tab_widget = (self.stack.children() + [default])[next((i for i, b in enumerate(self.tab_buttons) if b.text() == tab_name), len(self.stack.children()))]
        
        if type(tab_widget) == type(Ellipsis):
            raise KeyError(f'There is no tab named: "{tab_name}"')
        return tab_widget
    
    def index(self, widget: QWidget):
        return next(i for i, w in enumerate(self.stack.children()) if w == widget)
    
    def set_tab(self, tab: int | str):
        if isinstance(tab, int) and tab >= len(self.tab_buttons):
            self.stack.setCurrentIndex(tab)
        else:
            self.tab_buttons[self.index(self.get(tab)) if isinstance(tab, str) else tab].click()
    
    def _make_tab_clicked_func(self, index: int, clicked_func: Callable[[int, ], None] | None):
        self.tab_src_changed_func_mapping[self.tab_buttons[index].text()] = clicked_func
        
        def func():
            if clicked_func is not None:
                clicked_func(index)
            
            self.stack.setCurrentIndex(index)
            self.current_tab = self.tab_buttons[index].text()
            
            for i, button in enumerate(self.tab_buttons):
                button.setChecked(i == index)
            
            child: QWidget = self.stack.children()[index]
            if child.isWidgetType():
                child.setFocus()
        
        return func

class OptionsMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
    
    def set_options(self, options: dict[str, Callable]):
        clear_layout(self.main_layout)
        
        self.add_options(options)
    
    def add_options(self, options: dict[str, Callable]):
        for option_name, option_func in options.items():
            btn = QLabel(option_name)
            btn.setProperty("class", "QPushButton")
            btn.mousePressEvent = self._option_selected(option_func)
            
            self.main_layout.addWidget(btn)
    
    def _option_selected(self, option_func: Callable):
        def func(a0):
            option_func()
            self.hide()
        
        return func

class Image(QLabel):
    def __init__(self, path: str, parent=None, width: int | None = None, height: int | None = None):
        super().__init__(parent)
        
        pixmap = QPixmap(path)
        
        if width is not None or height is not None:
            if height is not None and width is None:
                self.setFixedSize(int(height * pixmap.size().width() / pixmap.size().height()), height)
            elif width is not None and height is None:
                self.setFixedSize(width, int(width * pixmap.size().height() / pixmap.size().width()))
            else:
                self.setFixedSize(width, height)
        
        self.setScaledContents(True)  # Optional: scale image to fit self
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)


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
