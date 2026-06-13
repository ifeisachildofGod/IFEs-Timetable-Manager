
from utils import *
from imports import *

from widgets.base import *

import math
from typing import Literal, TypeVar

T = TypeVar("T")

class ProgressBar(QProgressBar):
    def __init__(self, master: QWidget):
        super().__init__()
        
        self.update_var = None
        self.update_max = None
        
        self.progress = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_bar)
        
        self.master = master
        
        if self.master:
            self.master.setVisible(False)
        else:
            self.setVisible(False)
    
    def start(self, mst: int):
        self.progress_timer.start(mst)
        if self.master:
            self.master.setVisible(True)
        else:
            self.setVisible(True)
    
    def set_var_func(self, update_var: Callable[[], int]):
        self.update_var = update_var
    
    def set_max(self, update_max: Callable[[], int]):
        self.update_max = update_max
    
    def update_progress_bar(self):
        self.progress = int((self.update_var() / self.update_max()) * 100)
        
        if self.progress >= 100:
            self.progress_timer.stop()
            if self.master:
                self.master.setVisible(False)
            else:
                self.setVisible(False)
        else:
            self.setValue(self.progress)


class NumberLineEdit(BaseWidget):
    textChanged = pyqtSignal(int)
    
    def __init__(self, number: int, min_validatorAmt: int = 0, max_validatorAmt: int = 10):
        super().__init__(QHBoxLayout)
        
        self._min_num = min_validatorAmt
        self._max_num = max_validatorAmt
        
        self.edit = QLineEdit()
        self.edit.textChanged.connect(self._updateNumber)
        self.edit.setValidator(QIntValidator())
        self.setNumber(number)
        
        self.min_num = self._min_num
        self.max_num = self._max_num
        
        buttons_widget = BaseWidget()
        buttons_widget.setStyleSheet("background: none;")
        
        self.addWidget(self.edit, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        self.addWidget(buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        
        buttons_widget.setContentsMargins(0, 0, 0, 0)
        
        increment_button = ArrowWidget(180)
        increment_button.setContentsMargins(0, 0, 0, 0)
        increment_button.mouseclicked.connect(lambda: self._incDecNumber(1))
        
        decrement_button = ArrowWidget(0)
        increment_button.setContentsMargins(0, 0, 0, 0)
        decrement_button.mouseclicked.connect(lambda: self._incDecNumber(-1))
        
        buttons_widget.addWidget(increment_button, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        buttons_widget.addWidget(decrement_button, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.setFixedHeight(50)
        self.edit.setFixedHeight(30)
        
        self._updateNumber(str(number))
    
    @property
    def min_num(self):
        return self._min_num
    
    @min_num.setter
    def min_num(self, value: int):
        self._min_num = value
        
        if self._min_num > self.number():
            self.setNumber(self._min_num)
        
        assert self.min_num <= self.max_num, f"Min: {self.min_num}; Max: {self.max_num}"
    
    @property
    def max_num(self):
        return self._max_num
    
    @max_num.setter
    def max_num(self, value: int):
        self._max_num = value
        
        if self._max_num < self.number():
            self.setNumber(self._max_num)
        
        assert self.min_num <= self.max_num, f"Min: {self.min_num}; Max: {self.max_num}"
    
    def number(self):
        return int(self._number)
    
    def setNumber(self, number: int):
        self._number = str(number)
        self.edit.setText(self._number)
    
    def setPlaceholderText(self, text: str):
        self.edit.setPlaceholderText(text)
    
    def _updateNumber(self, text: str):
        if not text.isnumeric() or self.max_num < int(text) < self.min_num:
            self.edit.setText(self._number)
        else:
            self.textChanged.emit(int(text))
            self._number = text
    
    def _incDecNumber(self, direction: int):
        number = self.number() + direction
        
        if self.min_num <= number <= self.max_num:
            self.setNumber(number)

class ArrowWidget(QLabel):
    mouseclicked = pyqtSignal()
    
    def __init__(self, angle: int = 0, parent=None):
        super().__init__("▼", parent)
        self.angle = angle  # Angle in degrees to rotate the text
        self.setProperty("class", "Arrow")
    
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.mouseclicked.emit()
    
    def setAngle(self, angle):
        self.angle = angle
        self.update()  # Trigger a repaint
    
    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Save the painter's current state
        painter.save()

        # Translate to the center of the label
        center = self.rect().center()
        painter.translate(center)

        # Rotate the painter
        painter.rotate(self.angle)

        # Translate back and draw the text
        center.setX(center.x() + (2 if self.angle >= 180 else -1))
        painter.translate(-center)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

        # Restore the painter's state
        painter.restore()


class MenuFrame(QFrame):
    def __init__(self):
        super().__init__()
        
        self.setProperty("class", "DPMenu")
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self._pos = self.pos()
    
    def set_pos(self, pos: QPoint):
        self._pos = pos
    
    def toogle(self):
        if self.isVisible():
            self.hide()
        else:
            self.move(self._pos)
            self.show()

class _SearchEditOption(BaseWidget):
    def __init__(self, se: "SearchEdit", data_point: T, style: str | list | tuple, info: tuple[Optional[str], Optional[str], Optional[str], Optional[str]]):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "SearchOptions")
        self.setContentsMargins(10, 10, 10, 10)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        self.se = se
        self.data_point = data_point
        self.main_text, self.right_text, self.bottom_text, self.end_text = info
        
        if isinstance(style, str):
            self.m_style = self.b_style = self.r_style = self.e_style = style
        elif isinstance(style, (list, tuple)):
            for i, (x, s_name) in enumerate(((self.main_text, "m_style"), (self.bottom_text, "b_style"), (self.right_text, "r_style"), (self.end_text, "e_style"))):
                if x is not None:
                    setattr(self, s_name, style[i])
        else:
            raise TypeError("Style is of type:", type(style))
        
        assert self.m_style is not None
        
        self.main_label = QLabel() ; self.main_label.setMinimumHeight(25)
        self.bottom_label = QLabel() ; self.main_label.setMinimumHeight(17)
        self.right_label = QLabel() ; self.main_label.setMinimumHeight(19)
        self.end_label = QLabel() ; self.main_label.setMinimumHeight(15)
        
        w1 = BaseWidget()
        w1.setContentsMargins(0, 0, 0, 0)
        w1.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        
        main_right_widget = BaseWidget(QHBoxLayout)
        main_right_widget.setSpacing(10)
        main_right_widget.setContentsMargins(0, 0, 0, 0)
        
        main_right_widget.addWidget(self.main_label)
        main_right_widget.addWidget(self.right_label)
        
        w1.addWidget(main_right_widget)
        w1.addWidget(self.bottom_label, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.addWidget(w1)
        self.addWidget(self.end_label, alignment=Qt.AlignmentFlag.AlignRight)
    
    def update_highlights(self, text: str, score_highlight_data: tuple[float | Literal[-1], tuple[list[int], list[int], list[int], list[int]]]):
        score, (main_hi, right_hi, bottom_hi, end_hi) = score_highlight_data
        
        if score != -1:
            if not self.isVisible():
                self.setVisible(True)
            
            self.main_label.setText("".join([f"<span style='font-size: 25px; {f"{self.m_style}" if i in main_hi else ""}'>{c}</span>" for i, c in enumerate(self.main_text)]))
            self.right_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-150__minimum}")}; font-size: 19px; font-weight: 300; {f"{self.r_style}" if i in right_hi else ""}'>{c}</span>" for i, c in enumerate(self.right_text)]) if self.right_text else "")
            self.bottom_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-150__minimum}")}; font-size: 15px; font-weight: 500; {f"{self.b_style}" if i in bottom_hi else ""}'>{c}</span>" for i, c in enumerate(self.bottom_text)]) if self.bottom_text else "")
            self.end_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-100__minimum}")}; font-size: 13px; font-weight: 300; {f"{self.e_style}" if i in end_hi else ""}'>{c}</span>" for i, c in enumerate(self.end_text)]) if self.end_text else "")
        else:
            self.setVisible(False)
    
    def mousePressEvent(self, a0):
        self.se.hide()
        self.se.search_le.blockSignals(True)
        self.se.search_le.clear()
        self.se.search_le.blockSignals(False)
        
        if self.se.goto_search_callback:
            self.se.goto_search_callback(self.data_point)
        
        return super().mousePressEvent(a0)

class SearchEdit(QFrame):
    DEBOUNCE_MS = 120
    MAX_RESULTS = math.inf

    def __init__(
            self,
            get_search_scope_callback: Callable[
                [], list[tuple[T, str, tuple[Optional[str], Optional[str], Optional[str]], list[Optional[str]]]]
            ],
            goto_search_callback: Optional[Callable[[T], None]] = None
        ):
        super().__init__(None)

        self.get_search_scope_callback = get_search_scope_callback
        self.goto_search_callback = goto_search_callback

        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        self.setProperty("class", "option-menu")
        self.setFixedWidth(500)

        self.ref_data = {}
        self._updating = False

        # ---------- Layout ----------
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("Search")
        self.search_le.setFixedWidth(496)
        self.search_le.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        self.main_layout.addWidget(self.search_le, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.options_widget_wrapper = BaseScrollWidget()
        
        self.options_widget = BaseWidget()
        self.options_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        self.options_widget_wrapper.addWidget(self.options_widget)
        self.options_widget_wrapper.addStretch()
        
        self.options_widget_wrapper.setFixedWidth(496)
        self.options_widget_wrapper.setMinimumHeight(220)
        self.options_widget_wrapper.setVisible(False)

        self.main_layout.addWidget(self.options_widget_wrapper, alignment=Qt.AlignmentFlag.AlignTop)

        # ---------- Debounce ----------
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._run_search)
        
        self.search_le.textEdited.connect(self._on_text_edited)
    
    def _on_text_edited(self, _):
        self._search_timer.start(self.DEBOUNCE_MS)

    def show(self):
        self.search_le.blockSignals(True)
        self.search_le.clear()
        self.search_le.blockSignals(False)

        self._run_search()
        super().show()
        self.search_le.setFocus()
    
    def _run_search(self):
        if self._updating:
            return
        
        self._updating = True
        text = self.search_le.text().strip()
        
        if not text:
            self.options_widget_wrapper.setVisible(False)
            self._updating = False
            
            return
        
        score_data = sorted(
            [
                (
                    data_point,
                    (name, right, bottom, end),
                    self._score(text, name, (right, bottom, end), bg)
                )
                for data_point, name, (right, bottom, end), bg
                in self.get_search_scope_callback()
            ],
            key=lambda x: x[2][0],
            reverse=True
        )
        
        ref_data_copy = self.ref_data.copy()
        l_ref_data = list(ref_data_copy)
        
        self.ref_data.clear()
        
        added = 0
        for index, (data_point, info, score_highlight_data) in enumerate(score_data):
            added += 1
            
            if data_point not in ref_data_copy:
                widget = _SearchEditOption(self, data_point, f"color: {THEME_MANAGER.pallete_get("fg1")}; font-weight: bold;", info)
                
                self.options_widget.addWidget(widget)
            else:
                widget = ref_data_copy[data_point]
                
                if index != l_ref_data.index(data_point):
                    self.options_widget.insertWidget(index, widget)
            
            widget.update_highlights(text, score_highlight_data)
            self.ref_data[data_point] = widget
            
            if added >= self.MAX_RESULTS:
                break
        
        for dp, widg in ref_data_copy.items():
            if dp not in self.ref_data:
                self.options_widget.removeWidget(widg)
        
        # added = 0
        # for data_point, (name, right, bottom, end), (score, indices) in score_data:
        #     if score == -1 or added >= self.MAX_RESULTS:
        #         continue
            
        #     label = QLabel(
        #         self._stylize_text_indices(
        #             name,
        #             f"color: {THEME_MANAGER.pallete_get("fg1")}; font-weight: bold;",
        #             right,
        #             bottom,
        #             end,
        #             indices
        #         )
        #     )
        #     label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        #     label.setProperty("class", "SearchOptions")
        #     label.mousePressEvent = self._make_option_clicked_func(data_point)
            
        #     self.options_widget.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)
        #     added += 1
        
        self.options_widget_wrapper.setVisible(added > 0)
        
        self._updating = False
    
    def _score(
        self,
        text: str,
        potential_match: str,
        extra_text_data: Optional[tuple[Optional[str], Optional[str], Optional[str]]] = None,
        backgrounds_texts: Optional[list[Optional[str]]] = None
    ) -> tuple[float | Literal[-1], tuple[list[int], list[int], list[int], list[int]]]:
        l_text = text.lower()
        l_target = potential_match.lower()
        
        space_amt = 0
        additions = 0
        
        text_len = len(l_text)
        target_len = len(l_target)
        
        index = 0
        
        bg_data = []
        
        score_indices = []
        right_indices = []
        bottom_indices = []
        end_indices = []
        
        right_score = -1
        bottom_score = -1
        end_score = -1
        
        if extra_text_data:
            right_text, bottom_text, end_text = extra_text_data
            
            if right_text:
                right_score, right_indices = self._score(text, right_text)
                right_indices = right_indices[0]
            if bottom_text:
                bottom_score, bottom_indices = self._score(text, bottom_text)
                bottom_indices = bottom_indices[0]
            if end_text:
                end_score, end_indices = self._score(text, end_text)
                end_indices = end_indices[0]
        
        if backgrounds_texts:
            bg_data = [self._score(text, bg_text)[0] for bg_text in backgrounds_texts if bg_text is not None]
        
        for i, c in enumerate(l_text):
            f_index = l_target[index:].find(c)
            
            if f_index != -1 and text_len <= target_len:
                space_amt += f_index
                index += f_index + 1
                
                additions += text[i] == potential_match[index - 1]
                additions += f_index == 0
                
                score_indices.append(index - 1)
                
                continue
            break
        else:
            return (text_len / (target_len + space_amt)) + additions, (score_indices, [], [], [])
        
        if bottom_score == -1 and right_score != -1:
            return right_score / 20, ([], right_indices, [], [])
        elif right_score == -1 and bottom_score != -1:
            return bottom_score / 20, ([], [], bottom_indices, [])
        elif right_score != -1 and bottom_score != -1:
            return (right_score + bottom_score) / 20, ([], right_indices, bottom_indices, [])
        elif end_score != -1:
            return end_score / 20, ([], [], [], end_indices)
        elif bg_data:
            for bg_score in bg_data:
                if bg_score != -1:
                    return bg_score / 20, ([], [], [], [])
        
        return -1, ([], [], [], [])

class CustomTitleBar(BaseWidget):
    def __init__(self, parent: QWidget, get_search_scope_func: Callable, goto_search_func: Callable):
        super().__init__(QHBoxLayout)
        
        self.master = parent
        
        self.setFixedHeight(40)
        self.setProperty("class", "TitleBar")
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)
        
        self.left_widget = BaseWidget(QHBoxLayout)
        self.left_widget.setProperty("class", "TitleBar")
        self.left_widget.setContentsMargins(0, 0, 60, 0)
        self.left_widget.setSpacing(0)
        
        self.center_widget = BaseWidget(QHBoxLayout)
        self.center_widget.setProperty("class", "TitleBar")
        self.center_widget.setContentsMargins(60, 0, 60, 0)
        
        right_widget = BaseWidget(QHBoxLayout)
        right_widget.setProperty("class", "TitleBar")
        right_widget.setContentsMargins(60, 0, 0, 0)
        right_widget.setSpacing(0)
        
        # Center widget
        self.search_edit = SearchEdit(get_search_scope_func, goto_search_func)
        
        self.search_pb = QPushButton("Search Subjects")
        self.search_pb.setFixedWidth(self.search_edit.width())
        self.search_pb.setProperty("class", "SearchPB")
        self.search_pb.clicked.connect(self._open_search_edit)
        
        self.center_widget.addWidget(self.search_pb)
        
        # Right widget
        # Nothing here
        
        self.addWidget(self.left_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self.center_widget)
        self.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignRight)
    
    def _open_search_edit(self):
        self.search_edit.move(self.center_widget.mapToGlobal(QPoint(self.search_pb.x(), self.search_pb.y())))
        self.search_edit.search_le.setFocus()
        
        self.search_edit.show()

class MainTitleBar(CustomTitleBar):
    def __init__(self, parent, menu_bar: QMenuBar, get_search_scope_func: Callable, goto_search_func: Callable, go_back_func: Callable, go_forward_func: Callable):
        super().__init__(parent, get_search_scope_func, goto_search_func)
        
        menu_bar.setFixedHeight(40)
        menu_bar.setContentsMargins(0, 0, 0, 0)
        menu_bar.setStyleSheet("QMenuBar {background-color: transparent; border: none;}")
        
        self.left_widget.addWidget(menu_bar)
        
        self.go_back_button = QPushButton("<")
        self.go_forward_button = QPushButton(">")
        
        self.go_back_button.setProperty("class", "GoButton")
        self.go_forward_button.setProperty("class", "GoButton")
        
        self.go_back_button.clicked.connect(go_back_func)
        self.go_forward_button.clicked.connect(go_forward_func)
        
        self.center_widget.insertWidget(0, self.go_back_button)
        self.center_widget.insertWidget(1, self.go_forward_button)

class WidgetDropdown(BaseWidget):
    def __init__(self, title: str, widget: QWidget, parent=None):
        super().__init__(parent)
        
        self.widget = widget
        
        self.setSpacing(0)
        
        self.setProperty("class", "Bordered")
        self.setProperty("class", "BorderRadiused")
        self.setProperty("class", "DropdownCheckboxes")
        
        self.header = BaseWidget(QHBoxLayout)
        self.header.setProperty("class", "DPC_Header")
        self.header.setFixedHeight(50)
        self.header.setContentsMargins(12, 0, 12, 0)
        self.header.mousePressEvent = self.tdp_event_func
        
        self.toogle_icon = ArrowWidget(270)
        self.toogle_icon.setProperty("class", "Arrow")
        self.toogle_icon.mouseclicked.connect(self.toogle_widget)
        self.toogle_icon.setContentsMargins(0, 0, 10, 0)
        
        self.title_label = QLabel(title)
        
        self.header.addWidget(self.toogle_icon)
        self.header.addWidget(self.title_label)
        self.header.addStretch()
        
        self.addWidget(self.header)
        self.addWidget(self.widget) # type: ignore
    
    def tdp_event_func(self, a0: QMouseEvent | None):
        if a0.button() == Qt.MouseButton.LeftButton: # type: ignore
            self.toogle_widget()
    
    def toogle_widget(self):
        self.toogle_icon.setAngle(0 if self.toogle_icon.angle != 0 else 270)
        self.widget.setVisible(not self.widget.isVisible())

class EditableCancelableEntry(BaseWidget):
    deleted = pyqtSignal()
    started_editing_signal = pyqtSignal()
    finished_editing_signal = pyqtSignal()
    
    def __init__(self, initial_text: str | None = None):
        super().__init__(QHBoxLayout)
        self.setProperty("class", "OptionTag")
        
        self.text = initial_text if initial_text is not None else ""
        self.is_editing = False
        
        self.setContentsMargins(4, 2, 4, 2)
        self.setSpacing(4)
        
        # Input mode widgets
        self.input = QLineEdit()
        self.input.setProperty("class", "OptionEdit")
        self.input.setText(self.text)
        self.input.setPlaceholderText("Enter option")
        self.input.setFixedWidth(80)  # Fix input width
        self.input.returnPressed.connect(self.input.clearFocus)
        self.input.editingFinished.connect(self.finish_editing)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setProperty("class", "Close")
        self.close_btn.clicked.connect(self.remove)
        self.close_btn.setFixedSize(20, 20)
        
        self.deleted.connect(self.deleteLater)
        self.started_editing_signal.connect(self.start_editing)
        self.finished_editing_signal.connect(self._finished_editing)
        
        # Label mode widget
        self.label = QLabel(self.text)
        self.label.setMinimumWidth(80)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.mousePressEvent = lambda _: self.started_editing_signal.emit()
        
        # Initialize both widgets but hide input initially
        self.addWidget(self.label)
        self.addWidget(self.input)
        self.addWidget(self.close_btn)
        self.input.hide()
        
        self.setFixedHeight(30)
        self.setFixedWidth(130)
    
    def _finished_editing(self):
        if self.is_editing:
            self.text = self.input.text().strip()
            self.is_editing = False
            self.setup_display_mode()
            self.label.setText(self.text)
            self.label.show()
    
    def setup_display_mode(self):
        self.label.show()
        self.input.hide()
        self.close_btn.show()
    
    def setup_edit_mode(self):
        self.label.hide()
        self.input.show()
        self.close_btn.show()
    
    def start_editing(self):
        if not self.is_editing:
            self.input.setText(self.text)
            self.setup_edit_mode()
            self.input.setFocus()
            
            self.is_editing = True
    
    def finish_editing(self):
        self.finished_editing_signal.emit()
    
    def remove(self):
        self.deleted.emit()
    
    def get_text(self):
        return self.text




class Image(QLabel):
    def __init__(self, path: str, width: int | None = None, height: int | None = None):
        super().__init__()
        
        self._width = width
        self._height = height
        
        self.setImagePath(path)
    
    def setImagePath(self, path: str):
        pixmap = QPixmap(path)
        
        if self._width is not None or self._height is not None:
            if self._height is not None and self._width is None:
                self.setFixedSize(int(self._height * pixmap.size().width() / pixmap.size().height()), self._height)
            elif self._width is not None and self._height is None:
                self.setFixedSize(self._width, int(self._width * pixmap.size().height() / pixmap.size().width()))
            else:
                self.setFixedSize(self._width, self._height)
        
        self.setScaledContents(True)  # Optional: scale image to fit self
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
        # self.update()


class _SideBarOption(BaseWidget):
    def __init__(self, name: str, do_action: Callable):
        super().__init__(QHBoxLayout)
        
        self.SELECTED_STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget.SideBarOption {{
                    background-color: {fg4};
                }}
                
                QLabel {{
                    color: {text};
                    font-weight: 500;
                }}
            """
        )
        
        self.UNSELECTED_STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget.SideBarOption {{
                    background-color: transparent;
                }}
                
                QWidget.SideBarOption:hover {{
                    background-color: {hover__bg3};
                }}
                
                QLabel {{
                    color: {hover__text};
                }}
            """
        )
        
        self.setProperty("class", "SideBarOption")
        self.setStyleSheet(self.UNSELECTED_STYLESHEET)
        
        self.setSpacing(0)
        self.setContentsMargins(10, 8, 10, 8)
        
        self.do_action = do_action
        
        self.addWidget(QLabel(name))
        self.getWidget().mousePressEvent = lambda _: self._clicked(True)
    
    def _clicked(self, do: bool):
        if do:
            self.setStyleSheet(self.SELECTED_STYLESHEET)
            self.do_action()
        else:
            self.setStyleSheet(self.UNSELECTED_STYLESHEET)

class SideBar(BaseWidget):
    def __init__(self, *content: tuple[str | None, Callable] | None):
        super().__init__()
        
        self.widgets = []
        
        self.setFixedWidth(210)
        
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setProperty("class", "ExportEditorSideBar")
        
        for index, data in enumerate(content):
            name, action = data if data is not None else (None, None)
            
            option = (
                _SideBarOption(name, self._mf_option_changed(index, action))
                if name is not None else
                SeperatorWidget(Qt.Orientation.Vertical, 10, None, 1)
            )
                
            self.widgets.append(option)
            self.addWidget(option)
        
        for widget in self.widgets:
            if isinstance(widget, _SideBarOption):
                widget._clicked(True)
                
                break
        
        self.addStretch()
    
    def _mf_option_changed(self, index: int, action: Callable):
        def func():
            action()
            
            if hasattr(self, "curr_widget"):
                self.curr_widget._clicked(False)
            
            self.curr_widget = self.widgets[index]
        
        return func

class _Tab(BaseWidget):
    tab_selected = pyqtSignal()
    
    def __init__(self, name: str):
        super().__init__()
        
        self.SELECTED_STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget {{
                    background-color: transparent;
                }}
                
                QLabel {{
                    font-size: 13px;
                    font-weight: bold;
                    color: {fg4};
                }}
                
                QLabel:hover {{
                    color: {hover__fg4};
                }}
            """
        )
        
        self.UNSELECTED_STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget {{
                    background-color: transparent;
                }}
                
                QLabel {{
                    color: {text};
                    font-size: 13px;
                }}
                
                QLabel:hover {{
                    color: {hover__text};
                }}
            """
        )
        
        self.setFixedHeight(35)
        
        self.setSpacing(0)
        self.setContentsMargins(10, 0, 10, 15)
        
        self.name = name
        
        self.tab_selected.connect(lambda: self.setState(self.styleSheet() != self.SELECTED_STYLESHEET))
        self.setState(False)
        
        self.addWidget(QLabel(self.name))
    
    def setState(self, state):
        if state and self.styleSheet() != self.SELECTED_STYLESHEET:
            self.setStyleSheet(self.SELECTED_STYLESHEET)
        elif self.styleSheet() != self.UNSELECTED_STYLESHEET:
            self.setStyleSheet(self.UNSELECTED_STYLESHEET)
    
    def mousePressEvent(self, a0):
        self.tab_selected.emit()
        
        return super().mousePressEvent(a0)

class TabView(BaseWidget):
    def __init__(self, tabs: dict[str, QWidget], *extra_title_widgets: QWidget):
        super().__init__()
        
        self.STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget.TabView {{
                    background-color: {bg1};
                }}
                
                QWidget.TabWidget {{
                    background-color: transparent;
                    border-bottom: 1px solid {secondary};
                }}
            """ 
        )   
        
        self.setProperty("class", "TabView")
        
        self.setSpacing(0)
        
        self.tabs = tabs
        self.extra_title_widgets = extra_title_widgets
        
        self.tabWidget = BaseWidget(QHBoxLayout)
        self.tabWidget.setProperty("class", "TabWidget")
        self.tabWidget.setFixedHeight(40)
        self.tabWidget.setStyleSheet(self.STYLESHEET)
        self.tabWidget.setContentsMargins(10, 10, 10, 0)
        
        self.bodyWidget = QStackedWidget()
        
        self._initTabs()
        
        self.main_layout.addWidget(self.tabWidget)
        self.main_layout.addWidget(self.bodyWidget)
    
    def _mf_tab_changed(self, tab, index: int):
        def func():
            if hasattr(self, "curr_tab"):
                self.curr_tab.setState(self.curr_tab == tab)
            
            self.curr_tab = tab
            
            self.bodyWidget.setCurrentIndex(index)
        
        return func
    
    def _initTabs(self):
        for tab_index, (tab_name, widget) in enumerate(self.tabs.items()):
            tab = _Tab(tab_name)
            func = self._mf_tab_changed(tab, tab_index)
            
            if tab_index == 0:
                func()
                tab.setState(True)
            
            tab.tab_selected.connect(func)
            
            self.tabWidget.addWidget(tab)
            self.bodyWidget.addWidget(widget)
        
        self.tabWidget.addStretch()
        
        for et_widget in self.extra_title_widgets:
            self.tabWidget.addWidget(et_widget)

class SeperatorWidget(BaseWidget):
    def __init__(self, orientation: Qt.Orientation, spacing: int, width: Optional[int] = None, height: Optional[int] = None):
        super().__init__()
        
        x_spacing = spacing // 2 if orientation == Qt.Orientation.Horizontal else 0
        y_spacing = spacing // 2 if orientation == Qt.Orientation.Vertical else 0
        
        self.setContentsMargins(x_spacing, y_spacing, x_spacing, y_spacing)
        
        widget = BaseWidget()
        
        if width:
            widget.setFixedWidth(width)
        if height:
            widget.setFixedHeight(height)
        
        widget.setStyleSheet(f"background-color: {THEME_MANAGER.process_stylesheet("{interpolate-250__maximum}")};")
        
        self.addWidget(widget)

class SeparatorLabel(BaseWidget):
    def __init__(self, text: str):
        super().__init__(QHBoxLayout)
        
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(text)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        label.setContentsMargins(0, 0, 5, 0)
        self.setStyleProperty(label, "font-weight", "bold")
        
        sep_widget = SeperatorWidget(Qt.Orientation.Vertical, 0, None, 1)
        sep_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sep_widget.setContentsMargins(0, 7, 0, 0)
        
        self.addWidget(label)
        self.addWidget(sep_widget)

class LabeledWidget(BaseWidget):
    def __init__(self, starter: str | QWidget, widget: QWidget):
        super().__init__(QHBoxLayout)
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.addWidget(QLabel(starter) if isinstance(starter, str) else starter, alignment=Qt.AlignmentFlag.AlignLeft)
        self.addSpacing(10)
        self.addWidget(widget, alignment=Qt.AlignmentFlag.AlignRight)



class IconToolBarOption(BaseWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        if args or kwargs:
            self.initialize(*args, **kwargs)
    
    def initialize(
            self,
            content: Callable | list[tuple[str, Callable | dict[str, Callable] | tuple[Callable, Callable]]] | QWidget,
            title: Optional[str | QLabel] = None,
            icon_path: Optional[str] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            font_size: Optional[int] = None,
            show_dp_icon: bool = False
        ):
        self.content = content
        
        self.HOVER_STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget.IconToolBarOption:hover {{
                    background-color: {hover__bg3}
                }}
            """
        )
        
        self.STYLESHEET = THEME_MANAGER.process_stylesheet(
            f"""
                QWidget.IconToolBarOption {{{{
                    background-color: transparent;
                }}}}
                
                QWidget.IconToolBarOption QWidget._TopWidget QLabel.TitleLabel {{{{
                    background: none;
                    font-size: {font_size}px;
                }}}}
                QWidget.IconToolBarOption QLabel {{{{
                    color: {{text}};
                    font-size: {font_size}px;
                }}}}
            """
        ) + self.HOVER_STYLESHEET
        
        self.setSpacing(0)
        self.setContentsMargins(5, 5, 5, 5)
        
        self.getWidget().setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.setProperty("class", "IconToolBarOption")
        self.setStyleSheet(self.STYLESHEET)
        
        if isinstance(title, str):
            title_label = QLabel(title)
            title_label.setProperty("class", "TitleLabel")
        else:
            title_label = title
        
        self.arrow = None
        if not isinstance(content, Callable) and show_dp_icon:
            self.arrow = ArrowWidget(270)
            
            self.addWidget(self.arrow)
        
        if icon_path is not None:
            self.addWidget(Image(icon_path, width, height))
        if title is not None:
            self.addWidget(title_label)
        
        self.getWidget().mousePressEvent = self._clicked
        
        if not isinstance(self.content, Callable) and not isinstance(self.content, list):
            self.content.setProperty("class", "Bordered")
            
            def hide_event(_):
                self.setStyleSheet(self.STYLESHEET)
                self.update()
                
                if self.arrow:
                    self.arrow.setAngle(270)
            
            self.content.hideEvent = hide_event
    
    def getMenuPosition(self, menu_widget: QWidget | QMenu):
        pos = self.getWidget().mapToGlobal(QPoint(self.getWidget().x(), self.getWidget().y() + self.getWidget().rect().height() - self.getWidget().contentsMargins().bottom()))
        
        screen_geom = self.getWidget().screen().geometry()
        g_pos = self.getWidget().mapToGlobal(self.getWidget().pos())
        
        offset_x_factor = 1 if g_pos.x() < screen_geom.width() / 2 else -1
        offset_y_factor = 1 if g_pos.y() < screen_geom.height() / 2 else -1
        
        left_most = menu_widget.rect().width() - self.getWidget().width()
        top_most = menu_widget.rect().height() + self.getWidget().height()
        
        off_X = int(left_most - left_most * (offset_x_factor + 1) / 2)
        off_Y = int(top_most - top_most * (offset_y_factor + 1) / 2)
        
        return pos - QPoint(off_X, off_Y)
    
    def _clicked(self, a0):
        if isinstance(self.content, Callable):
            return self.content()
        else:
            self.setStyleSheet(self.STYLESHEET.replace(self.HOVER_STYLESHEET, "") + THEME_MANAGER.process_stylesheet("QWidget.IconToolBarOption {{ background-color: {hover__bg3} }}"))
            self.update()
            
            if self.arrow:
                self.arrow.setAngle(0)
            
            if isinstance(self.content, list):
                menu = self._getMenu(self, self.content)
                
                menu.exec(self.getMenuPosition(menu))
                
                self.setStyleSheet(self.STYLESHEET)
                self.update()
            elif isinstance(self.content, QWidget):
                self.content.setWindowFlags(Qt.WindowType.Popup)
                
                self.content.move(self.getMenuPosition(self.content))
                self.content.show()
    
    def _getMenu(self, parent: QMenu | BaseWidget, content: list | None, name: Optional[str] = None):
        args = [parent]
        if name is not None:
            args.insert(0, name)
        
        menu = QMenu(*args)
        
        for data in content:
            if data is None:
                menu.addSeparator()
            else:
                optionName, optionData = data
                
                if isinstance(optionData, (Callable, tuple)):
                    optionAction, disableAction = (optionData, None) if isinstance(optionData, Callable) else optionData
                    
                    action = menu.addAction(optionName, optionAction)
                    
                    action.setDisabled(disableAction() if disableAction else False)
                elif isinstance(optionData, list):
                    menu.addMenu(self._getMenu(menu, optionData, optionName))
                else:
                    raise
        
        return menu

class TitledWidget(BaseWidget):
    def __init__(self, title: str | QWidget, widget: QWidget, *extra_title_widgets: QWidget, scrollable: bool = False):
        super().__init__()
        
        self.STYLESHEET = THEME_MANAGER.process_stylesheet(
            """
                QWidget.TitleArea {{
                    background-color: {bg1};
                }}
                
                QWidget.Body {{
                    background-color: {bg2};
                }}
            """
        )
        
        self.setProperty("class", "TitledWidget")
        self.setStyleSheet(self.STYLESHEET)
        
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Title Area
        titleArea = QWidget()
        titleArea.setProperty("class", "TitleArea")
        titleArea.setFixedHeight(30)
        titleAreaLayout = QHBoxLayout(titleArea)
        titleAreaLayout.setContentsMargins(5, 0, 5, 0)
        
        if isinstance(title, str):
            self.titleWidget = QLabel(title)
            self.titleWidget.setProperty("class", "Title")
        else:
            self.titleWidget = title
        
        titleAreaLayout.addWidget(self.titleWidget)
        titleAreaLayout.addStretch()
        for et_widget in extra_title_widgets:
            titleAreaLayout.addWidget(et_widget)
        
        # Widget Area
        bodyWidget = BaseScrollWidget() if scrollable else BaseWidget()
        bodyWidget.setProperty("class", "Body")
        bodyWidget.setContentsMargins(0, 0, 0, 0)
        bodyWidget.setSpacing(0)
        bodyWidget.addWidget(widget)
        
        self.addWidget(titleArea)
        self.addWidget(bodyWidget)
    
    def setTitle(self, text: str):
        if isinstance(self.titleWidget, QLabel):
            self.titleWidget.setText(text)


class FontEditor(IconToolBarOption):
    def __init__(self):
        super().__init__()
        
        self.font_display_label = QLabel()
        self.font_display_label.setStyleSheet("background: none;")
        
        content_widget = TabView(
            {
                "FONT": self.getFontSection(),
                "OUTLINE": self.getOutlineSection(),
                "SHADOW": self.getShadowSection(),
                "MARGINS": self.getMarginSection(),
                "FORMAT": self.getFormatSection()
            }
        )
        content_widget.setProperty("class", "Section")
        
        self.initialize(content_widget, title=self.font_display_label)
        
        self.font_cb.currentFontChanged.connect(self.fontFamilyChanged)
        self.s_sb.valueChanged.connect(self.fontSizeChanged)
        self.ls_sb.valueChanged.connect(self.fontLetterSpacingChanged)
        self.o_slider.valueChanged.connect(lambda v: self.o_sb.setValue(v))
        self.o_sb.valueChanged.connect(lambda v: self.o_slider.setValue(v))
        self.o_sb.valueChanged.connect(self.fontOpacityChanged)
        self.st_cb.currentIndexChanged.connect(self.fontStyleChanged)
        self.ul_cb.clicked.connect(lambda s: self.fontLineStyleChanged(s, False))
        self.ol_cb.clicked.connect(lambda s: self.fontLineStyleChanged(False, s))
        self.c_cb.colorSelected.connect(self.fontColorChanged)
        
        self.fontFamilyChanged(self.font_cb.currentFont())
        self.fontSizeChanged(self.s_sb.value())
        self.fontLetterSpacingChanged(self.ls_sb.value())
        self.fontStyleChanged(0)
        self.fontOpacityChanged(self.o_sb.value())
        self.fontLineStyleChanged(self.ul_cb.isChecked(), self.ol_cb.isChecked())
        self.fontColorChanged(self.c_cb.currentColor())
    
    def fontFamilyChanged(self, font: QFont):
        family = font.family()
        
        f = self.font_display_label.font()
        f.setFamily(family)
        
        self.font_display_label.setText(family)
        self.setStyleProperty(self.font_display_label, "font-family", f"'{family}'")
    
    def fontSizeChanged(self, size: int):
        font = self.font_display_label.font()
        
        font.setPointSize(size)
        
        self.setStyleProperty(self.font_display_label, "font-size", f"{size}px")
    
    def fontOpacityChanged(self, opacity: int):
        self.setStyleProperty(self.font_display_label, "opacity", str(opacity))
    
    def fontStyleChanged(self, index: int):
        font = self.font_display_label.font()
        
        match index:
            case 0:
                font.setBold(False)
                font.setItalic(False)
                self.setStyleProperty(self.font_display_label, "font-style", "normal")
                self.setStyleProperty(self.font_display_label, "font-weight", "normal")
            case 1:
                font.setBold(True)
                font.setItalic(False)
                self.setStyleProperty(self.font_display_label, "font-style", "normal")
                self.setStyleProperty(self.font_display_label, "font-weight", "bold")
            case 2:
                font.setBold(False)
                font.setItalic(True)
                self.setStyleProperty(self.font_display_label, "font-style", "italic")
                self.setStyleProperty(self.font_display_label, "font-weight", "normal")
            case 3:
                font.setBold(True)
                font.setItalic(True)
                self.setStyleProperty(self.font_display_label, "font-style", "italic")
                self.setStyleProperty(self.font_display_label, "font-weight", "bold")
    
    def fontLineStyleChanged(self, underline: bool, overline: bool):
        font = self.font_display_label.font()
        
        font.setOverline(overline)
        font.setUnderline(underline)
        
        self.setStyleProperty(self.font_display_label, "text-decoration", "underline" if underline else ("overline" if overline else "none"))
        
        if underline:
            self.ol_cb.blockSignals(True)
            self.ol_cb.setChecked(False)
            self.ol_cb.blockSignals(False)
        elif overline:
            self.ul_cb.blockSignals(True)
            self.ul_cb.setChecked(False)
            self.ul_cb.blockSignals(False)
    
    def fontColorChanged(self, color: str):
        self.setStyleProperty(self.font_display_label, "color", color)
    
    def fontLetterSpacingChanged(self, spacing: float):
        font = self.font_display_label.font()
        
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        self.setStyleProperty(self.font_display_label, "letter-spacing", f"{spacing}px")
    
    def getFontSection(self):
        font_section = BaseWidget()
        font_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        f_widget = BaseWidget() ; f_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        self.font_cb = QFontComboBox()
        self.s_sb = QSpinBox() ; self.s_sb.setValue(self.font_display_label.font().pointSize())
        self.ls_sb = QSpinBox() ; self.ls_sb.setValue(int(self.font_display_label.font().letterSpacing()))
        self.c_cb = ColorComboBox("white")
        self.st_cb = QComboBox() ; self.st_cb.addItems(["Regular", "Bold", "Italic", "Bold Italic"])
        uss_widget = BaseWidget(QHBoxLayout) ; uss_widget.setContentsMargins(0, 5, 0, 5)
        uss_widget.addWidget(ul_cb := QCheckBox("Underline"))
        uss_widget.addWidget(ol_cb := QCheckBox("Overline"))
        o_widget = BaseWidget(QHBoxLayout)
        o_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        o_widget.setContentsMargins(0, 0, 0, 0)
        o_widget.addWidget(o_slider := QSlider(Qt.Orientation.Horizontal)) ; o_slider.setMaximum(100) ; o_slider.setValue(100)
        o_widget.addWidget(o_sb := QSpinBox()) ; o_sb.setMaximum(100) ; o_sb.setValue(100)
        self.o_slider = o_slider
        self.o_sb = o_sb
        self.ul_cb = ul_cb
        self.ol_cb = ol_cb
        
        f_widget.addWidget(LabeledWidget("Font Name", self.font_cb))
        f_widget.addWidget(LabeledWidget("Size", self.s_sb))
        f_widget.addWidget(LabeledWidget("Letter Spacing", self.ls_sb))
        f_widget.addWidget(LabeledWidget("Color", self.c_cb))
        f_widget.addWidget(LabeledWidget("Style", self.st_cb))
        f_widget.addWidget(uss_widget)
        f_widget.addWidget(LabeledWidget("Opacity", o_widget))
        
        # -----------------------------------------------------------------------------------------------------------
        
        a_widget = BaseWidget() ; a_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        ta_cb = QComboBox() ; ta_cb.addItems(["Left", "Center", "Right"])
        va_cb = QComboBox() ; va_cb.addItems(["Left", "Center", "Right"])
        
        a_widget.addWidget(LabeledWidget("Text Alignment", ta_cb))
        a_widget.addWidget(LabeledWidget("Vertical Alignment", va_cb))
        
        # -----------------------------------------------------------------------------------------------------------
        
        font_section.addWidget(SeparatorLabel("Font"))
        font_section.addWidget(f_widget)
        font_section.addWidget(SeparatorLabel("Alignment"))
        font_section.addWidget(a_widget)
        font_section.addStretch()
        
        return font_section
    
    def getOutlineSection(self):
        outline_section = BaseWidget()
        outline_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        ou_widget = BaseWidget() ; ou_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        s_cb = QComboBox() ; s_cb.addItems(["None", "Outer", "Center", "Inner"])
        c_ccb = ColorComboBox("black")
        j_cb = QComboBox() ; j_cb.addItems(["Round", "Square", "Bevel"])
        s_widget = BaseWidget(QHBoxLayout)
        s_widget.addWidget(s_slider := QSlider(Qt.Orientation.Horizontal))
        s_widget.addWidget(s_sb := QSpinBox())
        o_widget = BaseWidget(QHBoxLayout)
        o_widget.addWidget(o_slider := QSlider(Qt.Orientation.Horizontal))
        o_widget.addWidget(o_sb := QSpinBox())
        
        ou_widget.addWidget(LabeledWidget("Style", s_cb))
        ou_widget.addWidget(LabeledWidget("Color", c_ccb))
        ou_widget.addWidget(LabeledWidget("Join", j_cb))
        ou_widget.addWidget(LabeledWidget("Size", s_widget))
        ou_widget.addWidget(LabeledWidget("Opacity", o_widget))
        
        # -----------------------------------------------------------------------------------------------------------
        
        outline_section.addWidget(SeparatorLabel("Outline"))
        outline_section.addWidget(ou_widget)
        outline_section.addStretch()
        
        return outline_section
    
    def getShadowSection(self):
        shadow_section = BaseWidget()
        shadow_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        sh_widget = BaseWidget() ; sh_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        s_cb = QComboBox() ; s_cb.addItems(["None", "Outer", "Center", "Inner"])
        c_ccb = ColorComboBox("black")
        a_widget = BaseWidget(QHBoxLayout) ; a_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        a_widget.addWidget(a_dial := QDial())
        a_widget.addWidget(a_sb := QSpinBox())
        off_widget = BaseWidget(QHBoxLayout)
        off_widget.addWidget(off_slider := QSlider(Qt.Orientation.Horizontal))
        off_widget.addWidget(off_sb := QSpinBox())
        b_widget = BaseWidget(QHBoxLayout)
        b_widget.addWidget(b_slider := QSlider(Qt.Orientation.Horizontal))
        b_widget.addWidget(b_sb := QSpinBox())
        o_widget = BaseWidget(QHBoxLayout)
        o_widget.addWidget(o_slider := QSlider(Qt.Orientation.Horizontal))
        o_widget.addWidget(o_sb := QSpinBox())
        
        sh_widget.addWidget(LabeledWidget("Style", s_cb))
        sh_widget.addWidget(LabeledWidget("Color", c_ccb))
        sh_widget.addWidget(LabeledWidget("Angle", a_widget))
        sh_widget.addWidget(LabeledWidget("Offset", off_widget))
        sh_widget.addWidget(LabeledWidget("Blur", b_widget))
        sh_widget.addWidget(LabeledWidget("Opacity", o_widget))
        
        # -----------------------------------------------------------------------------------------------------------
        
        shadow_section.addWidget(SeparatorLabel("Shadow"))
        shadow_section.addWidget(sh_widget)
        shadow_section.addStretch()
        
        return shadow_section
    
    def getMarginSection(self):
        margins_section = BaseWidget()
        margins_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        m_widget = BaseWidget() ; m_widget.setSpacing(10)
        
        m_widget.addWidget(LabeledWidget(LabeledWidget("Left", l_sb := QSpinBox()), LabeledWidget("Top", t_sb := QSpinBox())))
        m_widget.addWidget(LabeledWidget(LabeledWidget("Right", r_sb := QSpinBox()), LabeledWidget("Bottom", b_sb := QSpinBox())))
        
        # -----------------------------------------------------------------------------------------------------------
        
        margins_section.addWidget(SeparatorLabel("Margins"))
        margins_section.addWidget(m_widget)
        margins_section.addStretch()
        
        return margins_section
    
    def getFormatSection(self):
        format_section = BaseWidget()
        format_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        as_widget = BaseWidget()
        
        as_widget.addWidget(dnast_rb := QRadioButton("Do not auto size text"))
        as_widget.addWidget(rttfe_rb := QRadioButton("Resize text to fit element"))
        ntsas_widget = BaseWidget() ; ntsas_widget.addWidget(ntsas_cb := QCheckBox("Normalize text size across slides"))
        
        # -----------------------------------------------------------------------------------------------------------
        
        fmt_widget = BaseWidget()
        
        fmt_widget.addWidget(ww_cb := QCheckBox("Word Wrapping"))
        fmt_widget.addWidget(caw_cb := QCheckBox("Capitalize all words"))
        fmt_widget.addWidget(cfwoel_cb := QCheckBox("Capitalize first word of each line"))
        fmt_widget.addWidget(acfcotw_cb := QCheckBox("Automatically capitalize first character of these words"))
        acfcotw_widget = BaseWidget() ; acfcotw_widget.addWidget(acfcotw_te := QTextEdit())
        fmt_widget.addWidget(acfcotw_widget)
        
        # -----------------------------------------------------------------------------------------------------------
        
        format_section.addWidget(SeparatorLabel("Auto Sizing"))
        format_section.addWidget(as_widget)
        format_section.addWidget(SeparatorLabel("Formatting"))
        format_section.addWidget(fmt_widget)
        format_section.addStretch()
        
        return format_section

class ColorComboBox(IconToolBarOption):
    colorSelected = pyqtSignal(str)
    
    def __init__(self, color: QColor | str):
        super().__init__()
        
        color = QColor(color)
        
        wrapper_widget = BaseWidget(QHBoxLayout)
        wrapper_widget.setSpacing(5)
        wrapper_widget.setContentsMargins(0, 0, 0, 0)
        
        self.selected_color_display = QWidget()
        self.selected_color_display.setFixedSize(20, 20)
        
        self.selected_color_hex_label = QLabel()
        self.selected_color_hex_label.setStyleSheet("font-family: consolas; font-size: 15px;")
        
        wrapper_widget.addWidget(self.selected_color_display)
        wrapper_widget.addWidget(self.selected_color_hex_label)
        
        color_picker = QColorDialog()
        color_picker.currentColorChanged.connect(self._setColor)
        
        self._is_init = True
        self._setColor(color)
        self._is_init = False
        
        self.initialize(color_picker, title=wrapper_widget, font_size=10)
        
        self.setContentsMargins(5, 5, 5, 5)
    
    def currentColor(self):
        return self._color
    
    def _colorToHex(self, color: QColor):
        r = hex(color.red()).replace("0x", "")
        g = hex(color.green()).replace("0x", "")
        b = hex(color.blue()).replace("0x", "")
        
        return f"#{"0" + r if len(r) == 1 else r}{"0" + g if len(g) == 1 else g}{"0" + b if len(b) == 1 else b}"
    
    def _setColor(self, color: QColor):
        color = self._colorToHex(color)
        
        self.selected_color_hex_label.setText(color)
        self.selected_color_display.setStyleSheet(f"background-color: {color};")
        
        if not self._is_init:
            self.colorSelected.emit(color)
        
        self._color = color



class ExportsEditorDialogWidget(BaseDialogWidget):
    def __init__(self):
        super().__init__("Export Editor", BaseWidget)
        
        self.export_mode = 0
        self._initGeometry()
        
        self.setProperty("class", "ExportEditor")
        
        main_widget = BaseScrollWidget()
        main_widget.setProperty("class", "ExportEditorOptionsBG")
        
        e_widget = BaseWidget() ; e_widget.setContentsMargins(35, 0, 35, 0)
        et_widget = BaseWidget(QHBoxLayout) ; et_widget.setSpacing(50)
        et_widget.addWidget(s_rb := QRadioButton("School")) ; s_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        et_widget.addWidget(l_rb := QRadioButton("Level")) ; l_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        et_widget.addWidget(c_rb := QRadioButton("Class")) ; c_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        s_rb.clicked.connect(lambda b: path_edit.setPlaceholderText("School Export File Path" if b else path_edit.placeholderText()))
        l_rb.clicked.connect(lambda b: path_edit.setPlaceholderText("Level Export Folder Path" if b else path_edit.placeholderText()))
        c_rb.clicked.connect(lambda b: path_edit.setPlaceholderText("Class Export Folder Path" if b else path_edit.placeholderText()))
        e_widget.addWidget(et_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        e_widget.addWidget(LabeledWidget("Export File Type", eft_cb := QComboBox())) ; eft_cb.addItems(["PNG", "JPG", "HTML", "PDF", "MSIX"])
        s_rb.clicked.connect(lambda b: self._set_export_mode(0 if b else self.export_mode))
        l_rb.clicked.connect(lambda b: self._set_export_mode(1 if b else self.export_mode))
        c_rb.clicked.connect(lambda b: self._set_export_mode(2 if b else self.export_mode))
        self.eft_cb = eft_cb
        
        f_widget = BaseWidget() ; f_widget.setContentsMargins(35, 0, 35, 0)
        f_widget.addWidget(LabeledWidget("Title", title_font := FontEditor()))
        f_widget.addWidget(LabeledWidget("Timetable Title", tt_font := FontEditor()))
        f_widget.addWidget(LabeledWidget("Timetable Content", tc_font := FontEditor()))
        f_widget.addWidget(LabeledWidget("Break", b_font := FontEditor()))
        
        t_widget = BaseWidget() ; t_widget.setContentsMargins(35, 0, 35, 0)
        t_widget.addWidget(LabeledWidget("Weekday Background Color", wb_color := ColorComboBox("black")))
        t_widget.addWidget(LabeledWidget("Timetable Background Color", ttbl_bg_color := ColorComboBox("black")))
        t_widget.addWidget(LabeledWidget("Break Background Color", b_bg_color := ColorComboBox("black")))
        t_widget.addWidget(LabeledWidget("Border Color", b_color := ColorComboBox("white")))
        thickness_widget = BaseWidget()
        thickness_widget.addWidget(t_l1_widg := LabeledWidget("  Vertical Line Thickness", vlt_sb := QSpinBox())) ; t_l1_widg.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        thickness_widget.addWidget(t_l2_widg := LabeledWidget("Horizontal Line Thickness", hlt_sb := QSpinBox())) ; t_l2_widg.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        t_widget.addWidget(thickness_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_widget.addWidget(SeparatorLabel("Export"))
        main_widget.addWidget(e_widget)
        main_widget.addWidget(SeparatorLabel("Fonts"))
        main_widget.addWidget(f_widget)
        main_widget.addWidget(SeparatorLabel("Table"))
        main_widget.addWidget(t_widget)
        
        base_widget = BaseWidget(QHBoxLayout)
        
        preview = QCheckBox("Preview Output")
        export_button = QPushButton("Export") ; export_button.clicked.connect(self.export)
        cancel_button = QPushButton("Cancel") ; cancel_button.clicked.connect(self.close)
        
        base_widget.addWidget(preview)
        base_widget.addStretch()
        base_widget.addWidget(path_edit := QLineEdit(), alignment=Qt.AlignmentFlag.AlignBottom)
        base_widget.addWidget(export_button, alignment=Qt.AlignmentFlag.AlignBottom)
        base_widget.addWidget(cancel_button, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.path_edit = path_edit
        self.path_edit.setPlaceholderText("Export File Path")
        self.path_edit.setFixedWidth(400)
        
        s_rb.setChecked(True)
        
        self.addWidget(main_widget)
        self.addWidget(base_widget)
    
    def _initGeometry(self):
        self.setMinimumSize(800, 550)
        
        screen_geom = self.screen().geometry()
        
        self.setGeometry(int(screen_geom.width() / 2 - self.geometry().width() / 2), int(screen_geom.height() / 2 - self.geometry().height() / 2), self.geometry().width(), self.geometry().height())
    
    def _set_export_mode(self, mode: int):
        self.export_mode = mode
    
    def export(self):
        path = self.path_edit.text()
        file_type = self.eft_cb.currentText().lower()
        
        if self.export_mode == 0:
            if file_type == "html":
                body = ""
                for _, cls_level in SCHOOL.class_levels:
                    for cls in cls_level.classes.values():
                        body += get_export_html_text(cls)
                    
                html = HTML_TEXT.format(title="School", body=body)
                
                with open(path, "w") as file:
                    file.write(html)
            elif file_type == "png":
                surfs: list[pygame.Surface] = []
                
                width = 0
                height = 0
                
                for _, cls_level in SCHOOL.class_levels:
                    for cls in cls_level.classes.values():
                        cls_surf = get_export_surface(cls)
                        
                        width = max(width, cls_surf.get_width())
                        height += cls_surf.get_height()
                        
                        surfs.append(cls_surf)
                
                screen = pygame.Surface((width, height))
                screen.fill("white")
                
                y = 0
                for surf in surfs:
                    screen.blit(surf, ((0, y), surf.get_size()))
                    
                    y += surf.get_height()
                
                pygame.image.save(screen, path)
        elif self.export_mode == 1:
            if file_type == "html":
                for _, cls_level in SCHOOL.class_levels:
                    body = ""
                    
                    for cls in cls_level.classes.values():
                        body += get_export_html_text(cls)
                    
                    html = HTML_TEXT.format(title=cls_level.name.full(), body=body)
                    
                    with open(path + f"/{cls_level.name.full()}.html", "w") as file:
                        file.write(html)
            elif file_type == "png":
                for _, cls_level in SCHOOL.class_levels:
                    surfs: list[pygame.Surface] = []
                    
                    width = 0
                    height = 0
                    
                    for cls in cls_level.classes.values():
                        cls_surf = get_export_surface(cls)
                        
                        width = max(width, cls_surf.get_width())
                        height += cls_surf.get_height()
                        
                        surfs.append(cls_surf)
                    
                    screen = pygame.Surface((width, height))
                    screen.fill("white")
                    
                    y = 0
                    for surf in surfs:
                        screen.blit(surf, ((0, y), surf.get_size()))
                        
                        y += surf.get_height()
                    
                    pygame.image.save(screen, path + f"/{cls_level.name.full()}.png")
        elif self.export_mode == 2:
            if file_type == "html":
                for _, cls_level in SCHOOL.class_levels:
                    for cls in cls_level.classes.values():
                        body = get_export_html_text(cls)
                        html = HTML_TEXT.format(title=f"{cls_level.name.full()} {cls.name}", body=body)
                        
                        with open(path + f"/{cls_level.name.full()} {cls.name}.html", "w") as file:
                            file.write(html)
            elif file_type == "png":
                for _, cls_level in SCHOOL.class_levels:
                    for cls in cls_level.classes.values():
                        pygame.image.save(get_export_surface(cls), path + f"/{cls.level.name.full()} {cls.name}.png")
    






