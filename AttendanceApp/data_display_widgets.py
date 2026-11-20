
from widgets.base import *

from .functions_and_uncategorized import *
from .imports import *
from .communication import *


class ScrollableCanvas(FigureCanvas):

    def wheelEvent(self, event: QWheelEvent):
        # Ctrl + mouse wheel: zoom the Matplotlib graph.
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2

            # Get the mouse position relative to the graph.
            mouse_pos = event.position()

            # Convert the mouse position to Matplotlib coordinates.
            width, height = self.width(), self.height()

            if width <= 0 or height <= 0:
                event.ignore()
                return

            x_fraction = mouse_pos.x() / width
            y_fraction = 1 - (mouse_pos.y() / height)

            # Get the current axis limits.
            xlim = self.axes.get_xlim()
            ylim = self.axes.get_ylim()

            # Zoom around the mouse position.
            x_center = xlim[0] + x_fraction * (xlim[1] - xlim[0])
            y_center = ylim[0] + y_fraction * (ylim[1] - ylim[0])

            self.axes.set_xlim(
                x_center - (x_center - xlim[0]) / zoom_factor,
                x_center + (xlim[1] - x_center) / zoom_factor
            )

            self.axes.set_ylim(
                y_center - (y_center - ylim[0]) / zoom_factor,
                y_center + (ylim[1] - y_center) / zoom_factor
            )

            self.draw_idle()
            event.accept()
            return

        # Normal mouse wheel: scroll the parent QScrollArea.
        parent = self.parentWidget()

        while parent is not None:
            if isinstance(parent, QScrollArea):
                viewport = parent.viewport()

                forwarded_event = QWheelEvent(
                    QPointF(
                        viewport.mapFromGlobal(
                            event.globalPosition().toPoint()
                        )
                    ),
                    event.globalPosition(),
                    event.pixelDelta(),
                    event.angleDelta(),
                    event.buttons(),
                    event.modifiers(),
                    event.phase(),
                    event.inverted()
                )

                QApplication.sendEvent(viewport, forwarded_event)

                event.accept()
                return

            parent = parent.parentWidget()

        super().wheelEvent(event)

class BarChartCanvas(ScrollableCanvas):

    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(6, 5), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

        self.title, self.x_label, self.y_label = (
            title, x_label, y_label
        )

        self.set_vars(self.title, self.x_label, self.y_label)

    def set_vars(self, title: str, x_label: str, y_label: str):
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)

    def bar(self, x_values, y_values, display_values=False, **kwargs):
        bars = self.axes.bar(x_values, y_values, **kwargs)

        if display_values:
            for bar in bars:
                height = bar.get_height()

                self.axes.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 0.5,
                    f'{int(height)}',
                    ha='center',
                    va='bottom'
                )

        self.draw()

class GraphCanvas(ScrollableCanvas):

    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

        self.title, self.x_label, self.y_label = (
            title, x_label, y_label
        )

        self.set_vars(self.title, self.x_label, self.y_label)

    def set_vars(self, title: str, x_label: str, y_label: str):
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)

    def plot(self, x, y, **kwargs):
        if x is not None:
            self.axes.plot(x, y, **kwargs)
        else:
            self.axes.plot(y, **kwargs)

        handles, labels = self.axes.get_legend_handles_labels()

        if labels:
            self.axes.legend(loc="upper right")

        self.draw()

class BarWidget(BaseWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        self.main_keys_widget = BaseWidget()
        self.bar_canvas = BarChartCanvas(title, x_label, y_label)
        
        self.addWidget(self.main_keys_widget)
        self.addWidget(self.bar_canvas)
    
    def add_data(self, name: str, color, data: tuple[list, list] | dict, add_key: bool = True):
        if isinstance(data, dict):
            data = list(data), list(data.values())
        
        if add_key:
            keys_widget, keys_layout = create_widget(None, QHBoxLayout)
            
            keys_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            
            key_frame = QFrame()
            key_frame.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid black;
            """)
            key_frame.setFixedSize(20, 20)
            
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            keys_layout.addWidget(key_frame)
            keys_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignLeft)
            
            self.main_keys_widget.addWidget(keys_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.bar_canvas.bar(data[0], data[1], display_values=True, color=color, edgecolor="black")
    
    def set_title(self, title: str):
        self.bar_canvas.set_vars(title, self.bar_canvas.x_label, self.bar_canvas.y_label)
    
    def clear(self):
        y_lim = self.bar_canvas.axes.get_ylim()
        
        self.bar_canvas.axes.clear()
        
        self.bar_canvas.axes.set_ylim(y_lim)
        
        self.main_keys_widget.clearLayout()
        
        self.bar_canvas.set_vars(self.bar_canvas.title, self.bar_canvas.x_label, self.bar_canvas.y_label)

class GraphWidget(BaseWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        self.graph = GraphCanvas(title, x_label, y_label)
        self.addWidget(self.graph)
    
    def plot(self, x, y, **kwargs):
        self.graph.plot(x, y, **kwargs)
    
    def set_title(self, title: str):
        self.graph.set_vars(title, self.graph.x_label, self.graph.y_label)
    
    def clear(self):
        self.graph.axes.clear()
        
        self.graph.set_vars(self.graph.title, self.graph.x_label, self.graph.y_label)

