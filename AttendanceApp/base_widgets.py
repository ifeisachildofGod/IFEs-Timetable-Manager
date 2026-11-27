
from .imports import *
from .extra_widgets import *
from .functions_and_uncategorized import *


_T = TypeVar("_T")


class BaseListWidget(QWidget):
    def __init__(self, scroll_area: QScrollArea) -> None:
        super().__init__()
        
        self.widgets: list[BaseAttendanceEntryWidget] = []
        self.scroll_area = scroll_area
        
        self.container = QWidget(self)
        self.main_layout = QVBoxLayout(self.container)
        self.container.setLayout(self.main_layout)
        
        self.main_layout.addStretch()
        
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.container)
        self.setLayout(self._layout)
    
    # Category name is here to avoid edge cases
    def addWidget(self, widget: "BaseAttendanceEntryWidget", category_name: str | None = None, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch, alignment)
        else:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch)
        
        widget.show()
        widget.adjustSize()
        
        self.widgets.append(widget)
    
    def getWidgets(self):
        return self.widgets

class BaseScrollListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        
        self.widgets: list[BaseAttendanceEntryWidget] = []
        
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        widget = QWidget()
        self.scroll_widget.setWidget(widget)
        self.main_layout = QVBoxLayout(widget)
        self.main_layout.setSpacing(20)
        self.main_layout.addStretch()
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._layout.addWidget(self.scroll_widget)
        
        self._scroll_delay = 0
        self._target_y = 0
        self._scroll_start = None
        self._focus_widget = None
        self._scroll_delta = None
        
        self.scroll_delay = 10
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._scrolling)
    
    def _scrolling(self):
        self._scroll_start += self._scroll_delta
        self.scroll_widget.verticalScrollBar().setValue(int(self._scroll_start))
        
        self.update()
        
        self._scroll_delay += 1
        if (self._target_y <= self._scroll_start - 100 and self._scroll_delta > 0) or (self._target_y >= self._scroll_start - 150 and self._scroll_delta < 0) or self._scroll_start - 50 <= self._target_y <= self._scroll_start + 50:
            self._scroll_delay = 0
            self.scroll_delay = 10
            self.scroll_timer.stop()
            
            self._focus_widget = None
            self._scroll_delta = None    
    
    def _scroll_to(self, widget: QWidget, is_first: bool):
        widget.ensurePolished()
        
        self._focus_widget = widget
        self._scroll_start = self.scroll_widget.verticalScrollBar().value()
        self._target_y = widget.y()
        
        if is_first:
            self.scroll_delay = 1
        
        self._scroll_delta = (widget.y() - self.scroll_widget.verticalScrollBar().value()) / self.scroll_delay
        
        self.scroll_timer.stop()
        self.scroll_timer.start(1)
    
    def scroll_to(self, widget: QWidget, msec: Optional[int] = None, is_first=False):
        QTimer.singleShot(
            msec or 0,
            lambda: self._scroll_to(widget, is_first)
        )
    
    def addWidget(self, widget: "BaseAttendanceEntryWidget", stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if alignment is not None:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch, alignment)
        else:
            self.main_layout.insertWidget(len(self.widgets), widget, stretch)
        
        self.widgets.append(widget)
    
    def getWidgets(self):
        return self.widgets

class BaseFilterCategoriesWidget(BaseListWidget):
    def __init__(self, scroll_area: QScrollArea):
        super().__init__(scroll_area)
        
        self.category_widgets = {}
        self.category_widgets_tracker = []
    
    def addWidget(self, widget: "BaseAttendanceEntryWidget", category_name: str | tuple[str, ...] | int, stretch: int = 0, alignment: Qt.AlignmentFlag = None):
        if isinstance(category_name, (str, int)):
            category_name = str(category_name)
            
            if category_name not in self.category_widgets:
                cat_widg = QWidget()
                cat_layout = QVBoxLayout()
                cat_widg.setLayout(cat_layout)
                
                self.category_widgets[category_name] = DropdownLabeledField(category_name, cat_widg)
                
                super().addWidget(self.category_widgets[category_name])
            
            if alignment is not None:
                self.category_widgets[category_name].addWidget(widget, stretch, alignment)
            else:
                self.category_widgets[category_name].addWidget(widget, stretch)
            
            self.category_widgets_tracker.append([self.category_widgets[category_name], widget])
        else:
            parent = super()
            widgs = self.category_widgets
            
            self.category_widgets_tracker.append([])
            
            for i, name in enumerate(category_name):
                name = str(name)
                
                if name not in widgs:
                    cat_widg = QWidget()
                    cat_layout = QVBoxLayout()
                    cat_widg.setLayout(cat_layout)
                    
                    widgs[name] = [DropdownLabeledField(name, cat_widg), {}]
                    
                    parent.addWidget(widgs[name][0], alignment=alignment)
                
                self.category_widgets_tracker[-1].append(widgs[name][0])
                
                if i != len(category_name) - 1:
                    parent = widgs[name][0]
                    widgs = widgs[name][1]
                else:
                    if alignment is not None:
                        widgs[name][0].addWidget(widget, stretch, alignment)
                    else:
                        widgs[name][0].addWidget(widget, stretch)
            
            self.category_widgets_tracker[-1].append(widget)
    
    def getWidgets(self):
        return self.category_widgets_tracker


class BaseDataDisplayWidget(BaseScrollListWidget):
    def __init__(self):
        super().__init__()
        
        self.scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.widgets = self._get_filter_widgets()
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not isinstance(staff_widget, tuple):
                staff_widget.setVisible(i == 0)
                self.main_layout.insertWidget(i, staff_widget)
        
        for i, staff_widget in enumerate(self.widgets.values()):
            if not i and isinstance(staff_widget, tuple):
                for k in staff_widget:
                    self.widgets[k].setVisible(True)
        
        filters = QComboBox()
        filters.addItems(list(self.widgets))
        filters.currentIndexChanged.connect(self.filter)
        
        self._layout.insertWidget(0, filters, alignment=Qt.AlignmentFlag.AlignRight)
    
    def _get_filter_widgets(self):
        raise NotImplementedError()
    
    @staticmethod
    def is_entry_countable(entry: AttendanceEntry, valid_days: list[str], timeline_dates: list[tuple[Period, Period]]):
        is_in_timeline = next((True for t_d in timeline_dates if t_d[0].in_minutes() <= entry.period.in_minutes() <= t_d[1].in_minutes()), False)
        
        return is_in_timeline and entry.is_check_in and entry.period.day in valid_days
    
    def filter(self, index: int):
        for i, staff_widget in enumerate(self.widgets.values()):
            if isinstance(staff_widget, tuple) and index == i:
                for k, w in self.widgets.items():
                    if not isinstance(w, tuple):
                        w.setVisible(k in staff_widget)
                
                break
            elif not isinstance(staff_widget, tuple):
                staff_widget.setVisible(index == i)



class _CharacterNameWidget(QWidget):
    def __init__(self, name: StaffName):
        super().__init__()
        self.name = name
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        widget_2_1 = QWidget()
        layout_2_1 = QVBoxLayout()
        widget_2_1.setLayout(layout_2_1)
        
        widget_2_1_1 = QWidget()
        layout_2_1_1 = QHBoxLayout()
        widget_2_1_1.setLayout(layout_2_1_1)
        layout_2_1.addWidget(widget_2_1_1)
        
        name_1 = LabeledField("Surname", QLabel(f"<span style='font-weight: bold'>{self.name.first}</span>"))
        name_2 = LabeledField("First name", QLabel(f"<span style='font-weight: bold'>{self.name.second}</span>"))
        
        layout_2_1_1.addWidget(name_1)
        layout_2_1_1.addWidget(name_2)
        
        widget_2_1_2 = QWidget()
        layout_2_1_2 = QHBoxLayout()
        widget_2_1_2.setLayout(layout_2_1_2)
        layout_2_1.addWidget(widget_2_1_2)
        
        name_4 = LabeledField("Other name", QLabel(f"<span style='font-weight: bold'>{self.name.third if self.name.third else "No other name"}</span>"))
        name_5 = LabeledField("Abbreviation", QLabel(f"<span style='font-weight: bold'>{self.name.abbrev if self.name.abbrev else "No abbreviatory name"}</span>"))
        
        layout_2_1_2.addWidget(name_4)
        layout_2_1_2.addWidget(name_5, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(LabeledField("Names", widget_2_1, height_policy=QSizePolicy.Policy.Maximum))


class BaseAttendanceEntryWidget[_T](QWidget):
    def __init__(self, name: str, data: AttendanceEntry[_T], layout_type: type[QHBoxLayout] | type[QVBoxLayout] = QHBoxLayout):
        super().__init__()
        
        self.data = data
        self.staff = self.data.staff
        
        _layout = QVBoxLayout()
        self.setLayout(_layout)
        
        self.container = QWidget()
        
        self.main_layout = layout_type()
        self.container.setLayout(self.main_layout)
        
        self.labeled_container = LabeledField(f"<span style='font-weight: bold;'>{name} - Check {"IN" if data.is_check_in else "OUT"}</span>", self.container, height_policy=QSizePolicy.Policy.Maximum)
        self.labeled_container.setContentsMargins(10, 10, 10, 10)
        
        _layout.addWidget(self.labeled_container)
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(f"<span style='font-weight: bold'>{self.data.period.day}</span")))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"<span style='font-weight: bold'>{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}</span>")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(f"<span style='font-weight: bold'>{("0" if self.data.period.time.hour < 10 else "")}{str(self.data.period.time.hour)}</span>")))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(f"<span style='font-weight: bold'>{("0" if self.data.period.time.minute < 10 else "")}{str(self.data.period.time.minute)}</span>")))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(f"<span style='font-weight: bold'>{("0" if self.data.period.time.second < 10 else "")}{str(self.data.period.time.second)}</span>")))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_policy=QSizePolicy.Policy.Maximum))
        
        self.main_info_widget = BaseWidget()
        self.main_info_widget.addWidget(_CharacterNameWidget(self.staff.name))
        
        self.main_layout.addWidget(self.main_info_widget)




