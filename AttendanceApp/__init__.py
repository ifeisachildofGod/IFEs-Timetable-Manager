
from communication import *

from .main import *
from .theme import AttendanceThemeManager


class AttendanceManager(TabViewWidget):
    comm_signal = pySignal(dict)
    connection_changed = pySignal(bool)
    saved_state_changed = pySignal(bool)
    search_state_changed = pySignal(str)
    
    def __init__(self, parent: QMainWindow) -> None:
        super().__init__()
        
        self._parent = parent
        
        self.search_state = True
        
        self.THEME_MANAGER = AttendanceThemeManager()
        self.THEME_MANAGER.set_widget(self)
        self.THEME_MANAGER.apply_theme("dark-blue")
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.attendance_chart_widget = AttendanceBarWidget(self._parent)
        self.punctuality_graph_widget = PunctualityGraphWidget()
        self.attendance_widget = AttendanceWidget(self, self.attendance_chart_widget, self.punctuality_graph_widget, self._parent.comm_system)
        
        def _changed_to_attendance_graph_widget(_, from_main_page: bool = False):
            self._set_search_state("")
            
            if from_main_page:
                self.attendance_chart_widget.prefect_data_changed()
                self.attendance_chart_widget.teacher_data_changed()
        
        def _changed_to_punctuality_chart_widget(_, from_main_page: bool = False):
            self._set_search_state("")
            
            if from_main_page:
                self.punctuality_graph_widget.prefect_data_changed()
                self.punctuality_graph_widget.teacher_data_changed()
        
        self.add("Attendance", self.attendance_widget, lambda _: self._set_search_state("Attendance Data"))
        self.add("Attendance Chart", self.attendance_chart_widget, _changed_to_attendance_graph_widget)
        self.add("Punctuality Graph", self.punctuality_graph_widget, _changed_to_punctuality_chart_widget)
    
    def _set_search_state(self, state: str):
        self.search_state = state
        self.search_state_changed.emit(state)


