import os
import sys
import pickle
from typing import Any, Callable, Optional, TypeVar

from PyQt6.QtWidgets import (
    QWidget, QLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QScrollArea,
    QMainWindow, QLabel, QDialog, QCheckBox,
    QGridLayout, QStackedWidget, QTableWidgetItem,
    QMessageBox, QMenu, QAbstractItemView, QFrame,
    QTableWidget, QHeaderView, QSizePolicy, QProgressBar,
    QFileDialog, QApplication, QMenuBar, QStyle, QStatusBar,
    QFontComboBox, QComboBox, QSpinBox, QSlider,
    QTextEdit, QRadioButton, QColorDialog, QTimeEdit
)
from PyQt6.QtGui import (
    QAction, QActionGroup, QIcon, QPixmap, QFont, QPen,
    QFontMetrics, QIntValidator, QPainter, QColor, QDrag, QCursor,
    QDragMoveEvent, QDragEnterEvent, QDropEvent, QEnterEvent, QMouseEvent,
    QRegularExpressionValidator, QShortcut, QKeySequence, QWheelEvent
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, QMimeData, QSize, QTime,
    QPoint, QPointF, QObject, QRect, QRectF, QRegularExpression,
    QByteArray, pyqtBoundSignal as pyBoundSignal, pyqtSignal as pySignal
)
from PyQt6.QtSvg import QSvgRenderer

from core import *

import sys
import faulthandler
import traceback
from datetime import datetime

crash_log = open("crash.log", "a", buffering=1)

faulthandler.enable(crash_log, all_threads=True)


def exception_hook(exc_type, exc_value, exc_traceback):
    crash_log.write(
        f"\n\n--- Python Exception: {datetime.now()} ---\n"
    )
    traceback.print_exception(
        exc_type,
        exc_value,
        exc_traceback,
        file=crash_log
    )
    crash_log.flush()

    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = exception_hook