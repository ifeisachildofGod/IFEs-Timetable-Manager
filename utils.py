import pygame

from imports import *

ALL_EXTENSION_TYPE = "all"
TABLE_EXTENSION_TYPE = "ttbl"
TEMPLATE_EXTENSION_TYPE = "frmwk"

FT_MAPPING = {
    ALL_EXTENSION_TYPE: "All Files (*.*)",
    TABLE_EXTENSION_TYPE: "Timetable Files (*.ttbl)",
    TEMPLATE_EXTENSION_TYPE: "Template Files (*.frmwk)"
} ; REV_FT_MAPPING = {v: k for k, v in FT_MAPPING.items()}

pygame.init()

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
            self.main_window.crashed_signal.emit(e)
            self.exit(-1)

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

