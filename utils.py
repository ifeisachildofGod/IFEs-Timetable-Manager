from imports import *


EXTENSION_NAME = "ttbl"


class Thread(QThread):
    crashed = pyqtSignal(Exception)
    
    def __init__(self, main_window: QMainWindow, func: Callable):
        super().__init__()
        self.setParent(None)
        
        self.main_window = main_window
        
        self.func = func is not None and func or (lambda: ())
        main_window.close = self._window_closed()
    
    def _window_closed(self):
        def window_closed_event(self):
            self.exit(0)
            super().close()
        
        return window_closed_event
    
    def run(self):
        try:
            self.func()
        except Exception as e:
            QMessageBox.critical(None, e.__class__.__name__, str(e))
            self.crashed.emit(e)
            self.exit(-1)

class FileManager:
    def __init__(self, parent: QWidget, path: Optional[str], file_filter="Text Files (*.txt);;All Files (*)"):
        self.path = path
        self.parent = parent
        self.file_filter = file_filter
        self._from_save = False
        
        # Hooks: user-defined callbacks for file read/write
        self.save_callback: Optional[Callable[[str | None], str]] = None
        self.open_callback: Optional[Callable[[], None] | Callable[[str, Any], None]] = None
        self.load_callback: Optional[Callable[[str], Any]] = None

    def set_callbacks(self, save: Callable[[str | None], None], open_: Callable[[], None] | Callable[[str, Any], None], load: Callable[[str], Any], export: Callable[[str, int], None]):
        self.save_callback = save
        self.open_callback = open_
        self.load_callback = load
        self.export_callback = export
    
    def get_data(self):
        if self.path:
            return self.load_callback(self.path)
    
    def new(self):
        if self.open_callback:
            self.open_callback()
    
    def open(self):
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Open File", "", self.file_filter)
        if file_path:
            try:
                if self.open_callback:
                    self.open_callback(file_path)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))

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
        file_path, _ = QFileDialog.getSaveFileName(self.parent, ("Save File" if self._from_save else "Save File As"), "", self.file_filter)
        
        if file_path:
            try:
                if self.save_callback:
                    self.path = file_path
                    self.save_callback(self.path)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))
        
        if self._from_save:
            self._from_save = False

    def export(self, export_mode: int, file_filter: str):
        if export_mode == 0:
            file_path, _ = QFileDialog.getSaveFileName(self.parent, "Export File", "", file_filter)
        elif export_mode == 1:
            file_path = QFileDialog.getExistingDirectory(self.parent, "Batch Export Folder", "")
        else:
            raise Exception("Invalid Export Mode")
        
        if file_path:
            try:
                if self.export_callback:
                    self.export_callback(file_path, export_mode)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))


