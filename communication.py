
import serial, requests, websockets
import queue
import threading

from bleak import BleakScanner, BleakClient
from serial.tools.list_ports import comports

from imports import *
from utils import *
from core import *
from widgets.base import *
from widgets.user_interface import *


_T = TypeVar("_T")


"Name:Variable-Type(Data)|...|..."


SERVER_URL = "http://127.0.0.1:8000"
WEB_SOCKET_URI = "ws://127.0.0.1:8000/ws"

TIMEOUT = 15


import asyncio
from bleak import BleakScanner

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class PasswordException(Exception):
    pass

class ServerException(Exception):
    pass


class BLEDiscoveryWorker(QObject):
    devices_discovered = pyqtSignal(list)
    error_occurred = pyqtSignal(Exception)
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.loop = None
        self.scan_task = None
        self._cancel_requested = threading.Event()
    @pyqtSlot()
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            if self._cancel_requested.is_set():
                return
            self.scan_task = self.loop.create_task(BleakScanner.discover(timeout=5))
            devices = self.loop.run_until_complete(self.scan_task)
            if not self._cancel_requested.is_set():
                self.devices_discovered.emit([
                    (device.address, device.name or "Unknown device")
                    for device in devices
                ])
        except asyncio.CancelledError:
            pass
        except Exception as error:
            if not self._cancel_requested.is_set():
                self.error_occurred.emit(error)
        finally:
            if self.loop is not None and not self.loop.is_closed():
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                self.loop.close()
            self.loop = None
            self.scan_task = None
            self.finished.emit()
    def cancel(self):
        self._cancel_requested.set()
        loop, task = self.loop, self.scan_task
        if loop is not None and task is not None and not loop.is_closed() and not task.done():
            loop.call_soon_threadsafe(task.cancel)

class API_Key(str):
    pass

class EnvironVariableName(str):
    pass


@dataclass
class CommDevice:
    parent: "BaseCommSystem"
    connection_changed: pyBoundSignal[bool]
    direct_msg_signal: pyBoundSignal[str]
    is_connected: bool
    is_connecting: bool

    def __init__(self, /, **kwds):
        # Kept for direct construction. Dataclass subclasses call __post_init__.
        self.__dict__.update(kwds)
        self.__post_init__()
    
    def __post_init__(self):
        self.msg_buffer = queue.Queue()
        self.data_points: list[tuple[str | list[str], pyBoundSignal]] = []
        self.connection_thread = None
        self._stop_event = threading.Event()
        self._data_lock = threading.RLock()
        self.connection_changed.connect(self._connection_state_changed)
    
    def _connection_state_changed(self, connected=False):
        self.is_connecting = False

    def _process_data(self, data: str):
        processed_data = {}
        for item in filter(None, (part.strip() for part in data.split("|"))):
            if ":" not in item:
                raise ValueError(f"Malformed data field: {item!r}")
            name, value = item.split(":", 1)
            name = name.strip()
            if not name:
                raise ValueError("Received a data field with an empty name")
            processed_data[name] = self._process_sub_data(value)
        return processed_data

    def _process_sub_data(self, data: str, numbers: bool = False):
        data = data.strip()
        if numbers:
            return float(data)
        if len(data) < 3 or "(" not in data or not data.endswith(")"):
            raise ValueError(f"Malformed typed value: {data!r}")
        var_type, value = data.split("(", 1)
        value = value[:-1]
        if var_type == "s":
            return value
        if var_type == "n":
            return float(value)
        if var_type == "l":
            if not value.strip():
                return []
            return [float(part.strip()) for part in value.split(",")]
        raise ValueError(f"Type ({var_type}) is not valid")
    
    def _crashed(self, error):
        self.is_connected = False
        self.is_connecting = False
        self.connection_changed.emit(False)
        try:
            self.parent.error_func(error)
        except Exception:
            traceback.print_exc()
    
    def get_options(self):
        raise NotImplementedError()
    
    def exec_data_point(self, all_data: dict[str, Any]):
        for key, value in all_data.items():
            for registered_key, signal in self.data_points:
                if isinstance(registered_key, str):
                    if key == registered_key:
                        signal.emit(value)
                elif key in registered_key:
                    # A multi-key data point is emitted only when all its values
                    # arrive in the same received message.
                    pass
        for registered_key, signal in self.data_points:
            if isinstance(registered_key, list) and all(k in all_data for k in registered_key):
                signal.emit([all_data[k] for k in registered_key])
    
    def init_process_data(self, data: bytes):
        return data.decode("utf-8", errors="replace").strip().removesuffix("|").strip()
    
    def data_process(self, msg_recv: str):
        full_data = self._process_data(msg_recv)
        self.exec_data_point(full_data)
        # This signal is declared as pySignal(str), so emit the original payload.
        self.direct_msg_signal.emit(msg_recv)
    
    def send_message(self, msg: str):
        if self.is_connected and isinstance(msg, str):
            self.msg_buffer.put(msg)
    
    def set_data_point(self, key: int | str | list[str], signal: pyBoundSignal):
        if isinstance(key, str):
            self.data_points.append((key, signal))
        elif isinstance(key, (list, set, tuple)):
            self.data_points.append((list(key), signal))
        else:
            raise TypeError(f"Bad key type: {type(key)}")
    
    def should_stop(self):
        thread = QThread.currentThread()
        return self._stop_event.is_set() or (thread is not None and thread.isInterruptionRequested())
    
    def start_connection(self):
        if self.is_connected or self.is_connecting:
            return
        if self.connection_thread is not None and self.connection_thread.isRunning():
            return
        self._stop_event.clear()
        self.is_connecting = True
        self.connection_thread = Thread(self.update)
        self.connection_thread.crashed.connect(self._crashed)
        self.connection_thread.finished.connect(self._thread_finished)
        self.connection_thread.start()
    
    def _thread_finished(self):
        self.is_connecting = False
        if not self.is_connected:
            self.connection_changed.emit(False)
    
    def stop_connection(self):
        self._stop_event.set()
        self.is_connected = False
        thread = self.connection_thread
        if thread is not None and thread.isRunning():
            thread.requestInterruption()
            thread.quit()
        self.connection_changed.emit(False)
    
    def _set_connected(self, connected: bool):
        self.is_connected = connected
        self.connection_changed.emit(connected)
    
    def update(self):
        raise NotImplementedError()

@dataclass
class CommDevices:
    serial_port_devices: list[SerialPortDevice]
    ble_devices: list[BLE_Device]
    server_devices: list[ServerDevice]

    def all(self):
        return self.serial_port_devices + self.ble_devices + self.server_devices

class BaseCommSystem:
    def __init__(self, window: QMainWindow, devices: CommDevices, error_func: Callable[[Exception], None]):
        self.window = window

        self.devices = devices


        self.error_func = error_func
    
    def set_data_point(self, key: int | str | list[str], signal: pyBoundSignal):
        for device in self.devices.all():
            device.set_data_point(key, signal)
    
    def send_message(self, msg: str):
        for device in self.devices.all():
            device.send_message(msg)

class CommSetupDialog(BaseDialogWidget):
    def __init__(self, parent, comm_system: BaseCommSystem):
        super().__init__("Device Connection Configuration", BaseWidget, parent=parent)

        self.setModal(True)
        self.setFixedSize(700, 500)
        self.setContentsMargins(10, 10, 10, 10)

        self.comm_system = comm_system


        self.main_widget = TabViewWidget()

        self.ble_devices_widget = BLE_DevicesWidget(self.comm_system.devices.ble_devices, self)

        self.main_widget.add("Serial Connection", SerialPort_DevicesWidget(self.comm_system.devices.serial_port_devices, self))
        self.main_widget.add("BLE Connection", self.ble_devices_widget)
        self.main_widget.add("API Connection", Server_DevicesWidget(self.comm_system.devices.server_devices, self))

        self.addWidget(self.main_widget)
    
    def closeEvent(self, event):
        if self.ble_devices_widget.shutdown():
            event.accept()
            return
        event.ignore()
        thread = self.ble_devices_widget.discovery_thread
        if thread is not None:
            try:
                thread.finished.disconnect(self._close_after_discovery)
            except (TypeError, RuntimeError):
                pass
            thread.finished.connect(self._close_after_discovery)
    
    def _close_after_discovery(self):
        QTimer.singleShot(0, self.close)

class DeviceWidget[_T](BaseWidget):
    def __init__(self, device: _T, parent: CommSetupDialog, layout_type=None):
        super().__init__(layout_type)

        self.setProperty("class", "SpecialBG1 BorderRadiused")
        self.setSpacing(10)

        self.device = device

        self._parent = parent


        def conn_clicked():
            self.connect_button.setDisabled(True)
            self.device.start_connection()

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(conn_clicked)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.device.stop_connection)
        self.disconnect_button.setDisabled(True)

        self.device.connection_changed.connect(self._connection_changed)

    def _connection_changed(self, connected: bool):
        raise NotImplementedError()

class DevicesWidget[_T](BaseWidget):
    connection_changed = pySignal(bool)
    direct_msg_signal = pySignal(str)

    def __init__(self, devices: list[_T], parent: CommSetupDialog):
        super().__init__()

        self._parent = parent


        self.devices = devices

        self.device_widgets: list[DeviceWidget[_T]] = []

        self.main_widget = BaseScrollWidget()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(lambda: self.add_device(self.new_device()))

        self.main_widget.addStretch()

        self.addWidget(self.main_widget)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _make_cancel_func(self, device_widget: DeviceWidget[_T]):
        def func():
            device_widget.device.stop_connection()
            if device_widget in self.device_widgets:
                self.device_widgets.remove(device_widget)
            if device_widget.device in self.devices:
                self.devices.remove(device_widget.device)
            self.main_widget.removeWidget(device_widget)
            device_widget.deleteLater()

        return func

    def new_device(self) -> _T:
        raise NotImplementedError()

    def new_device_widget(self, device: _T) -> DeviceWidget[_T]:
        raise NotImplementedError()

    def add_device(self, device: _T):
        device_widget = self.new_device_widget(device)

        cancel_button = BaseWidget()
        cancel_button.setFixedSize(40, 40)
        cancel_button.setContentsMargins(0, 0, 0, 0)
        cancel_button.enableCursorPointing()
        cancel_button.setProperty("class", "CancelButton NoBG SpecialBG1Hover BorderRadiused")
        cancel_button.setStyleProperty("border-radius", "20px")
        cancel_button.clicked.connect(self._make_cancel_func(device_widget))
        cancel_button.addWidget(QLabel("<span style='font-size: 30px; font-weight: bold;'>×</span>"), alignment=Qt.AlignmentFlag.AlignCenter)

        device_widget.insertWidget(0, cancel_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.devices.append(device)
        self.device_widgets.append(device_widget)

        self.main_widget.insertWidget(len(self.main_widget.getChildren()), device_widget)


@dataclass
class SerialPortDevice(CommDevice):
    port: Optional[str]
    baud_rate: int
    pswd: Optional[str]
    
    @staticmethod
    def get_options():
        return [port.name for port in comports()]
    
    def update(self):
        if not self.port:
            raise ConnectionError("Select a serial port before connecting")
        serial_target = None
        try:
            serial_target = serial.Serial(self.port, self.baud_rate, timeout=0.5, write_timeout=2)
            # Give the microcontroller time to reset after opening its serial port.
            for _ in range(20):
                if self.should_stop():
                    return
                time.sleep(0.1)
            password = self.pswd or ""
            authenticated = False
            for _ in range(TIMEOUT):
                if self.should_stop():
                    return
                serial_target.write((password + "\n").encode())
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline and not self.should_stop():
                    if serial_target.in_waiting:
                        response = serial_target.readline().decode(errors="replace").strip()
                        if response == password:
                            authenticated = True
                            break
                    time.sleep(0.05)
                if authenticated:
                    break
            if not authenticated:
                raise PasswordException("Password authentication failed. Check the device password and serial protocol.")
            self._set_connected(True)
            while not self.should_stop():
                try:
                    message = self.msg_buffer.get_nowait()
                except queue.Empty:
                    message = None
                if message is not None:
                    serial_target.write((message + "\n").encode())
                if serial_target.in_waiting:
                    received = self.init_process_data(serial_target.readline())
                    if received:
                        self.data_process(received)
                else:
                    time.sleep(0.02)
        finally:
            self.is_connected = False
            if serial_target is not None:
                try:
                    if serial_target.is_open:
                        serial_target.close()
                except Exception:
                    traceback.print_exc()
            self.connection_changed.emit(False)

@dataclass
class BLE_Device(CommDevice):
    port: str
    name: str
    addr: str
    pswd: Optional[str]
    
    def update(self):
        async def run_ble():
            async with BleakClient(self.addr, timeout=15) as client:
                services = await client.get_services()
                writable = None
                readable = None
                notifiable = None
                for service in services:
                    for characteristic in service.characteristics:
                        props = set(characteristic.properties)
                        if writable is None and ({"write", "write-without-response"} & props):
                            writable = characteristic.uuid
                        if readable is None and "read" in props:
                            readable = characteristic.uuid
                        if notifiable is None and "notify" in props:
                            notifiable = characteristic.uuid
                if writable is None:
                    raise ConnectionError("The BLE device has no writable GATT characteristic")
                if readable is None and notifiable is None:
                    raise ConnectionError("The BLE device needs a readable or notify GATT characteristic for password authentication and incoming data")
                incoming = asyncio.Queue()
                notification_started = False
                if notifiable is not None:
                    def notification_handler(_sender, data):
                        incoming.put_nowait(bytes(data))
                    await client.start_notify(notifiable, notification_handler)
                    notification_started = True

                async def receive(timeout=1.0):
                    if readable is not None:
                        try:
                            return bytes(await asyncio.wait_for(client.read_gatt_char(readable), timeout=timeout))
                        except asyncio.TimeoutError:
                            return b""
                    try:
                        return await asyncio.wait_for(incoming.get(), timeout=timeout)
                    except asyncio.TimeoutError:
                        return b""
                try:
                    password = self.pswd or ""
                    authenticated = False
                    for _ in range(TIMEOUT):
                        if self.should_stop():
                            return
                        await client.write_gatt_char(writable, (password + "\n").encode())
                        response = (await receive(1.0)).decode(errors="replace").strip()
                        if response == password:
                            authenticated = True
                            break
                    if not authenticated:
                        raise PasswordException("BLE password authentication failed. Check the password and the device's GATT protocol.")
                    self._set_connected(True)
                    while not self.should_stop() and client.is_connected:
                        try:
                            message = self.msg_buffer.get_nowait()
                        except queue.Empty:
                            message = None
                        if message is not None:
                            await client.write_gatt_char(writable, message.encode())
                        data = await receive(0.5)
                        if data:
                            decoded = self.init_process_data(data)
                            if decoded:
                                self.data_process(decoded)
                finally:
                    if notification_started:
                        try:
                            await client.stop_notify(notifiable)
                        except Exception:
                            pass
        try:
            asyncio.run(run_ble())
        finally:
            self.is_connected = False
            self.connection_changed.emit(False)

@dataclass
class ServerDevice(CommDevice):
    server_url: str
    web_sock_uri: str
    api_key: Optional[API_Key | EnvironVariableName]
    @staticmethod
    def get_options():
        return [(SERVER_URL, WEB_SOCKET_URI)]
    
    def update(self):
        if self.api_key is None:
            raise PasswordException("No API key found. Set an API key in the connection settings or provide an environment-variable name.")
        api_key = str(self.api_key) if isinstance(self.api_key, API_Key) else os.environ.get(str(self.api_key))
        if not api_key:
            raise PasswordException("The configured API key is empty or the environment variable is not set")
        async def run_server():
            async def receive_updates():
                # websockets >= 14 uses additional_headers; older versions used extra_headers.
                try:
                    connection = websockets.connect(self.web_sock_uri, additional_headers={"X-API-Key": api_key}, open_timeout=10, close_timeout=2)
                except TypeError:
                    connection = websockets.connect(self.web_sock_uri, extra_headers={"X-API-Key": api_key}, open_timeout=10, close_timeout=2)
                async with connection as websocket:
                    self._set_connected(True)
                    while not self.should_stop():
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        except asyncio.TimeoutError:
                            continue
                        event = json.loads(message)
                        if not isinstance(event, dict) or "id" not in event or "data" not in event:
                            raise ServerException(f"Invalid WebSocket event: {event!r}")
                        self.exec_data_point({str(event["id"]): event["data"]})
            async def send_updates():
                while not self.should_stop():
                    try:
                        message = self.msg_buffer.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                        continue
                    try:
                        response = await asyncio.to_thread(
                            requests.post,
                            f"{self.server_url.rstrip('/')}/attendance",
                            headers={"X-API-Key": api_key},
                            json=message,
                            timeout=TIMEOUT,
                        )
                        if not response.ok:
                            raise ServerException(f"Server returned HTTP {response.status_code}: {response.text[:500]}")
                    except Exception:
                        self.msg_buffer.put(message)
                        raise

            receive_task = asyncio.create_task(receive_updates())
            send_task = asyncio.create_task(send_updates())
            try:
                done, pending = await asyncio.wait(
                    {receive_task, send_task}, return_when=asyncio.FIRST_EXCEPTION
                )
                for task in done:
                    error = task.exception()
                    if error is not None:
                        raise error
                if self.should_stop():
                    return
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
            finally:
                for task in (receive_task, send_task):
                    if not task.done():
                        task.cancel()
                await asyncio.gather(receive_task, send_task, return_exceptions=True)
        try:
            asyncio.run(run_server())
        finally:
            self.is_connected = False
            self.connection_changed.emit(False)


class SerialPortDeviceWidget(DeviceWidget[SerialPortDevice]):
    def __init__(self, device: SerialPortDevice, parent: CommSetupDialog):
        super().__init__(device, parent)

        self.main_widget = BaseWidget()
        self.main_widget.setProperty("class", "NoBackground")

        bottom_widget = BaseWidget(QHBoxLayout)
        bottom_widget.setProperty("class", "NoBackground")

        # ---------------------------------------------------------------------------------------------------------------------------------------------------

        self.port_cb = QComboBox()
        self.port_cb.currentTextChanged.connect(self._com_port_changed)

        self.baud_rate_selector_widget = QComboBox()
        self.baud_rate_selector_widget.addItems(
            [
                "300", "1200", "2400", "4800", "9600", "19200",
                "38400", "57600", "74880", "115200", "230400",
                "250000", "500000", "1000000", "2000000"
            ]
        )
        self.baud_rate_selector_widget.currentTextChanged.connect(self._baud_rate_changed)
        self.baud_rate_selector_widget.setCurrentText(str(self.device.baud_rate))

        self.main_widget.addWidget(p_lw := LabeledWidget("Ports", self.port_cb)) ; p_lw.setProperty("class", "NoBackground")
        self.main_widget.addWidget(br_lw := LabeledWidget("Baud rate", self.baud_rate_selector_widget)) ; br_lw.setProperty("class", "NoBackground")

        # ---------------------------------------------------------------------------------------------------------------------------------------------------

        self.psword_edit = QLineEdit()
        self.psword_edit.setText(self.device.pswd or "")
        self.psword_edit.textChanged.connect(self._pswd_edited)
        self.psword_edit.setPlaceholderText("Password")
        self.psword_edit.setEchoMode(QLineEdit.EchoMode.Password)

        bottom_widget.addWidget(self.connect_button)
        bottom_widget.addStretch()
        bottom_widget.addWidget(self.psword_edit)
        bottom_widget.addStretch()
        bottom_widget.addWidget(self.disconnect_button)

        # ---------------------------------------------------------------------------------------------------------------------------------------------------

        self.addWidget(self.main_widget)
        self.addWidget(bottom_widget, alignment=Qt.AlignmentFlag.AlignBottom)

        self.refresh_options()

    def _pswd_edited(self, text: str):
        self.device.pswd = text.strip() or None


    def _connection_changed(self, connected: bool):
        self.main_widget.setDisabled(connected)
        self.psword_edit.setDisabled(connected)
        self.connect_button.setDisabled(connected)

        self.disconnect_button.setDisabled(not connected)

    def _com_port_changed(self, com_port: str):
        self.device.port = com_port


    def _baud_rate_changed(self, baud_rate: str):
        self.device.baud_rate = int(baud_rate)

    def refresh_options(self):
        current = self.device.port or self.port_cb.currentText()
        options = [
            port for port in self.device.get_options()
            if port not in [
                device.port
                for device in self._parent.comm_system.devices.serial_port_devices
                if device is not self.device
            ]
        ]
        if current and current not in options:
            options.insert(0, current)
        self.port_cb.blockSignals(True)
        try:
            self.port_cb.clear()
            self.port_cb.addItems(options)
            if current:
                self.port_cb.setCurrentText(current)
            elif options:
                self.port_cb.setCurrentIndex(0)
        finally:
            self.port_cb.blockSignals(False)
        self.device.port = self.port_cb.currentText() or None

class BLE_DeviceWidget(DeviceWidget[BLE_Device]):
    def __init__(self, device: BLE_Device, parent: CommSetupDialog):
        super().__init__(device, parent, QHBoxLayout)

        left = BaseWidget()
        left.setProperty("class", "NoBackground")

        info_widget = BaseWidget()
        info_widget.setProperty("class", "NoBackground")

        info_widget.addWidget(name_label := QLabel(self.device.name)) ; name_label.setStyleSheet("font-size: 30px; font-weight: 900;")
        info_widget.addWidget(addr_label := QLabel(self.device.addr)) ; addr_label.setStyleSheet("font-size: 20px; font-weight: 100;")

        bottom_widget = BaseWidget(QHBoxLayout)
        bottom_widget.setSpacing(10)
        bottom_widget.setProperty("class", "NoBackground")

        self.port_edit = QLineEdit()
        self.port_edit.textChanged.connect(self._port_changed)
        self.port_edit.setText(self.device.port)

        self.pswd_edit = QLineEdit()
        self.pswd_edit.setText(self.device.pswd or "")
        self.pswd_edit.textChanged.connect(self._pswd_edited)
        self.pswd_edit.setEchoMode(QLineEdit.EchoMode.Password)

        bottom_widget.addWidget(p_lw := LabeledWidget("Port", self.port_edit)) ; p_lw.setProperty("class", "Bordered BorderRadiused") ; p_lw.setContentsMargins(10, 10, 10, 10)
        bottom_widget.addWidget(pw_lw := LabeledWidget("Password", self.pswd_edit)) ; pw_lw.setProperty("class", "Bordered BorderRadiused") ; pw_lw.setContentsMargins(10, 10, 10, 10)

        left.addWidget(info_widget)
        left.addWidget(bottom_widget)

        # ---------------------------------------------------------------------------------------------------------------------------------------------------

        right = BaseWidget()
        right.setProperty("class", "NoBackground")

        right.addWidget(self.connect_button)
        right.addWidget(self.disconnect_button)

        # ---------------------------------------------------------------------------------------------------------------------------------------------------

        self.addWidget(left)
        self.addWidget(right)
    def _pswd_edited(self, text: str):
        self.device.pswd = text.strip() or None

    def _connection_changed(self, connected: bool):
        self.port_edit.setDisabled(connected)
        self.pswd_edit.setDisabled(connected)
        self.connect_button.setDisabled(connected)

        self.disconnect_button.setDisabled(not connected)
    def _port_changed(self, port: str):
        self.device.port = port

class Server_DeviceWidget(DeviceWidget[ServerDevice]):
    def __init__(self, device: ServerDevice, parent: CommSetupDialog):
        super().__init__(device, parent)

        self.device = device

        self._parent = parent


        self.api_key_le = QLineEdit()
        self.api_key_le.textChanged.connect(self._api_key_changed)
        self.api_key_le.setText(self.device.api_key if isinstance(self.device.api_key, API_Key) else (os.environ.get(str(self.device.api_key), "") if self.device.api_key else ""))
        self.api_key_le.setEchoMode(QLineEdit.EchoMode.Password)

        self.api_key_storage_cb = QCheckBox("Environment Variable")
        self.api_key_storage_cb.stateChanged.connect(self._api_key_storage_changed)

        self.env_var_edit = QLineEdit()
        self.env_var_edit.setPlaceholderText("Env Var Name")
        self.env_var_edit.setText(self.device.api_key if isinstance(self.device.api_key, EnvironVariableName) else "")
        self.env_var_edit.setVisible(False)
        self.env_var_edit.textChanged.connect(self._env_var_changed)

        if isinstance(self.device.api_key, EnvironVariableName):
            self.api_key_storage_cb.click()

        bottom_widget = BaseWidget(QHBoxLayout)
        bottom_widget.setProperty("class", "NoBackground")

        bottom_widget.addWidget(self.api_key_storage_cb)
        bottom_widget.addWidget(self.env_var_edit)
        bottom_widget.addStretch()
        bottom_widget.addWidget(self.connect_button)
        bottom_widget.addWidget(self.disconnect_button)

        self.addWidget(LabeledField("API Key", self.api_key_le))
        self.addWidget(bottom_widget, alignment=Qt.AlignmentFlag.AlignBottom)

    def _connection_changed(self, connected):
        self.api_key_le.setDisabled(connected)
        self.api_key_storage_cb.setDisabled(connected)
        self.env_var_edit.setDisabled(connected)
        self.connect_button.setDisabled(connected)

        self.disconnect_button.setDisabled(not connected)

    def _env_var_changed(self, text: str):
        if isinstance(self.device.api_key, EnvironVariableName):
            old_name = str(self.device.api_key)
            new_name = text.strip()
            if old_name != new_name:
                os.environ.pop(old_name, None)
        self.device.api_key = EnvironVariableName(text.strip()) if text.strip() else None


        if self.device.api_key:
            os.environ[str(self.device.api_key)] = self.api_key_le.text().strip()

    def _api_key_changed(self, text: str):
        if self.api_key_storage_cb.isChecked():
            self._env_var_changed(self.env_var_edit.text())
        else:
            self.device.api_key = API_Key(text.strip()) if text.strip() else None

    def _api_key_storage_changed(self, state: bool):
        if state:
            self._env_var_changed(self.env_var_edit.text())
        else:
            if isinstance(self.device.api_key, EnvironVariableName):
                os.environ.pop(str(self.device.api_key), None)
            value = self.api_key_le.text().strip()
            self.device.api_key = API_Key(value) if value else None


        self.env_var_edit.setVisible(state)



class SerialPort_DevicesWidget(DevicesWidget[SerialPortDevice]):
    def __init__(self, devices, parent):
        super().__init__(devices, parent)

        for device in self.devices:
            self.add_device(device)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_options)
        self.refresh_timer.start(1500)

    def refresh_options(self):
        for device_widget in self.device_widgets:
            device_widget.refresh_options()

    def new_device(self):
        options = SerialPortDevice.get_options()

        return SerialPortDevice(self._parent.comm_system, self.connection_changed, self.direct_msg_signal, False, False, options[0] if options else None, 9600, None)

    def new_device_widget(self, device):
        return SerialPortDeviceWidget(device, self._parent)

class BLE_DevicesWidget(DevicesWidget[BLE_Device]):
    def __init__(self, devices, parent):
        super().__init__(devices, parent)

        self.add_button.setVisible(False)

        self.ble_discover_timer = QTimer(self)
        self.ble_discover_timer.timeout.connect(self.refresh_options)
        self.ble_discover_timer.start(5000)

        self.discovery_thread = None

        self.discovery_worker = None


        self._closing = False


    def refresh_options(self):
        if self._closing:
            return


        if self.discovery_thread is not None:
            return


        self.discovery_thread = QThread(self)
        self.discovery_worker = BLEDiscoveryWorker()

        self.discovery_worker.moveToThread(
            self.discovery_thread

        )

        self.discovery_thread.started.connect(
            self.discovery_worker.run

        )

        self.discovery_worker.devices_discovered.connect(
            self.update_devices

        )

        self.discovery_worker.error_occurred.connect(
            self.handle_discovery_error

        )

        self.discovery_worker.finished.connect(
            self.discovery_thread.quit

        )

        self.discovery_worker.finished.connect(
            self.discovery_worker.deleteLater

        )

        self.discovery_thread.finished.connect(
            self._on_discovery_finished

        )

        self.discovery_thread.start()

    @pyqtSlot()
    def _on_discovery_finished(self):
        thread = self.discovery_thread


        self.discovery_thread = None

        self.discovery_worker = None


        if thread is not None:
            thread.deleteLater()

    @pyqtSlot(list)
    def update_devices(self, options):

        for addr, name in options:

            if not any(
                addr == d_w.device.addr

                for d_w in self.device_widgets

            ):
                self.add_device(
                    BLE_Device(
                        self._parent.comm_system,
                        self.connection_changed,
                        self.direct_msg_signal,
                        False,
                        False,
                        "",
                        name,
                        addr,
                        None

                    )
                )

        # A device missing from one scan is not necessarily gone. Keep configured
        # devices; transient radio interference must not delete their settings.

    @pyqtSlot(Exception)
    def handle_discovery_error(self, error):
        if self._closing:
            return


        QMessageBox.warning(
            self,
            type(error).__name__,
            str(error)
        )

        traceback.print_exception(error)

        self.ble_discover_timer.stop()

    def shutdown(self):
        self._closing = True


        # Stop future discovery attempts.
        self.ble_discover_timer.stop()

        # No active discovery thread.
        if self.discovery_thread is None:
            return True


        # Cancel the active BLE scan.
        if self.discovery_worker is not None:
            self.discovery_worker.cancel()

        return False


    def add_device(self, device: _T):
        device_widget = self.new_device_widget(device)

        self.devices.append(device)
        self.device_widgets.append(device_widget)

        self.main_widget.insertWidget(len(self.main_widget.getChildren()), device_widget)

    def remove_device(self, device: _T):
        self.devices.remove(device)

        device_widget = self.device_widgets.pop(next(i for i, d_w in enumerate(self.device_widgets) if device == d_w.device))
        device_widget.device.stop_connection()

        self.main_widget.removeWidget(device_widget)
        device_widget.deleteLater()

    def new_device_widget(self, device):
        return BLE_DeviceWidget(device, self._parent)

class Server_DevicesWidget(DevicesWidget[ServerDevice]):
    def __init__(self, devices, parent):
        super().__init__(devices, parent)

        for device in self.devices:
            self.add_device(device)

    def new_device(self):
        return ServerDevice(self._parent.comm_system, self.connection_changed, self.direct_msg_signal, False, False, SERVER_URL, WEB_SOCKET_URI, None)

    def new_device_widget(self, device):
        return Server_DeviceWidget(device, self._parent)

