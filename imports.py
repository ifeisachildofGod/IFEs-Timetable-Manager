import os
import sys
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
    QAction, QActionGroup, QIcon,
    QFontMetrics, QIntValidator, QPainter,
    QColor, QMouseEvent, QDrag, QDragEnterEvent,
    QDragMoveEvent, QDropEvent, QPixmap
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, QMimeData, QSize,
    pyqtSignal, pyqtBoundSignal, QPoint
)
from PyQt6.QtPrintSupport import QPrinter

from utils.func_connection import *
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
    
    def set(self, value):
        self.__dict__ = value.__dict__
    
    def __len__(self):
        return self.data.__len__()
    
    def __iter__(self):
        return ((k, v) for k, v in self.data.items())
    
    def __getitem__(self, key: ID):
        return self.data.__getitem__(key)

class GlobalSubjects(Global):
    def __getitem__(self, key) -> Subject:
        return super().__getitem__(key)
    
    def add(self, entry: Subject):
        return super().add(entry)
    
    def remove(self, id: ID):
        return super().remove(id)

class GlobalTeachers(Global):
    def __getitem__(self, key) -> Teacher:
        return super().__getitem__(key)
    
    def add(self, entry: Teacher):
        return super().add(entry)
    
    def remove(self, id: ID):
        return super().remove(id)

class GlobalClassLevels(Global):
    def __getitem__(self, key) -> ClassLevel:
        return super().__getitem__(key)
    
    def add(self, entry: ClassLevel):
        SETTINGS.TEACHER_rsma_mapping[entry.id] = None
        
        return super().add(entry)
    
    def remove(self, id: ID):
        SETTINGS.TEACHER_rsma_mapping.pop(id)
        
        return super().remove(id)


SUBJECTS = GlobalSubjects()
TEACHERS = GlobalTeachers()
CLASS_LEVELS = GlobalClassLevels()

SETTINGS = Settings(10, {}, 3, 7, {"Monday": 10, "Tuesday": 10, "Wednesday": 10, "Thursday": 10, "Friday": 10}, "dark-blue")
