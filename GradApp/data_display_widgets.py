
from .functions_and_uncategorized import *
from .imports import *
from .communication import *


class BarChartCanvas(FigureCanvas):
    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(6, 5), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
        self.title, self.x_label, self.y_label = title, x_label, y_label
        
        self.set_vars(self.title, self.x_label, self.y_label)
    
    def set_vars(self, title: str, x_label: str, y_label: str):
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
    
    def bar(self, x_values, y_values, display_values = False, **kwargs):
        bars = self.axes.bar(x_values, y_values, **kwargs)
        
        # Optional: add value labels on top of each bar
        if display_values:
            for bar in bars:
                height = bar.get_height()
                self.axes.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{int(height)}', 
                                      ha='center', va='bottom')
        
        self.draw()

class GraphCanvas(FigureCanvas):
    def __init__(self, title: str, x_label: str, y_label: str):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
        self.title, self.x_label, self.y_label = title, x_label, y_label
        
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
        
        if y:
            self.axes.legend()
        self.draw()


class BarWidget(QWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        layout.addWidget(self.container)
        
        self.main_keys_widget = QWidget()
        self.main_keys_layout = QHBoxLayout()
        self.main_keys_widget.setLayout(self.main_keys_layout)
        
        self.bar_canvas = BarChartCanvas(title, x_label, y_label)
        
        self.main_layout.addWidget(self.main_keys_widget)
        self.main_layout.addWidget(self.bar_canvas)
    
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
            
            self.main_keys_layout.addWidget(keys_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.bar_canvas.bar(data[0], data[1], display_values=True, color=color, edgecolor="black")
    
    def set_title(self, title: str):
        self.bar_canvas.set_vars(title, self.bar_canvas.x_label, self.bar_canvas.y_label)
    
    def clear(self):
        y_lim = self.bar_canvas.axes.get_ylim()
        
        self.bar_canvas.axes.clear()
        
        self.bar_canvas.axes.set_ylim(y_lim)
        
        clear_layout(self.main_keys_layout)
        
        self.bar_canvas.set_vars(self.bar_canvas.title, self.bar_canvas.x_label, self.bar_canvas.y_label)

class GraphWidget(QWidget):
    def __init__(self, title: str, x_label: str, y_label: str):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.container.setLayout(self.main_layout)
        
        layout.addWidget(self.container)
        
        self.graph = GraphCanvas(title, x_label, y_label)
        self.main_layout.addWidget(self.graph)
    
    def plot(self, x, y, **kwargs):
        self.graph.plot(x, y, **kwargs)
    
    def set_title(self, title: str):
        self.graph.set_vars(title, self.graph.x_label, self.graph.y_label)
    
    def clear(self):
        self.graph.axes.clear()
        
        self.graph.set_vars(self.graph.title, self.graph.x_label, self.graph.y_label)

