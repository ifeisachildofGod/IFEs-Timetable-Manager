import os
import json
import pickle
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from PyQt6.QtWidgets import (
    QWidget,
    QLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QScrollArea,
    QMainWindow, QLabel, QDialog, QCheckBox,
    QGridLayout, QStackedWidget, QTableWidgetItem,
    QMessageBox, QMenu, QAbstractItemView, QFrame,
    QTableWidget, QHeaderView, QSizePolicy, QProgressBar,
    QFileDialog, QApplication, QMenuBar, QStyle, QStatusBar
)
from PyQt6.QtGui import (
    QAction, QFontMetrics, QIntValidator, QPainter,
    QColor, QMouseEvent, QDrag, QDragEnterEvent,
    QDragMoveEvent, QDropEvent, QPixmap
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, QMimeData, QSize,
    pyqtSignal, pyqtBoundSignal, QPoint
)
from PyQt6.QtPrintSupport import QPrinter

from utils.hooking import *
from utils.data import *


class Global:
    def __init__(self):
        self.data = {}
    
    def get(self):
        return self.data
    
    def add(self, entry):
        self.data[entry.id] = entry
    
    def remove(self, id):
        self.data.pop(id)
    
    def __len__(self):
        return self.data.__len__()
    
    def __iter__(self):
        return ((k, v) for k, v in self.data.items())
    
    def __getitem__(self, key):
        return self.data.__getitem__(key)
    
    # def __setitem__(self, key, value):
    #     return self.data.__setitem__(key, value)
    
    # def __delitem__(self, key):
    #     return self.data.__delitem__(key)


class Subjects(Global):
    @Hook(Signal.SubjectAdd, SignalType.RECIEVER)
    def add(self, entry: Subject):
        return super().add(entry)
    
    @Hook(Signal.SubjectRemove, SignalType.RECIEVER)
    def remove(self, id: ID):
        return super().remove(id)

class Teachers(Global):
    @Hook(Signal.TeacherAdd, SignalType.RECIEVER)
    def add(self, entry: Teacher):
        return super().add(entry)
    
    @Hook(Signal.TeacherRemove, SignalType.RECIEVER)
    def remove(self, id: ID):
        return super().remove(id)

class ClassLevels(Global):
    @Hook(Signal.ClassLevelAdd, SignalType.RECIEVER)
    def add(self, entry: ClassLevel):
        SETTINGS.TEACHER_rsma_mapping[entry.id] = None
        
        return super().add(entry)
    
    @Hook(Signal.ClassLevelRemove, SignalType.RECIEVER)
    def remove(self, id: ID):
        SETTINGS.TEACHER_rsma_mapping.pop(id)
        
        return super().remove(id)


SUBJECTS = Subjects()
TEACHERS = Teachers()
CLASS_LEVELS = ClassLevels()

SETTINGS = Settings(10, {}, 3, 7, {"Monday": 10, "Tuesday": 10, "Wednesday": 10, "Thursday": 10, "Friday": 10})
