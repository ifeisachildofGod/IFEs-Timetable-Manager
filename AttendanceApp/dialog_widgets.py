from widgets import BaseWidget, BaseDialogWidget

from .base_widgets import *
from .theme import AttendanceThemeManager


class CommSetupDialog(BaseDialogWidget):
    update_signal = pySignal(dict, list)
    bluetooth_state_signal = pySignal(bool)
    
    def __init__(self, parent, connector: BaseCommSystem):
        super().__init__("Device Connection Configuration", BaseWidget, parent=parent)
        
        self.THEME_MANAGER = AttendanceThemeManager()
        self.THEME_MANAGER.set_widget(self)
        self.THEME_MANAGER.apply_theme("dark-blue")
        
        self.setModal(True)
        self.setFixedSize(700, 500)
        self.setContentsMargins(10, 10, 10, 10)
        
        self.connector = connector
        
        self.connected = False
        self.connect_clicked = False
        self.connect_only_widgets = []
        self.data: dict[str, str | int | Literal["bt", "ser"]] = {}
        
        serial_widget, serial_layout = create_widget(None, QVBoxLayout)
        serial_widget.setProperty("class", "labeled-widget")
        bluetooth_widget, bluetooth_layout = create_widget(None, QVBoxLayout)
        bluetooth_widget.setProperty("class", "labeled-widget")
        
        self.main_widget = TabViewWidget()
        self.main_widget.add("Serial Connection", serial_widget)
        self.main_widget.add("BLE Connection", bluetooth_widget)
        
        _, serial_upper_buttons_layout = create_widget(serial_layout, QHBoxLayout)
        
        def bt_state_signal():
            self.refresh("ser", self.serial_refresh_button)
            self.bluetooth_state_signal.emit(True)
        
        self.serial_refresh_button = QPushButton("Refresh")
        self.serial_refresh_button.clicked.connect(bt_state_signal)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.serial_connect_clicked(-1))
        self.connect_only_widgets.append(connect_button)
        
        serial_upper_buttons_layout.addWidget(self.serial_refresh_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        serial_upper_buttons_layout.addWidget(connect_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        self.port_options = []
        
        serial_ports_widget, serial_ports_layout = create_widget(None, QHBoxLayout)
        serial_layout.addWidget(serial_ports_widget)
        
        self.port_selector_widget = QComboBox()
        self.port_selector_widget.addItems(self.port_options)
        
        serial_ports_layout.addWidget(QLabel("Ports"))
        serial_ports_layout.addWidget(self.port_selector_widget)
        
        baud_rate_options = ["300", "1200", "2400", "4800", "9600", "19200",
                             "38400", "57600", "74880", "115200", "230400",
                             "250000", "500000", "1000000", "2000000"]
        
        serial_baud_rate_widget, serial_baud_rate_layout = create_widget(None, QHBoxLayout)
        serial_layout.addWidget(serial_baud_rate_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.baud_rate_selector_widget = QComboBox()
        self.baud_rate_selector_widget.addItems(baud_rate_options)
        self.baud_rate_selector_widget.setCurrentIndex(baud_rate_options.index("9600"))
        
        serial_baud_rate_layout.addWidget(QLabel("Baud rate"))
        serial_baud_rate_layout.addWidget(self.baud_rate_selector_widget)
        
        self.bluetooth_refesh_button = QPushButton("Refresh")
        self.bluetooth_refesh_button.clicked.connect(lambda: self.refresh("bt", self.bluetooth_refesh_button))
        
        bluetooth_layout.addWidget(self.bluetooth_refesh_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.bluetooth_devices = []
        
        bluetooth_devices_widget, self.bluetooth_devices_layout = create_scrollable_widget(None, QVBoxLayout)
        
        bt_port_edit_widget, bt_port_edit_layout = create_widget(bluetooth_layout, QHBoxLayout)
        
        self.connect_only_widgets.append(bt_port_edit_widget)
        
        for index, (addr, name) in enumerate(self.bluetooth_devices):
            self.add_bt_device(name, addr, index)
        
        self.bt_port_edit = QLineEdit()
        self.bt_port_edit.setValidator(QIntValidator())
        
        bt_port_edit_layout.addWidget(QLabel("Port"))
        bt_port_edit_layout.addWidget(self.bt_port_edit)
        
        bluetooth_layout.addWidget(LabeledField("Bluetooth Low Energy Devices", bluetooth_devices_widget, height_policy=QSizePolicy.Policy.Minimum))
        bluetooth_layout.addWidget(bt_port_edit_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        self.addWidget(self.main_widget)
        
        self.disconnect_button = QPushButton("Disconnect")
        
        self.addWidget(self.disconnect_button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        
        def bt_state_signal_func(value):
            bluetooth_widget.setDisabled(not value)
            self.bluetooth_refesh_button.setDisabled(False)
        
        self.update_signal.connect(self._update_scan_timeout)
        self.bluetooth_state_signal.connect(bt_state_signal_func)
        
        self.refresh_tracker = {}
    
    def comm_disconnect(self):
        self.data = {}
        self.connected = False
        
        for widget in self.connect_only_widgets:
            widget.setDisabled(False)
        
        self.disconnect_button.setDisabled(True)
    
    def refresh(self, refresh_type: str, refresh_button: QPushButton):
        if self.refresh_tracker.get(refresh_type, [True, None])[0]:
            if not self.refresh_tracker.get(refresh_type, False):
                self.refresh_tracker[refresh_type] = [False, None]
            
            self.refresh_tracker[refresh_type][0] = False
            refresh_button.setDisabled(True)
            
            self.refresh_tracker[refresh_type][1] = Thread(lambda: self.update_scans(refresh_type, refresh_type, refresh_button))
            self.refresh_tracker[refresh_type][1].crashed.connect(self.parent().connection_error_func)
            self.refresh_tracker[refresh_type][1].start()
    
    def exec(self):
        self.serial_refresh_button.click()
        self.bluetooth_refesh_button.click()
        
        initial_exec_val = super().exec()
        
        if not self.connector.connected:
            self.connector.device.port = self.data.get("port", "")
            self.connector.device.addr = self.data.get("addr")
            self.connector.device.baud_rate = self.data.get("baud_rate")
            self.connector.device.pswd = self.data.get("key")
            
            if self.data.get("connection-type", None) is not None:
                self.connector.set_bluetooth(self.data["connection-type"] == "bt")
                self.connector.set_serial(self.data["connection-type"] == "ser")
                
                self.connector.start_connection()
        
        return initial_exec_val
    
    def _update_scan_timeout(self, data: dict[str, list[tuple[str, str]] | list[str]], args: list):
        if not args:
            refresh_type = None
            refresh_button = None
        else:
            refresh_type, refresh_button = args
        
        if data.get("ser", None) is not None and self.port_options != data["ser"]:
            self.port_options = data["ser"]
            
            for _ in range(self.port_selector_widget.count()):
                self.port_selector_widget.removeItem(0)
            
            if self.port_selector_widget.currentText() in self.port_options:
                self.port_options.insert(0, self.port_options.pop(self.port_options.index(self.port_selector_widget.currentText())))
            
            self.port_selector_widget.addItems(self.port_options)
            if self.port_options:
                self.port_selector_widget.setCurrentIndex(0)
        
        if data.get("bt", None) is not None and dict(self.bluetooth_devices) != dict(data["bt"]):
            for _ in range(len(self.bluetooth_devices)):
                prev_widget = self.bluetooth_devices_layout.itemAt(0).widget()
                self.bluetooth_devices_layout.removeWidget(prev_widget)
                prev_widget.deleteLater()
                
                for widget in self.connect_only_widgets[2:]:
                    widget.deleteLater()
                
                self.connect_only_widgets[2:] = []
            
            self.bluetooth_devices = data["bt"]
            
            for index, (addr, name) in enumerate(self.bluetooth_devices):
                self.add_bt_device(name, addr, index)
        
        if refresh_button is not None:
            refresh_button.setDisabled(False)
        if refresh_type is not None:
            self.refresh_tracker[refresh_type][0] = True
    
    def update_scans(self, send_type: str | None = None, *args):
        data = {}
        
        if send_type == "bt" or send_type is None:
            bt_data = self.connector.find_devices("bt")
            data["bt"] = bt_data
        elif send_type == "ser" or send_type is None:
            ser_data = self.connector.find_devices("ser")
            data["ser"] = ser_data
        
        self.update_signal.emit(data, args)
    
    def add_bt_device(self, name: str, addr: str, index: int):
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.serial_connect_clicked(index))
        self.connect_only_widgets.append(connect_button)
        
        _, bt_device_layout = create_widget(self.bluetooth_devices_layout, QHBoxLayout)
            
        _, info_layout = create_widget(bt_device_layout, QVBoxLayout)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 30px; font-weight: 900;")
        addr_label = QLabel(addr)
        addr_label.setStyleSheet("font-size: 20px; font-weight: 100;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(addr_label)
        
        bt_device_layout.addWidget(connect_button, alignment=Qt.AlignmentFlag.AlignRight)
    
    def serial_connect_clicked(self, a0: int):
        def func():
            self.connect_clicked = True
            self.connected = True
            
            self.data["key"] = "83ab579eee7f8a98c765"
            
            if a0 == -1:
                self.data["connection-type"] = "ser"
                self.data["port"] = self.port_selector_widget.currentText()
                self.data["baud_rate"] = int(self.baud_rate_selector_widget.currentText())
            elif isinstance(a0, int) and a0 >= 0:
                self.data["connection-type"] = "bt"
                self.data["addr"] = self.bluetooth_devices[a0][0]
                try:
                    self.data["port"] = int(self.bt_port_edit.text())
                except ValueError:
                    self.connector.error_func(ValueError(f'Invalid port value: "{self.bt_port_edit.text()}"'), False)
                    return
            
            self.close()
        
        return func
    
    def closeEvent(self, a0):
        if self.connect_clicked:
            self.connect_clicked = False
            
            response = QMessageBox.question(self, "Connection mode", "Are you want to continue with these settings",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if response == QMessageBox.StandardButton.Yes:
                a0.accept()
                
                for widget in self.connect_only_widgets:
                    widget.setDisabled(True)
                self.disconnect_button.setDisabled(False)
            else:
                self.comm_disconnect()
                
                a0.ignore()
                
                return
            
        return super().closeEvent(a0)


# class ManageSetupDialog(BaseDialogWidget):
#     def __init__(self):
#         super().__init__("Management Mode")
        
#         sch_att_rb = QCheckBox("School Attendance")
#         t_reg_rb = QCheckBox("Teacher Registry")
        
#         self.addStretch()
#         self.addWidget(sch_att_rb, alignment=Qt.AlignmentFlag.AlignCenter)
#         self.addWidget(t_reg_rb, alignment=Qt.AlignmentFlag.AlignCenter)
#         self.addStretch()

