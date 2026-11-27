from imports import *
import traceback

ALL_EXTENSION_TYPE = "all"
TABLE_EXTENSION_TYPE = "ttbl"
TEMPLATE_EXTENSION_TYPE = "frmwk"

FT_MAPPING = {
    ALL_EXTENSION_TYPE: "All Files (*.*)",
    TABLE_EXTENSION_TYPE: "Timetable Files (*.ttbl)",
    TEMPLATE_EXTENSION_TYPE: "Template Files (*.frmwk)"
} ; REV_FT_MAPPING = {v: k for k, v in FT_MAPPING.items()}

class Thread(QThread):
    crashed = pySignal(Exception)

    def __init__(self, func: Optional[Callable] = None,
                 main_window: Optional[QMainWindow] = None):
        super().__init__()
        self.setParent(None)
        self.main_window = main_window
        self.func = func or (lambda: None)

    def run(self):
        try:
            self.func()
        except Exception as error:
            self.crashed.emit(error)
            if self.main_window is not None:
                signal = getattr(self.main_window, "crashed_signal", None)
                if signal is not None:
                    signal.emit(error)

    def stop(self, timeout: int = 2000) -> bool:
        """Request cooperative shutdown and wait up to timeout milliseconds."""
        if not self.isRunning():
            return True
        self.requestInterruption()
        self.quit()
        return self.wait(timeout)

class FileManager:
    def __init__(self, parent: QWidget, export_parent: QWidget, path: Optional[str], file_filter: str):
        self.path = path
        self.parent = parent
        self.export_parent = export_parent
        self.file_filter = file_filter
        
        self._from_save = False

    def set_callbacks(self, save: Optional[Callable[[str, str], str]], open_: Optional[Callable[[str, str], None] | Callable[[str, Any], None]], export: Optional[Callable[[str], str]]):
        self.save_callback = save
        self.open_callback = open_
        self.export_callback = export
    
    def new(self):
        if self.open_callback:
            self.open_callback()
    
    def open(self):
        file_path, file_type = QFileDialog.getOpenFileName(self.parent, "Open File", "", FT_MAPPING[ALL_EXTENSION_TYPE] + ";;" + self.file_filter)
        
        if file_path:
            try:
                if self.open_callback:
                    self.open_callback(file_path, file_type)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))
                traceback.print_exception(e)

    def save(self):
        if self.path:
            # try:
                if self.save_callback:
                    self.save_callback(self.path)
            # except Exception as e:
            #     QMessageBox.critical(self.parent, type(e).__name__, str(e))
        else:
            self._from_save = True
            self.save_as()

    def save_as(self):
        file_path, file_type = QFileDialog.getSaveFileName(self.parent, ("Save File" if self._from_save else "Save File As"), "", self.file_filter)
        
        if file_path:
            try:
                if self.save_callback:
                    self.path = file_path
                    self.save_callback(self.path, file_type)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))
                traceback.print_exception(e)
        
        if self._from_save:
            self._from_save = False

    def export(self, export_mode: int, file_filter: str):
        if export_mode == 0:
            file_path, _ = QFileDialog.getSaveFileName(self.export_parent, "Export", "", file_filter)
        elif export_mode == 1:
            file_path = QFileDialog.getExistingDirectory(self.export_parent, "Batch Export", "")
        else:
            raise Exception("Invalid Export Mode")
        
        if file_path:
            try:
                if self.export_callback:
                    self.export_callback(file_path)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))
                traceback.print_exception(e)


def resource_path(rel_path: str):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, rel_path)

