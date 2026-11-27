
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

