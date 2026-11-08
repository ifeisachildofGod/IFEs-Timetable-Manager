
from .dialog_widgets import *
from .staff.option_widgets import *
from .staff.list_widgets import *

from .theme import AttendanceThemeManager


class AttendanceManager(TabViewWidget):
    comm_signal = pySignal(dict)
    connection_changed = pySignal(bool)
    saved_state_changed = pySignal(bool)
    search_state_changed = pySignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        
        self.search_state = True
        
        self.comm_system = BaseCommSystem(CommDevice(self.comm_signal, self.connection_changed, "", None, None), self.connection_error_func)
        self.connection_set_up_screen = CommSetupDialog(self, self.comm_system)
        # self.management_set_up_screen = ManageSetupDialog(self)
        
        self.THEME_MANAGER = AttendanceThemeManager()
        self.THEME_MANAGER.set_widget(self)
        self.THEME_MANAGER.apply_theme("dark-blue")
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        card_scan_widget = CardScanScreenWidget(self.comm_system, self)
        staff_data_widget = StaffDataWidget(self)
        
        self.attendance_chart_widget = AttendanceBarWidget(staff_data_widget)
        self.punctuality_graph_widget = PunctualityGraphWidget(staff_data_widget)
        self.attendance_widget = AttendanceWidget(self, self.attendance_chart_widget, self.punctuality_graph_widget, self.comm_system, card_scan_widget)
        
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
        self.stack.addWidget(card_scan_widget)
        self.stack.addWidget(staff_data_widget)
        
        def conn_changed(connected):
            if connected:
                QMessageBox.information(None, "Connection Status", "Attendance device connected")
            else:
                self.connection_set_up_screen.comm_disconnect()
        
        self.connection_set_up_screen.disconnect_button.clicked.connect(self.disconnect_connection)
        self.comm_system.device.connection_changed.connect(conn_changed)
        self.comm_system.device.connection_changed.emit(False)
    
    def disconnect_connection(self):
        self.comm_system.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
    
    # def comm_send_screen_changed(self, message: str):
    #     def scr_changed(_):
    #         if self.comm_system.connected:
    #             pass
    #             # self.comm_system.send_message(message)
        
    #     return scr_changed
    
    def activate_connection_screen(self):
        self.connection_set_up_screen.exec()
    
    # def activate_management_screen(self):
    #     self.management_set_up_screen.exec()
    
    def connection_error_func(self, e: Exception, conn_error: bool = True):
        self.comm_system.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
        
        if conn_error:
            response = QMessageBox.warning(None, type(e).__name__, str(e) + "\n\nTry again?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            response = QMessageBox.warning(None, type(e).__name__, str(e))
        
        if isinstance(e, OSError):
            self.connection_set_up_screen.bluetooth_state_signal.emit(False)
        
        if not self.connection_set_up_screen.isActiveWindow() and response == QMessageBox.StandardButton.Yes:
            self.activate_connection_screen()
    
    def _set_search_state(self, state: str):
        self.search_state = state
        self.search_state_changed.emit(state)


