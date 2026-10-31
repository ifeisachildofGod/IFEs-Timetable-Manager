
import time

from utils import *
from imports import *

from .base import *

import math


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
    textChanged = pySignal(int)
    
    def __init__(self, number: int, min_validatorAmt: int = 0, max_validatorAmt: int = 10):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "NumberLineEdit")
        
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
    mouseclicked = pySignal()
    
    def __init__(self, angle: int = 0, parent=None):
        super().__init__("▼", parent)
        
        self.setProperty("class", "Arrow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.angle = angle
    
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




class CustomTitleBar(BaseWidget):
    def __init__(self, get_search_scope_func: Callable, goto_search_func: Callable):
        super().__init__(QHBoxLayout)

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
        self.search_bar = SearchBar(get_search_scope_func, goto_search_func)
        self.center_widget.addWidget(self.search_bar)
        
        # Right widget
        # Nothing here
        
        self.addWidget(self.left_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        self.addWidget(self.center_widget)
        self.addWidget(right_widget, alignment=Qt.AlignmentFlag.AlignRight)

class MainTitleBar(CustomTitleBar):
    def __init__(self, menu_bar: QMenuBar, get_search_scope_func: Callable, goto_search_func: Callable, go_back_func: Callable, go_forward_func: Callable):
        super().__init__(get_search_scope_func, goto_search_func)
        
        menu_bar.setFixedHeight(40)
        menu_bar.setContentsMargins(0, 0, 0, 0)
        menu_bar.setStyleSheet("QMenuBar {background-color: transparent; border: none;}")
        
        self.left_widget.addWidget(menu_bar)
        
        self.go_back_svg = SvgWidget("src/images/svg/direction.svg")
        self.go_back_svg.set_all_colors(THEME_MANAGER.process_stylesheet("{text}"))
        self.go_back_button = BaseWidget()
        self.go_back_button.setProperty("class", "SpecialBG1Hover NoBG BorderRadiused")
        self.go_back_button.clicked.connect(go_back_func)
        self.go_back_button.addWidget(self.go_back_svg)
        
        self.go_forward_svg = SvgWidget("src/images/svg/direction.svg")
        self.go_forward_svg.set_all_colors(THEME_MANAGER.process_stylesheet("{text}"))
        self.go_forward_svg.rotate(180)
        self.go_forward_button = BaseWidget()
        self.go_forward_button.setProperty("class", "SpecialBG1Hover NoBG BorderRadiused")
        self.go_forward_button.clicked.connect(go_forward_func)
        self.go_forward_button.addWidget(self.go_forward_svg)
        
        self.center_widget.insertWidget(0, self.go_back_button)
        self.center_widget.insertWidget(1, self.go_forward_button)

class WidgetDropdown(BaseWidget):
    def __init__(self, title: str, widget: BaseWidget | QWidget):
        super().__init__()
        
        self.widget = widget
        self._disabled = False
        
        self.setSpacing(0)
        
        self.setProperty("class", "Bordered")
        self.setProperty("class", "BorderRadiused")
        self.setProperty("class", "DropdownCheckboxes")
        
        self.header = BaseWidget(QHBoxLayout)
        self.header.setProperty("class", "DPC_Header")
        self.header.setFixedHeight(50)
        self.header.setContentsMargins(12, 0, 12, 0)
        self.header.clicked.connect(self.tdp_event_func)
        
        self.toogle_icon = ArrowWidget(270)
        self.toogle_icon.setProperty("class", "Arrow")
        self.toogle_icon.setContentsMargins(0, 0, 10, 0)
        self.toogle_icon.mouseclicked.connect(self.toogle)
        
        self.title_label = QLabel(title)
        
        self.header.addWidget(self.toogle_icon)
        self.header.addWidget(self.title_label)
        self.header.addStretch()
        
        self.addWidget(self.header)
        self.addWidget(self.widget)
        
        self.widget.setVisible(False)
    
    def tdp_event_func(self, a0: QMouseEvent | None):
        if a0.button() == Qt.MouseButton.LeftButton and not self._disabled:
            self.toogle()
    
    def toogle(self):
        self.toogle_icon.setAngle(0 if self.toogle_icon.angle != 0 else 270)
        self.widget.setVisible(not self.widget.isVisible())
    
    def beDisabled(self, a0: bool, close_true_open_false=None):
        if a0:
            if close_true_open_false is not None:
                if close_true_open_false == self.widget.isVisible():
                    self.toogle()
            
            self._disabled = True
        else:
            self._disabled = False
    
    def setOpen(self, state: bool):
        if state != self.widget.isVisible():
            self.toogle()

class EditableCancelableEntry(BaseWidget):
    deleted = pySignal()
    started_editing_signal = pySignal()
    finished_editing_signal = pySignal()
    
    def __init__(self, initial_text: str | None = None):
        super().__init__(QHBoxLayout)
        
        self.enableCursorPointing()
        self.setProperty("class", "OptionTag")
        
        self.text = initial_text if initial_text is not None else ""
        self.is_editing = False
        
        self.setContentsMargins(4, 5, 4, 5)
        self.setSpacing(4)
        
        # Input mode widgets
        self.input = QLineEdit()
        self.input.setProperty("class", "OptionEdit")
        self.input.setText(f"<span>{"<br>".join(wrapify_text(self.text, 10))}</span>")
        self.input.setPlaceholderText("Enter option")
        self.input.setFixedWidth(110)  # Fix input width
        self.input.returnPressed.connect(self.input.clearFocus)
        self.input.editingFinished.connect(self.finish_editing)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setProperty("class", "SettingEntryClose")
        self.close_btn.clicked.connect(self.remove)
        
        self.deleted.connect(self.deleteLater)
        self.started_editing_signal.connect(self.start_editing)
        self.finished_editing_signal.connect(self._finished_editing)
        
        # Label mode widget
        self.label = QLabel(self.text)
        self.label.setMinimumWidth(110)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.mousePressEvent = lambda _: self.started_editing_signal.emit()
        
        # Initialize both widgets but hide input initially
        self.addWidget(self.label)
        self.addWidget(self.input)
        self.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.input.hide()
        
        self.setFixedWidth(140)
        
        self.set_text(self.text)
    
    def _finished_editing(self):
        if self.is_editing:
            self.text = self.input.text().strip()
            
            self.is_editing = False
            self.setup_display_mode()
            self.set_text(self.text)
    
    def set_text(self, text: str):
        self.label.setText(f"<span>{"<br>".join(wrapify_text(text, 15))}</span>")
    
    def setup_display_mode(self):
        self.label.show()
        self.input.hide()
        self.close_btn.show()
    
    def setup_edit_mode(self):
        self.label.setVisible(False)
        self.input.setVisible(True)
        self.close_btn.setVisible(True)
    
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



class SeperatorWidget(BaseWidget):
    def __init__(self, orientation: Qt.Orientation, spacing: int, width: Optional[int] = None, height: Optional[int] = None):
        super().__init__()
        
        x_spacing = spacing // 2 if orientation == Qt.Orientation.Vertical else 0
        y_spacing = spacing // 2 if orientation == Qt.Orientation.Horizontal else 0
        
        self.setContentsMargins(x_spacing, y_spacing, x_spacing, y_spacing)
        
        widget = BaseWidget()
        
        if width:
            widget.setFixedWidth(width)
        if height:
            widget.setFixedHeight(height)
        
        widget.setStyleSheet(f"background-color: {THEME_MANAGER.process_stylesheet("{interpolate-black-0.98__maximum}")};")
        
        self.addWidget(widget)

class SeparatorLabel(BaseWidget):
    def __init__(self, text: str):
        super().__init__(QHBoxLayout)
        
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(text)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        label.setContentsMargins(0, 0, 5, 0)
        self.static_setStyleProperty(label, "font-weight", "bold")
        
        sep_widget = SeperatorWidget(Qt.Orientation.Horizontal, 0, None, 1)
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
            content: Callable | list[tuple[str, Callable | dict[str, Callable] | tuple[Callable, Callable]]] | BaseWidget,
            title: Optional[str | QLabel] = None,
            font_size: Optional[int] = None,
            show_dp_icon: bool = False,
            default_bg: str = None
        ):
        self._first_press = True
        
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
                    background-color: {default_bg or "transparent"};
                }}}}
                
                QWidget.IconToolBarOption QWidget._TopWidget QLabel.TitleLabel {{{{
                    background: none;
                    font-size: {font_size}px;
                }}}}
                QWidget.IconToolBarOption QLabel {{{{
                    color: {{text}};
                    font-size: {font_size}px;
                    background-color: transparent;
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
        
        if title is not None:
            self.addWidget(title_label)
        
        self.getWidget().mousePressEvent = self._clicked
        
        if not isinstance(self.content, Callable) and not isinstance(self.content, list):
            self.content.setProperty("class", "Bordered")
            self.content.hideEvent = lambda _: self._disappear()
    
    def disappear(self):
        self._disappear()
        self.content.hide()
    
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
    
    def _disappear(self):
        self.setStyleSheet(self.STYLESHEET)
        self.update()
        
        if self.arrow:
            self.arrow.setAngle(270)
    
    def _clicked(self, a0):
        if isinstance(self.content, Callable):
            return self.content()
        
        self.setStyleSheet(self.STYLESHEET.replace(self.HOVER_STYLESHEET, "") + THEME_MANAGER.process_stylesheet("QWidget.IconToolBarOption {{ background-color: {hover__bg3} }}"))
        self.update()
        
        if self.arrow:
            self.arrow.setAngle(0)
        
        if isinstance(self.content, list):
            menu = self._getMenu(self, self.content)
            
            menu.adjustSize()
            menu.exec(self.getMenuPosition(menu))
            
            self.setStyleSheet(self.STYLESHEET)
            self.update()
        elif isinstance(self.content, QWidget):
            self.content.setWindowFlags(Qt.WindowType.Popup)
            
            if not self._first_press:
                self.content.move(self.getMenuPosition(self.content))
            
            self.content.show()
            
            if self._first_press:
                QTimer.singleShot(0, lambda: self.content.move(self.getMenuPosition(self.content)))
                
                self._first_press = False
    
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

class GeneralPeriodEditor(BaseWidget):
    periodChanged = pySignal(Period)
    
    def __init__(self, window: QMainWindow, period: Optional[Period] = None, min_period: Optional[Period] = None, max_period: Optional[Period] = None):
        super().__init__()
        
        self.__init = True
        
        self.setContentsMargins(5, 5, 5, 5)
        self.setProperty("class", "BorderRadiused BG2")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        self._window = window
        
        min_year = 1982
        max_year = Period.str_to_period(time.ctime()).year + 200
        
        self._default_min_period = Period(Time(0, 0, 1), "Monday", 1, "January", min_year - 1)
        self._default_max_period = Period(Time(23, 59, 59), "Monday", 1, "January", max_year + 1)
        
        self.min_period = min_period or self._default_min_period.copy()
        self.max_period = max_period or self._default_max_period.copy()
        
        self.period = period
        if self.period is None:
            self.period = Period.str_to_period(time.ctime())
            self.period.time = Time(0, 0, 0)
        
        self._prev_day_amt = self.period.in_days()
        
        self.day_label = QLabel(self.period.day)
        self.day_label.setStyleSheet("QLabel {padding: 6px}")
        self.day_label.setProperty("class", "Bordered BorderRadiused")
        
        self.date_sb = QSpinBox()
        self.month_cb = QComboBox()
        self.year_sb = QSpinBox()
        
        self.date_sb.setMinimum(1)
        self.month_cb.addItems(list(MONTHS_OF_THE_YEAR))
        self.year_sb.setRange(min_year, max_year)
        
        self.date_sb.setValue(self.period.date)
        self.month_cb.setCurrentText(self.period.month)
        self.year_sb.setValue(self.period.year)
        
        self.date_sb.valueChanged.connect(self._date_value_changed)
        self.month_cb.currentTextChanged.connect(self._month_text_changed)
        self.year_sb.valueChanged.connect(self._year_value_changed)
        
        self._year_value_changed(self.year_sb.value())
        self._month_text_changed(self.month_cb.currentText())
        self._date_value_changed(self.date_sb.value())
        
        self.addWidget(top_widget := BaseWidget(QHBoxLayout))
        self.addWidget(bottom_widget := BaseWidget(QHBoxLayout))
        
        top_widget.setProperty("class", "NoBG")
        bottom_widget.setProperty("class", "NoBG")
        
        top_widget.addWidget(self.date_sb)
        top_widget.addWidget(self.day_label)
        
        bottom_widget.addWidget(self.month_cb)
        bottom_widget.addWidget(self.year_sb)
        
        self.__init = False
    
    def update_inputs(self):
        if self.period.in_seconds() > self.max_period.in_seconds():
            self.year_sb.setValue(self.max_period.year)
            self.month_cb.setCurrentText(self.max_period.month)
            self.date_sb.setValue(self.max_period.date)
        elif self.period.in_seconds() < self.min_period.in_seconds():
            self.year_sb.setValue(self.min_period.year)
            self.month_cb.setCurrentText(self.min_period.month)
            self.date_sb.setValue(self.min_period.date)
    
    def _date_value_changed(self, date: int):
        prev_date = self.period.date
        self.period.date = date
        
        if not (self.min_period.in_seconds() <= self.period.in_seconds() <= self.max_period.in_seconds()):
            self.date_sb.setValue(prev_date)
        
        dodw_index = DAYS_OF_THE_WEEK.index(self.period.day)
        day_diff = int(self.period.in_days() - self._prev_day_amt)
        
        self.period.day = DAYS_OF_THE_WEEK[(dodw_index + day_diff) % len(DAYS_OF_THE_WEEK)]
        
        self.day_label.setText(self.period.day)
        
        self.date_sb.setSuffix(positionify(self.period.date)[-2:])
        
        self._prev_day_amt = self.period.in_days()
        
        self.periodChanged.emit(self.period)
        
        if not self.__init:
            self._window.saved_state_changed.emit(True)
    
    def _month_text_changed(self, month: str):
        prev_month = self.period.month
        self.period.month = month
        
        if not (self.min_period.in_seconds() <= self.period.in_seconds() <= self.max_period.in_seconds()):
            self.month_cb.setCurrentText(prev_month)
        
        self.date_sb.setMaximum(MONTHS_OF_THE_YEAR[month] + (1 if month == "February" else 0))
        
        self._date_value_changed(self.date_sb.value())
    
    def _year_value_changed(self, year: int):
        prev_year = self.period.year
        self.period.year = year
        
        if not (self.min_period.in_seconds() <= self.period.in_seconds() <= self.max_period.in_seconds()):
            self.year_sb.setValue(prev_year)
        
        self._month_text_changed(self.month_cb.currentText())
        
        if self.period.year % 4 == 0 and self.month_cb.currentText() == "February":
            self.date_sb.setMaximum(MONTHS_OF_THE_YEAR[self.month_cb.currentText()] + 1)
        
        self._date_value_changed(self.date_sb.value())


