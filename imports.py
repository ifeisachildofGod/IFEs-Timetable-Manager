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

from utils.core import *
from utils.data import *


class _Global:
    def __init__(self):
        self.data = {}
    
    def add(self, entry: Subject | Teacher | ClassLevel):
        self.data[entry.id] = entry
    
    def remove(self, id: ID):
        self.data.pop(id)


class _Subjects(_Global):
    @Hook(Signal.SubjectAdd, SignalType.RECIEVER)
    def add(self, entry):
        return super().add(entry)
    
    @Hook(Signal.SubjectRemove, SignalType.RECIEVER)
    def remove(self, entry):
        return super().remove(entry)

class _Teachers(_Global):
    @Hook(Signal.TeacherAdd, SignalType.RECIEVER)
    def add(self, entry):
        return super().add(entry)
    
    @Hook(Signal.TeacherRemove, SignalType.RECIEVER)
    def remove(self, entry):
        return super().remove(entry)

class _ClassLevels(_Global):
    @Hook(Signal.ClassLevelAdd, SignalType.RECIEVER)
    def add(self, entry):
        return super().add(entry)
    
    @Hook(Signal.ClassLevelRemove, SignalType.RECIEVER)
    def remove(self, entry):
        return super().remove(entry)


SUBJECTS = _Subjects()
TEACHERS = _Teachers()
CLASS_LEVELS = _ClassLevels()

