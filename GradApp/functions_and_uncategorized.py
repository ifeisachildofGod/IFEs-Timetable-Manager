
from .imports import *


def check_states(t: Time, cin: Time, cout: Time, cin_interval: int, cout_interval: int):
    is_cin = (cin.in_minutes() - cin_interval) <= t.in_minutes() <= (cin.in_minutes() + cin_interval)
    is_cout = (cout.in_minutes() - cout_interval) <= t.in_minutes() <= (cout.in_minutes() + cout_interval)
    
    return is_cin, is_cout

def process_from_data(data, data_class_mapping: dict[str, type] | None = None, class_mapping: dict[str, type] | None = None):
    class_mapping = class_mapping if class_mapping is not None else {}
    data_class_mapping = data_class_mapping if data_class_mapping is not None else {}
    
    if isinstance(data, dict):
        return_value = {key: process_from_data(value, data_class_mapping, class_mapping) for key, value in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return_value = data.__class__([process_from_data(value, data_class_mapping, class_mapping) for value in data])
        
        if len(data) == 2 and isinstance(data[0], str):
            if data[0].startswith("$$") and data[0].endswith("$$"):
                return_value = data_class_mapping[data[0].removeprefix("$$").removesuffix("$$")](**process_from_data(data[1], data_class_mapping, class_mapping))
            elif data[0].startswith("@@") and data[0].endswith("@@"):
                return_value = class_mapping[data[0].removeprefix("@@").removesuffix("@@")](**process_from_data(data[1], data_class_mapping, class_mapping))
    else:
        return_value = data
    
    return return_value


def create_widget(parent_layout: QLayout | None, layout_type: type[QHBoxLayout] | type[QVBoxLayout] | type[QGridLayout]):
    widget = QWidget()
    layout = layout_type()
    widget.setLayout(layout)
    
    if parent_layout is not None:
        parent_layout.addWidget(widget)
    
    return widget, layout

def create_scrollable_widget(parent_layout: QLayout | None, layout_type: type[QHBoxLayout] | type[QVBoxLayout], borderless=True):
    scroll_widget = QScrollArea()
    scroll_widget.setWidgetResizable(True)
    scroll_widget.setStyleSheet("QScrollArea{border: none}")
    
    widget = QWidget()
    scroll_widget.setWidget(widget)
    layout = layout_type(widget)
    
    if parent_layout is not None:
        parent_layout.addWidget(scroll_widget)
    
    return scroll_widget, layout

def clear_layout(layout: QLayout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()
        layout_item = item.layout()

        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()

        elif layout_item is not None:
            clear_layout(layout_item)


class Thread(QThread):
    crashed = pySignal(Exception)
    
    def __init__(self, func: Callable):
        super().__init__()
        self.func = func
    
    def run(self):
        try:
            self.func()
        except Exception as e:
            self.crashed.emit(e)
            self.exit(-1)

