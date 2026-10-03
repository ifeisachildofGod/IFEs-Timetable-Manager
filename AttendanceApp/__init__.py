
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
        
        self.target_connector = BaseCommSystem(CommDevice(self.comm_signal, self.connection_changed, "", None, None), self.connection_error_func)
        self.connection_set_up_screen = CommSetupDialog(self, self.target_connector)
        # self.management_set_up_screen = ManageSetupDialog(self)
        
        self.THEME_MANAGER = AttendanceThemeManager()
        self.THEME_MANAGER.set_widget(self)
        self.THEME_MANAGER.apply_theme("dark-blue")
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        card_scan_widget = CardScanScreenWidget(self.target_connector, self)
        staff_data_widget = StaffDataWidget(self)
        
        self.attendance_chart_widget = AttendanceBarWidget(staff_data_widget)
        self.punctuality_graph_widget = PunctualityGraphWidget(staff_data_widget)
        self.attendance_widget = AttendanceWidget(self, self.attendance_chart_widget, self.punctuality_graph_widget, self.target_connector, card_scan_widget)
        self.staff_list_widget = StaffListWidget(self, self.target_connector, card_scan_widget, staff_data_widget, self.attendance_widget)
        
        def _changed_to_staff_list_widget_func(_):
            self._set_search_state("Attendance Data")
            self.attendance_widget.update_tooltip()
        
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
        
        self.add("Attendance", self.attendance_widget, _changed_to_staff_list_widget_func)
        self.add("Staff", self.staff_list_widget, lambda _: self._set_search_state("Staff"))
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
        self.target_connector.device.connection_changed.connect(conn_changed)
        self.target_connector.device.connection_changed.emit(False)
    
    def update_staff_list_staff_name(self, staffID: ID):
        for staff_widget_dict in self.staff_list_widget.all_staff_widgets.values():
            if staffID in staff_widget_dict:
                staff_widget_dict[staffID].update_name()
    
    def update_staff_list_subject_name(self, subject: Subject):
        for teacher in SCHOOL.teachers.values():
            if subject.id in teacher.subjects:
                for teacher_widget_dict in self.staff_list_widget.all_staff_widgets.values():
                    if teacher.id in teacher_widget_dict:
                        teacher_widget_dict[teacher.id].update_subject_name(subject)
    
    def update_staff_list_class_name(self, cls: Class):
        for subject in cls.subjects.values():
            if isinstance(subject, Subject):
                subjects = [subject]
            elif isinstance(subject, CombinedSubject):
                subjects = subject.subjects
            
            for subj in subjects:
                if subj.teacher:
                    for teacher_filtered_dict in self.staff_list_widget.all_staff_widgets.values():
                        if subj.teacher.id in teacher_filtered_dict:
                            teacher_filtered_dict[subj.teacher.id].update_class_name(cls)
    
    def disconnect_connection(self):
        self.target_connector.stop_connection()
        self.connection_set_up_screen.comm_disconnect()
    
    # def comm_send_screen_changed(self, message: str):
    #     def scr_changed(_):
    #         if self.target_connector.connected:
    #             pass
    #             # self.target_connector.send_message(message)
        
    #     return scr_changed
    
    def activate_connection_screen(self):
        self.connection_set_up_screen.exec()
    
    # def activate_management_screen(self):
    #     self.management_set_up_screen.exec()
    
    def connection_error_func(self, e: Exception, conn_error: bool = True):
        self.target_connector.stop_connection()
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


