
from .imports import *
from .functions_and_uncategorized import Thread


"Name:Variable-Type(Data)|...|..."


class PasswordException(Exception):
    pass

@dataclass
class CommDevice:
    data_signal: pyBoundSignal
    connection_changed: pyBoundSignal
    
    port: int | str
    addr: str | None = None
    baud_rate: int | None = None
    pswd: str | None = None

class BaseCommSystem:
    def __init__(self, device: CommDevice, error_func: Callable[[Exception], None]):
        self.device = device
        self.error_func = error_func
        self.ble_scanner = BleakScanner()
        
        self.msg_buffer = []
        
        self.connected = False
        
        self.connection_message = ""
        self.data_points: list[tuple[int | str | list[str], pyBoundSignal]] = []
        
        self.direct_signal = self.device.data_signal
        self.connection_changed_signal = self.device.connection_changed
        
        self.serial_mode = False
        self.bluetooth_mode = False
    
    def set_bluetooth(self, a0: bool):
        self.bluetooth_mode = a0
    
    def set_serial(self, a0: bool):
        self.serial_mode = a0
    
    def set_data_point(self, key: int | str | list[str], signal: pyBoundSignal):
        if isinstance(key, str):
            self.data_points.append((key, signal))
        elif isinstance(key, (list, set, tuple)):
            self.data_points.append((list[key], signal))
        else:
            raise Exception(f"Bad key type: {type(key)}")
    
    def send_message(self, msg: str):
        if self.connected:
            self.msg_buffer.append(msg)
    
    def start_connection(self):
        if self.connected:
            raise Exception("Comm device already connected")
        
        self.connection_thread = Thread(self._connect)
        self.connection_thread.crashed.connect(self._crashed)
        self.connection_thread.start()
    
    def stop_connection(self):
        self.connected = False
        self.device.connection_changed.emit(self.connected)
    
    def find_devices(self, key: str):
        if key == "ser":
            return [port.name for port in comports()]
        elif key == "bt":
            return [(bl_info.address, bl_info.name) for bl_info in asyncio.run(self.ble_scanner.discover())]
    
    def _init_process_data(self, data: bytes):
        return data.decode().strip().removesuffix("|").strip()
    
    def _crashed(self, e: Exception):
        self.connection_thread.quit()
        self.error_func(e)
    
    def _data_process(self, msg_recv: str):
        full_data = self._process_data(msg_recv)
        
        data_key_mapping = {}
        for key, info in full_data.items():
            for d_k, d_signal in self.data_points:
                if isinstance(d_k, str):
                    if key == d_k:
                        d_signal.emit(info)
                        # break
                elif isinstance(d_k, list):
                    if key in d_k:
                        if d_k not in data_key_mapping:
                            data_key_mapping[d_k] = [None for _ in range(len(d_k))]
                        data_key_mapping[d_k][d_k.index(key)] = info
                        if None not in data_key_mapping[d_k]:
                            d_signal.emit(data_key_mapping[d_k])
                            # break
        
        self.direct_signal.emit(full_data)
    
    def _connect(self):
        if self.serial_mode:
            assert self.device.baud_rate is not None, "Invalid device"
            
            serial_target = serial.Serial(self.device.port, self.device.baud_rate, timeout=1)
            
            time.sleep(2)  # Wait for Target to initialize
            
            pswd_err = PasswordException("Internal password check failed\nDevice is not a registered attendance device")
            
            pswd_check_count = 0
            while True:
                serial_target.write((self.device.pswd + "\n").encode())
                
                if serial_target.in_waiting > 0:
                    response = serial_target.readline().decode().strip()
                    
                    if self.device.pswd == response:
                        self.connected = True
                        break
                    else:
                        raise pswd_err
                
                pswd_check_count += 1
                
                if pswd_check_count >= 15:
                    raise pswd_err
                
                time.sleep(1)
            
            self.device.connection_changed.emit(self.connected)
            
            while self.connected:
                if self.msg_buffer:
                    serial_target.write((self.msg_buffer.pop(0) + "\n").encode())
                
                if serial_target.in_waiting > 0:
                    bytetext = serial_target.readline()
                    msg_recv = self._init_process_data(bytetext)
                    
                    if msg_recv:
                        self._data_process(msg_recv)
            
            serial_target.close()
        elif self.bluetooth_mode:
            assert self.device.addr is not None, "Invalid device"
            
            # BLE override using bleak
            async def run_ble():
                async with BleakClient(self.device.addr) as client:
                    # Automatically find first writable characteristic
                    services = await client.services
                    writable_char = None
                    for service in services:
                        for char in service.characteristics:
                            if 'write' in char.properties or 'write-without-response' in char.properties:
                                writable_char = char.uuid
                                break
                        if writable_char:
                            break
                    
                    assert writable_char, "No writable characteristic found on device."
                    
                    while self.connected:
                        if self.msg_buffer:
                            msg = self.msg_buffer.pop(0)
                            await client.write_gatt_char(writable_char, msg.encode())
                        
                        data = await client.read_gatt_char(writable_char)
                        msg_recv = self._init_process_data(data)
                        if msg_recv:
                            self._data_process(msg_recv)

            asyncio.run(run_ble())
    
    def _process_data(self, data: str):
        processed_data = {}
        for sub_data_string in data.split("|"):
            name, data = sub_data_string.strip().split(":")
            
            processed_data[name] = self._process_sub_data(data)
        
        return processed_data
    
    def _process_sub_data(self, data: str, numbers: bool = False):
        data = data.strip()
        
        if not numbers:
            var_type = data[:data.find("(")]
            
            data = data.removeprefix(var_type).strip().removeprefix(f"(").removesuffix(")")
            
            if var_type == "l":
                data = [self._process_sub_data(sub_data, True) for sub_data in data.split(",")]
            elif var_type == "s":
                data = data
            elif var_type == "n":
                data = float(data)
            else:
                raise Exception(f"Type: ({var_type}) is not a valid type")
        else:
            data = float(data)
        
        return data


