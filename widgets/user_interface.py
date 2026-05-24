
from imports import *
from widgets.base_widgets import *

import math
from typing import TypeVar

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
        super().__init__()
        
        self._min_num = min_validatorAmt
        self._max_num = max_validatorAmt
        
        self.edit = QLineEdit()
        self.edit.textChanged.connect(self._updateNumber)
        self.edit.setValidator(QIntValidator())
        self.setNumber(number)
        
        self.min_num = self._min_num
        self.max_num = self._max_num
        
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout()
        
        buttons_widget.setStyleSheet("background: none;")
        buttons_widget.setLayout(buttons_layout)
        
        self.addWidget(self.edit, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        self.addWidget(buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        increment_button = ArrowWidget(180)
        increment_button.setContentsMargins(0, 0, 0, 0)
        increment_button.mouseclicked.connect(lambda: self._incDecNumber(1))
        
        decrement_button = ArrowWidget(0)
        increment_button.setContentsMargins(0, 0, 0, 0)
        decrement_button.mouseclicked.connect(lambda: self._incDecNumber(-1))
        
        buttons_layout.addWidget(increment_button, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        buttons_layout.addWidget(decrement_button, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        
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
        self.setProperty("class", "Menu")
        self.setStyleSheet("QFrame.Menu { border: 1px solid "+ THEME_MANAGER.parse_stylesheet("{border2}") +"; }")
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

        self._updating = False

        # ---------- Layout ----------
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("Search")
        self.search_le.setFixedWidth(496)
        self.search_le.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        self.main_layout.addWidget(self.search_le, alignment=Qt.AlignmentFlag.AlignTop)

        self.options_widget = BaseScrollWidget()
        
        self.options_widget.setFixedWidth(496)
        self.options_widget.setFixedHeight(220)
        self.options_widget.setVisible(False)

        self.main_layout.addWidget(self.options_widget, alignment=Qt.AlignmentFlag.AlignTop)

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

        BaseWidget.static_clear_layout(self.options_layout)
        
        self.options_layout.addStretch()
        
        if not text:
            self.options_container.setVisible(False)
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

        added = 0
        for index, (data_point, (name, right, bottom, end), (score, indices)) in enumerate(score_data):
            if score == -1 or added >= self.MAX_RESULTS:
                continue

            label = QLabel(
                self._stylize_text_indices(
                    name,
                    f"color: {THEME_MANAGER.pallete_get("fg1")}; font-weight: bold;",
                    right,
                    bottom,
                    end,
                    indices
                )
            )
            label.setProperty("class", "QPushButton")
            label.mousePressEvent = self._make_option_clicked_func(data_point)
            
            self.options_layout.insertWidget(index, label, alignment=Qt.AlignmentFlag.AlignTop)
            added += 1
        
        self.options_container.setVisible(added > 0)
        
        self._updating = False
    
    def _make_option_clicked_func(self, data_point: T):
        def handler(_):
            self.hide()
            self.search_le.blockSignals(True)
            self.search_le.clear()
            self.search_le.blockSignals(False)

            if self.goto_search_callback:
                self.goto_search_callback(data_point)

        return handler
    
    def _score(
        self,
        text: str,
        potential_match: str,
        extra_text_data: Optional[tuple[Optional[str], Optional[str], Optional[str]]] = None,
        backgrounds_texts: Optional[list[Optional[str]]] = None
    ):
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
    
    def _stylize_text_indices(self, main_text: str, style: str, right_text: Optional[str], bottom_text: Optional[str], end_text: Optional[str], indices: tuple[list[int], list[int], list[int]]):
        main_indices, right_indices, bottom_indices, end_indices = indices
        
        text = f"""
        <table width="100%">
        <tr>
            <td align="left">
            {"".join([f"<span style='font-size: 23px; {f"{style}" if i in main_indices else ""}'>{c}</span>" for i, c in enumerate(main_text)])}
            <span>    </span>
            {"".join([f"<span style='color: grey; font-size: 18px; font-weight: 300; {f"{style}" if i in right_indices else ""}'>{c}</span>" for i, c in enumerate(right_text)]) if right_text else ""}
            <br>
            {"".join([f"<span style='color: grey; font-size: 15px; font-weight: 500; {f"{style}" if i in bottom_indices else ""}'>{c}</span>" for i, c in enumerate(bottom_text)]) if bottom_text else ""}
            </td>
            <td align="right">
            {"".join([f"<span style='color: lightgrey; font-size: 10px; font-weight: 300; {f"{style}" if i in end_indices else ""}'>{c}</span>" for i, c in enumerate(end_text)]) if end_text else ""}
            </td>
            <br>
        </tr>
        </table>
        """
        return text

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
        self.center_widget.setContentsMargins(60, 5, 60, 5)
        
        right_widget = BaseWidget(QHBoxLayout)
        right_widget.setProperty("class", "TitleBar")
        right_widget.setContentsMargins(60, 0, 0, 0)
        right_widget.setSpacing(0)
        
        # Center widget
        self.search_edit = SearchEdit(get_search_scope_func, goto_search_func)
        
        self.search_pb = QPushButton("Search Subjects")
        self.search_pb.setFixedWidth(self.search_edit.width())
        self.search_pb.setStyleSheet(f"background-color: {THEME_MANAGER.pallete_get("bg2")}; border: 1px solid {THEME_MANAGER.pallete_get("border1")};")
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



