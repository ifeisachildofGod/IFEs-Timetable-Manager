
from imports import *

from utils import Thread
from theme import THEME_MANAGER

from widgets.user_interface import *


class UnMouseableOverlay(BaseWidget):
    def __init__(self, parent: BaseWidget, editor: "SchoolTimetableEditor"):
        super().__init__(parent=parent)
        
        self.editor = editor
        self.rects: list[tuple[Class, str, int, QColor, Subject]] = []
        
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: transparent")
        
        self.hide()
        self.raise_()
    
    def paintEvent(self, a0):
        painter = QPainter(self)
        
        for cls, day, row, color, subject in self.rects:
            col = list(SCHOOL.class_levels[cls.level.id].weekdays).index(day)
            
            rect = self.get_class_timetable_cell_rect(cls, row, col)
            
            painter.setBrush(color)
            painter.drawRoundedRect(rect, 3, 3)
            
            if subject is not None:
                painter.setPen(QPen(QColor("black" if (color.red() + color.green() + color.blue()) / 3 > 150 else "white"), 4))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, subject.name.short())
    
    def setVisibilityState(self, visible):
        if visible:
            self.setGeometry(self.editor.central_widget.rect())
            self.update()
            self.show()
        else:
            self.hide()
    
    def get_class_timetable_rect(self, cls: Class):
        widg = self.editor.classes_widget[cls.level.id][1][cls.id]
        cls_ttbl = self.editor.timetable_widgets[cls.level.id][cls.id]
        
        return QRect(cls_ttbl.x() + 36 + 82, widg.y() + cls_ttbl.y() + 120 + 40, cls_ttbl.rect().width() - 82, cls_ttbl.rect().height() - 40)
    
    def get_class_timetable_cell_rect(self, cls: Class, row: int, col: int):
        ttbl_rect = self.get_class_timetable_rect(cls)
        
        x_max = len(SCHOOL.class_levels[cls.level.id].weekdays)
        y_max = cls.level.period_amount
        
        cell_width = ttbl_rect.width() / x_max
        cell_height = ttbl_rect.height() / y_max
        cell_x = ttbl_rect.x() + col * cell_width
        cell_y = ttbl_rect.y() + row * cell_height
        
        return QRectF(cell_x, cell_y, cell_width, cell_height)

class ClashOverlay(UnMouseableOverlay):
    def __init__(self, parent, editor):
        super().__init__(parent, editor)
        
        self.colors = QColor.colorNames()
        
        for c in ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', "pink", "transparent"]:
            self.colors.remove(c)
    
    def paintEvent(self, a0):
        painter = QPainter(self)
        
        clash_rects: list[tuple[QColor, list[tuple[QRectF, Subject, tuple[str, int]]]]] = []
        positions_connections_alignment_mappings = {}
        
        for (pos, (s_id, _)), classes in SCHOOL.detect_clashes().items():
            day, row = pos
            
            clash_rects.append([None, []])
            
            for cls in classes:
                col = list(SCHOOL.class_levels[cls.level.id].weekdays).index(day)
                positions_connections_alignment_mappings[day] = 0
                
                clash_rects[-1][1].append((self.get_class_timetable_cell_rect(cls, row, col), SCHOOL.subjects[s_id], day))
            
            cls_index = list(classes[0].level.classes).index(classes[0].id)
            
            col = list(SCHOOL.class_levels[classes[0].level.id].weekdays).index(day)
            x_max = len(SCHOOL.class_levels[classes[0].level.id].weekdays)
            
            clash_rects[-1][0] = QColor(self.colors[(row * x_max + col + cls_index) % len(self.colors)])
        
        for color, rects_data in clash_rects:
            d = rects_data[0][2]
            
            index = positions_connections_alignment_mappings[d]
            i_mod = index % 2
            
            offset_factor = ((index + 1) // 2) * (i_mod * 2 - 1)
            offset = QPointF(painter.pen().width() * 2 * offset_factor, 0)
            
            for i, (rect, subject, day) in enumerate(rects_data):
                painter.setPen(QPen(color, 6))
                
                if i < len(rects_data) - 1:
                    rect2 = rects_data[i + 1][0]
                    
                    p1 = rect.center() + offset
                    p2 = rect2.center() + offset
                    
                    painter.drawLine(p1, p2)
                    
                    painter.drawLine(rect.center(), p1)
                    painter.drawLine(rect2.center(), p2)
                
                painter.setBrush(color)
                painter.drawRoundedRect(rect, 5, 5)
                
                painter.setPen(QPen(QColor("black" if (color.red() + color.green() + color.blue()) / 3 > 150 else "white"), 4))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, subject.name.short())
            
            positions_connections_alignment_mappings[d] += 1
        
        return super().paintEvent(a0)

class IslandOverlay(UnMouseableOverlay):
    def paintEvent(self, a0):
        painter = QPainter(self)
        
        for cls_id, (cls_level, islands) in SCHOOL.detect_islands().items():
            cls = cls_level.classes[cls_id]
            
            for s_id, day, row in islands:
                col = list(SCHOOL.class_levels[cls_level.id].weekdays).index(day)
                
                island_rect = self.get_class_timetable_cell_rect(cls, row, col)
                
                painter.setBrush(QColor(THEME_MANAGER.process_stylesheet("{fg1}")))
                painter.drawRoundedRect(island_rect, 5, 5)
                
                painter.setPen(QColor(THEME_MANAGER.process_stylesheet("{primary_text}")))
                painter.drawText(island_rect, Qt.AlignmentFlag.AlignCenter, cls.subjects[s_id].name.short())
        
        return super().paintEvent(a0)


class ClashDisplayDialog(BaseDialogWidget):
    def __init__(self, editor: "SchoolTimetableEditor"):
        super().__init__("Clashes", BaseScrollWidget)
        
        self.editor = editor
        self.setFixedSize(500, 300)
        
        self.main_teacher_widgets: dict[ID, WidgetDropdown] = {}
        self.subjects_widgets: dict[ID, dict[ID, WidgetDropdown]] = {}
        self.classes_widgets: dict[ID, dict[ID, dict[str, LabeledField]]] = {}
    
    def make_go_to_clash(self, cls: Class, day: str, row: int, subject_id: ID):
        def func3():
            def reset():
                item.setBackground(prev_background)
                self.editor.settings_widget.clash_overlay.rects.remove(rect_data)
                self.editor.settings_widget.island_overlay.rects.remove(rect_data)
                
                self.editor.update()
            
            color = QColor(THEME_MANAGER.process_stylesheet("{fg2}"))
            
            ttbl = self.editor.timetable_widgets[cls.level.id][cls.id]
            ttbl_wrapper_widget = self.editor.classes_widget[cls.level.id][1][cls.id]
            
            self.editor.scroll_widget.getScrollWidget().verticalScrollBar().setValue(ttbl_wrapper_widget.y())
            
            item = ttbl.item(row, cls.level.weekdays.index(day))
            
            prev_background = item.background()
            item.setSelected(True)
            
            rect_data = cls, day, row, color, cls.subjects[subject_id]
            
            item.setBackground(color)
            self.editor.settings_widget.clash_overlay.rects.append(rect_data)
            self.editor.settings_widget.island_overlay.rects.append(rect_data)
            
            QTimer.singleShot(2500, reset)
        
        def func2():
            cls_lvl_widget = self.editor.classes_widget[cls.level.id][0]
            
            if not cls_lvl_widget.widget.isVisible():
                cls_lvl_widget.toogle_widget()
                
                QTimer.singleShot(100, func3)
            else:
                func3()
        
        def func(_):
            self.close()
            
            QTimer.singleShot(100, func2)
        
        return func
    
    def exec(self):
        self.main_teacher_widgets.clear()
        self.subjects_widgets.clear()
        self.classes_widgets.clear()
        
        self.getWidget().clearLayout()
        
        for ((day, row), (s_id, t_id)), classes in SCHOOL.detect_clashes().items():
            for cls in classes:
                subject = cls.subjects[s_id]
                
                if t_id not in self.main_teacher_widgets:
                    self.main_teacher_widgets[t_id] = WidgetDropdown(subject.teacher.name.full(), BaseWidget())
                    self.addWidget(self.main_teacher_widgets[t_id])
                    
                    self.subjects_widgets[t_id] = {}
                    self.classes_widgets[t_id] = {}
                
                if s_id not in self.subjects_widgets[t_id]:
                    self.subjects_widgets[t_id][s_id] = WidgetDropdown(subject.name.full(), BaseWidget())
                    self.main_teacher_widgets[t_id].widget.addWidget(self.subjects_widgets[t_id][s_id])
                    
                    self.classes_widgets[t_id][s_id] = {}
                
                pos = f"{day}, Period {row + 1}"
                
                if pos not in self.classes_widgets[t_id][s_id]:
                    self.classes_widgets[t_id][s_id][pos] = LabeledField(pos, BaseWidget())
                    self.subjects_widgets[t_id][s_id].widget.addWidget(self.classes_widgets[t_id][s_id][pos])
                
                cls_label = QLabel(f"<span style='font-size: 30px; text-spacing: 2px;'>{cls.level.name.full()} {cls.name}</span>")
                cls_label.setProperty("class", "Link2")
                cls_label.mousePressEvent = self.make_go_to_clash(cls, day, row, s_id)
                
                self.classes_widgets[t_id][s_id][pos].inner_widget.addWidget(cls_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.addStretch()
        
        return super().exec()


class _ExtrasDraggableSubjectLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)
    
    def __init__(self, subject: Subject | CombinedSubject, cls: Class):
        name = subject.name.full()
        
        if isinstance(subject, CombinedSubject):
            name = "/".join([s.name.short() for s in subject.subjects]) if subject.name is None else subject.name.short()
            sub_subject_names = "\n".join([f"\tID: {s.id}\n\tSubject: {s.name.full()}\n" for s in subject.subjects])
        
        super().__init__(name)
        
        self.subject = subject
        self.cls = cls
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("class", 'RemSubjectItem')
        
        if isinstance(self.subject, Subject):
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {name}\nTeacher: {self.subject.teacher.name.full()}")
        else:
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {name}\nChild Subjects: {sub_subject_names}")
        
        self.setFixedSize(150, 40)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event)
    
    def update_info(self):
        if isinstance(self.subject, Subject):
            name = self.subject.name.full()
            
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {name}\nTeacher: {self.subject.teacher.name.full()}")
        else:
            name = "/".join([s.name.short() for s in self.subject.subjects]) if self.subject.name is None else self.subject.name.short()
            sub_subject_names = "\n".join([f"\tID: {s.id}\n\tSubject: {s.name.full()}\n" for s in self.subject.subjects])
            
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {name}\nChild Subjects: {sub_subject_names}")
        
        self.setText(name)

class TimeTableItem(QTableWidgetItem):
    def __init__(self, subject: Subject | CombinedSubject, cls: Class, locked: bool = False):
        super().__init__()
        
        self.subject = subject
        self.cls = cls
        self.locked = locked
        
        self.break_time = BreakPeriod.id == self.subject.id
        self.free_period = FreePeriod.id == self.subject.id
        
        self.setFlags(self.flags() & Qt.ItemFlag.ItemIsEnabled)
        
        self.orig_color = self.background()
        self.orig_flags = self.flags()
        
        self.set_color()
        
        # I check if subject is None seperately bcos of when the break time is checked
        
        if self.break_time:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable)
        elif self.free_period:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable)
        else:
            self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.update()
    
    def update(self):
        if isinstance(self.subject, Subject):
            self.setText(self.subject.name.short())
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {self.subject.name.full()}\nTeacher: {self.subject.teacher.name.full()}{"\nSubject Locked" if self.locked else ""}")
        else:
            name = "/".join([s.name.short() for s in self.subject.subjects]) if self.subject.name is None else self.subject.name.full()
            sub_subject_names = "\n".join([f"\tName: {s.name.full()}\n\tID: {s.id}\n" for s in self.subject.subjects])
            
            self.setText(name)
            self.setToolTip(f"ID: {self.subject.id}\nSubject: {name}\nChild Subjects: {sub_subject_names}{"\nSubjects Locked" if self.locked else ""}")
    
    def set_locked_state(self, state: bool):
        self.locked = state
        
        self.set_color(self.orig_color if not self.locked else None)
    
    def set_color(self, color: str | None = None):
        if self.break_time:
            color = QColor(THEME_MANAGER.pallete_get("fg2"))
        elif self.locked:
            color = QColor(THEME_MANAGER.pallete_get("fg3"))
        elif self.subject is None:
            color = QColor(THEME_MANAGER.pallete_get("disabled"))
        
        if color:
            self.setBackground(color)

class TimetableTimeEditor(BaseWidget):
    def __init__(self, parent: "SchoolTimetableEditor", t_time: TimetableTime):
        super().__init__()
        
        self.__init = True
        
        self._parent = parent
        self.t_time = t_time
        
        self.start_time_edit = QTimeEdit()
        self.interval_sb = QSpinBox()
        self.break_time_duration_sb = QSpinBox()
        
        self.interval_sb.setRange(1, 60 * 24)
        self.break_time_duration_sb.setRange(1, 60 * 24)
        
        self.start_time_edit.setTime(QTime(self.t_time.start_time.hour, self.t_time.start_time.minute))
        self.interval_sb.setValue(self.t_time.interval)
        self.break_time_duration_sb.setValue(self.t_time.break_time_duration)
        
        self.addWidget(LabeledWidget("<span style='font-weight: 100'>Start Time</span>", self.start_time_edit))
        self.addWidget(LabeledWidget("<span style='font-weight: 100'>Interval</span>", self.interval_sb))
        self.addWidget(SeperatorWidget(Qt.Orientation.Horizontal, 0, None, 1))
        self.addWidget(LabeledWidget("<span style='font-weight: 100'>Break Time Duration</span>", self.break_time_duration_sb))
        
        self.start_time_edit.timeChanged.connect(self.start_time_changed)
        self.interval_sb.valueChanged.connect(self.interval_changed)
        self.break_time_duration_sb.valueChanged.connect(self.break_time_duration_changed)
        
        self.__init = False
    
    def start_time_changed(self, time: QTime):
        if not self.__init:
            self._parent.window().saved_state_changed.emit(True)
        
        self.t_time.start_time.hour = time.hour()
        self.t_time.start_time.minute = time.minute()
    
    def interval_changed(self, interval: int):
        if not self.__init:
            self._parent.window().saved_state_changed.emit(True)
        
        self.t_time.interval = interval
    
    def break_time_duration_changed(self, duration: int):
        if not self.__init:
            self._parent.window().saved_state_changed.emit(True)
        
        self.t_time.break_time_duration = duration


class TimetableSettings(BaseWidget):
    def __init__(self, editor: 'SchoolTimetableEditor'):
        super().__init__(QHBoxLayout)
        
        self.__init = True
        
        self.editor = editor
        
        self._can_generate_new = True
        
        # Clashes Viewer
        self.clash_viewer = ClashDisplayDialog(self.editor)
        
        # Overlays
        self.clash_overlay = ClashOverlay(self.editor.central_widget, self.editor)
        self.island_overlay = IslandOverlay(self.editor.central_widget, self.editor)
        
        clashes_dialog_pb = QPushButton("Clashes Viewer") ; clashes_dialog_pb.clicked.connect(lambda: self.clash_viewer.exec())
        self.show_clashes_cb = QCheckBox("Show Clashes") ; self.show_clashes_cb.clicked.connect(lambda: self.show_overlays(0))
        self.show_islands_cb = QCheckBox("Show Islands") ; self.show_islands_cb.clicked.connect(lambda: self.show_overlays(1))
        
        self.period_amt_edit = NumberLineEdit(10, 1, 20)
        self.period_amt_edit.setPlaceholderText("Period amount")
        self.period_amt_edit.textChanged.connect(self._set_period_amt)
        
        self.breakperiod_edit = NumberLineEdit(7, 1, self.period_amt_edit.number())  # Temporary
        self.breakperiod_edit.setPlaceholderText("Break period")
        self.breakperiod_edit.textChanged.connect(self._set_break_periods)
        
        # Settings Menu
        settings_menu_widget = BaseWidget()
        
        settings_menu_widget.addWidget(LabeledWidget("Period Amount", self.period_amt_edit))
        settings_menu_widget.addWidget(LabeledWidget("Break Period", self.breakperiod_edit))
        settings_menu_widget.addSpacing(10)
        # settings_menu_widget.addWidget(dotw_button := QPushButton("Days of the Week"))
        settings_menu_widget.addWidget(generate_button := QPushButton("Generate School")) ; generate_button.clicked.connect(lambda: self.generate_school_timetable())
        settings_menu_widget.addWidget(generate_new_button := QPushButton("Generate New School")) ; generate_new_button.clicked.connect(lambda: self.generate_school_timetable(self.clear_all_timetables))
        settings_menu_widget.addWidget(clear_button := QPushButton("Clear Timetables")) ; clear_button.clicked.connect(self.clear_all_timetables)
        settings_menu_widget.addSpacing(10)
        settings_menu_widget.addWidget(randomize_button := QCheckBox("Randomize")) ; randomize_button.clicked.connect(self.randomize)
        self.randomize_button = randomize_button
        
        self.addWidget(clashes_dialog_pb)
        self.addWidget(self.show_clashes_cb)
        self.addWidget(self.show_islands_cb)
        self.addStretch()
        self.addWidget(IconToolBarOption(settings_menu_widget, title="☰"))
        
        self.__init = False
    
    def _set_period_amt(self, period_amt: int):
        self.editor.window().saved_state_changed.emit(True)
        
        self.breakperiod_edit.blockSignals(True)
        self.breakperiod_edit.max_num = period_amt
        self.breakperiod_edit.blockSignals(False)
        
        for _, cls_level in SCHOOL.class_levels:
            for cls in cls_level.classes.values():
                self.editor.timetable_widgets[cls_level.id][cls.id].set_period_amt(period_amt)
            
            cls_level.period_amount = period_amt
    
    def _set_break_periods(self, break_period: int):
        self.editor.window().saved_state_changed.emit(True)
        
        for _, cls_level in SCHOOL.class_levels:
            for cls in cls_level.classes.values():
                self.editor.timetable_widgets[cls_level.id][cls.id].set_break_period(break_period)
            
            cls_level.break_period = break_period
    
    def _toogle_self(self):
        self.settings_menu.set_pos(self.toogle_button.mapToGlobal(QPoint(-470, self.toogle_button.height())))
        self.settings_menu.toogle()
    
    def show_overlays(self, overlay_type: int):
        c_state = self.show_clashes_cb.isChecked()
        i_state = self.show_islands_cb.isChecked()
        
        state = c_state or i_state
        
        for lvl_dp, _ in self.editor.classes_widget.values():
            lvl_dp.beDisabled(state, False)
            
            lvl_dp.toogle_icon.setDisabled(state)
            lvl_dp.title_label.setDisabled(state)
        
        match overlay_type:
            case 0:
                self.clash_overlay.setVisibilityState(c_state)
            case 1:
                self.island_overlay.setVisibilityState(i_state)
        
        self.editor.update()
    
    def generating_finished(self):
        self._can_generate_new = True
        
        for lvl_ttbl_content in self.editor.timetable_widgets.values():
            for ttbl in lvl_ttbl_content.values():
                ttbl.populate_timetable()
    
    def clear_all_timetables(self):
        self.editor.window().saved_state_changed.emit(True)
        
        for lvl_ttbl_content in self.editor.timetable_widgets.values():
            for ttbl in lvl_ttbl_content.values():
                ttbl.clear_timetable()
    
    def continue_with_irreversable_action(self):
        return QMessageBox.StandardButton.Yes == QMessageBox.warning(
            self,
            "Action Irreversible",
            "This action cannot be reversed\n"
            "All information will be overwritten",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
    
    def generate_school_timetable(self, pre_func: Optional[Callable] = None):
        if self._can_generate_new:
            if not self.continue_with_irreversable_action():
                return
            
            if callable(pre_func):
                pre_func()
            
            self.editor.window().saved_state_changed.emit(True)
            
            self.generate_new = Thread(self.window(), lambda: SCHOOL.generate_timetables())
            self.generate_new.finished.connect(self.generating_finished)
            self.generate_new.start()
            
            self._can_generate_new = False
            
            return
        
        QMessageBox.critical(self, "ThreadingError", "School Timetable is already being generated")

    def randomize(self, state: bool):
        if not self.__init:
            self.editor.window().saved_state_changed.emit(True)
        
        for lvl_id, _ in SCHOOL.class_levels:
            if state != self.editor.level_randomize_cbs[lvl_id].isChecked():
                self.editor.level_randomize_cbs[lvl_id].click()


class ClassTimetable(QTableWidget):
    def __init__(self, cls: Class, editor: 'SchoolTimetableEditor'):
        super().__init__()
        
        self.__init = True
        
        self.cls = cls
        self.editor = editor
        self.timetable, self.timetable_remains = SCHOOL.timetables_data[self.cls.id]
        
        self.remainder_widget_width = 200
        
        self.remainder_widget = BaseScrollWidget()
        self.remainder_widget.setFixedWidth(self.remainder_widget_width)
        self.remainder_widget.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.remainder_widget.addStretch()
        
        self.remainder_labels: list[_ExtrasDraggableSubjectLabel] = []
        
        self.weekdays = self.cls.level.weekdays
        self.period_amt = self.cls.level.period_amount
        
        self.setRowCount(self.period_amt)
        self.setColumnCount(len(self.weekdays))
        self.setHorizontalHeaderLabels(self.weekdays)
        self.setVerticalHeaderLabels([f"Period {i+1}" for i in range(self.rowCount())])
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.rowCount() * 30 + 42)  # Adjust row height + header
        
        # Enable drag & drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        # Connect context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Load initial data
        self.populate_timetable()
        
        # Variables
        self.current_source = None
        self.drag_source_col = -1
        
        self.__init = False
    
    def set_period_amt(self, period_amt: int):
        self.window().saved_state_changed.emit(True)
        
        for col, day in enumerate(self.weekdays):
            is_diff_positive = period_amt - self.cls.level.period_amount > 0
            is_diff_negative = period_amt - self.cls.level.period_amount < 0
            
            if is_diff_positive:
                self.timetable[day] += [FreePeriod() for _ in range(period_amt - self.cls.level.period_amount)]
            elif is_diff_negative:
                break_index = next(i for i, s in enumerate(self.timetable[day]) if s.id == BreakPeriod.id)
                
                if period_amt < break_index + 1:
                    self.timetable_exchange(self.item(break_index, col), self.item(break_index - 1, col))
                
                for i, subj in enumerate(self.timetable[day][period_amt - self.cls.level.period_amount:]):
                    if subj.id not in (FreePeriod.id, BreakPeriod.id):
                        self.addRemainder(subj)
                    
                    self.timetable[day].pop(i + period_amt - self.cls.level.period_amount)
            else:
                continue
        
        self.setRowCount(period_amt)
        self.setVerticalHeaderLabels([f"Period {i + 1}" for i in range(self.rowCount())])
        self.setFixedHeight(self.rowCount() * 30 + 42)
        
        for col in range(self.columnCount()):
            for row in range(self.rowCount()):
                if self.item(row, col) is None:
                    self.setItem(row, col, TimeTableItem(FreePeriod(), self.cls))
        
        self.period_amt = period_amt
    
    def set_break_period(self, break_period: int):
        self.window().saved_state_changed.emit(True)
        
        for col, day in enumerate(self.weekdays):
            ls_key = day, break_period - 1
            
            break_index = next(i for i, s in enumerate(self.timetable[day]) if s.id == BreakPeriod.id)
            
            if ls_key in self.cls.locked_subjects:
                self.cls.locked_subjects.pop(ls_key)
            
            self.timetable_exchange(self.item(break_index, col), self.item(break_period - 1, col))
    
    def update_break_time_color(self):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                
                if item.break_time:
                    item.set_color()
    
    def timetable_exchange(self, source_item: TimeTableItem, target_item: TimeTableItem):
        if not self.__init:
            self.window().saved_state_changed.emit(True)
        
        source_row, source_col = self.row(source_item), self.column(source_item)
        target_row, target_col = self.row(target_item), self.column(target_item)
        
        # Same timetable swap
        self.blockSignals(True)  # Prevent unnecessary updates
        
        # Remove old items
        self.takeItem(source_row, source_col)
        self.takeItem(target_row, target_col)
        
        # Create new items
        new_target = TimeTableItem(source_item.subject, self.cls)
        new_source = TimeTableItem(target_item.subject, self.cls)
        
        # Set new items
        self.setItem(target_row, target_col, new_target)
        self.setItem(source_row, source_col, new_source)
        
        # Background replacement
        source = self.timetable[self.weekdays[source_col]][source_row]
        target = self.timetable[self.weekdays[target_col]][target_row]
        self.timetable[self.weekdays[source_col]][source_row] = target
        self.timetable[self.weekdays[target_col]][target_row] = source
        
        # Force refresh
        self.blockSignals(False)
        self.editor.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            
            if item and isinstance(item, TimeTableItem) and item.subject:
                self.drag_source_col = self.column(item)
                self.drag_source_row = self.row(item)
                
                # Store original position
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(item.subject.name.full())
                drag.setMimeData(mime_data)
                
                # Create drag feedback by grabbing the cell widget
                cell_rect = self.visualItemRect(item)
                pixmap = self.viewport().grab(cell_rect)
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.pos() - cell_rect.topLeft())
                
                drag.exec()
        
        super().mousePressEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            row = self.rowAt(int(event.position().y()))
            col = self.columnAt(int(event.position().x()))
            
            source: TimeTableItem = self.item(row, col)
            
            if source is not None and not source.locked and (self.editor.remainder_source_ref is not None or source.subject.id != FreePeriod.id):
                event.accept()
                if self.editor.remainder_source_ref is None:
                    self.current_source = source
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            source_cls: ClassTimetable = event.source()
            
            col = self.columnAt(int(event.position().x()))
            row = self.rowAt(int(event.position().y()))
            
            break_time = next(i + 1 for i, s in enumerate(self.timetable[self.weekdays[col]]) if s.id == BreakPeriod.id)
            source_break_time = next(i + 1 for i, s in enumerate(self.timetable[self.weekdays[self.drag_source_col]]) if s.id == BreakPeriod.id)
            
            ignore = True
            if self.editor.remainder_source_ref is None:
                ignore = source_cls.cls.id != self.cls.id or (
                    self.drag_source_col != col and (
                        row == break_time - 1 or
                        source_break_time == self.drag_source_row + 1
                        )
                    )
            else:
                ignore = self.editor.remainder_source_ref.cls.id != self.cls.id or row == break_time - 1
            
            ignore = ignore or (self.weekdays[col], row + 1) in self.cls.locked_subjects
            
            if ignore:
                event.ignore()
            else:
                event.accept()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasText():
            if self.current_source is not None:
                target_row = self.rowAt(int(event.position().y()))
                target_col = self.columnAt(int(event.position().x()))
                target_item = self.item(target_row, target_col)
                
                # Handle swapping
                if target_item is not None and not target_item.locked and isinstance(target_item, TimeTableItem):
                    if self.current_source.cls.id == self.cls.id:
                        self.timetable_exchange(self.current_source, target_item)
                        
                        event.accept()
                        
                        del target_item
            elif self.editor.remainder_source_ref is not None and self.cls.id == self.editor.remainder_source_ref.cls.id:
                row = self.rowAt(int(event.position().y()))
                col = self.columnAt(int(event.position().x()))
                target_item = self.item(row, col)
                
                self.blockSignals(True)  # Prevent unnecessary updates
                
                new_target = TimeTableItem(self.editor.remainder_source_ref.subject, self.cls)
                
                self.takeItem(row, col)
                self.setItem(row, col, new_target)
                
                if isinstance(target_item, TimeTableItem) and not target_item.free_period:
                    # Set new items
                    self.addRemainder(target_item.subject, self.remainder_widget.indexOf(self.editor.remainder_source_ref))
                    
                    self.timetable[self.weekdays[col]][row] = FreePeriod()
                
                # Remove remainder widget
                self.removeRemainder(self.editor.remainder_source_ref)
                
                self.remainder_widget.update()
                
                self.blockSignals(False)
                
                self.timetable[self.weekdays[col]][row] = self.editor.remainder_source_ref.subject
                
                event.accept()
                self.editor.update()
            
            self.editor.remainder_unfocused()
            self.current_source = None
    
    def addRemainder(self, subject: Subject, index: int | None = None):
        if not self.__init:
            self.window().saved_state_changed.emit(True)
        
        remainder_label = _ExtrasDraggableSubjectLabel(subject, self.cls)
        remainder_label.clicked.connect(self.editor.make_ds_func(remainder_label))
        
        if index is not None:
            self.remainder_widget.insertWidget(index, remainder_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.insert(index - 1, remainder_label)
            self.timetable_remains.insert(index - 1, subject)
        else:
            self.remainder_widget.insertWidget(len(self.remainder_widget.getChildren()), remainder_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.append(remainder_label)
            self.timetable_remains.append(subject)
    
    def removeRemainder(self, remainder: _ExtrasDraggableSubjectLabel):
        if not self.__init:
            self.window().saved_state_changed.emit(True)
        
        self.remainder_labels.remove(remainder)
        self.remainder_widget.removeWidget(remainder)
        self.timetable_remains.remove(remainder.subject)
        
        remainder.deleteLater()
    
    def clear_remains(self):
        for widg in self.remainder_labels.copy():
            self.remainder_labels.remove(widg)
            self.remainder_widget.removeWidget(widg)
            
            widg.deleteLater()
        
        self.timetable_remains.clear()
    
    def clear_timetable(self):
        if not self.__init:
            self.window().saved_state_changed.emit(True)
        
        SCHOOL.fresh_timetable(self.cls)
        
        self.populate_timetable()
    
    def generate(self):
        try:
            SCHOOL.generate_timetables([(self.cls.level.id, self.cls.id)])
            self.populate_timetable()
        except Exception as e:
            QMessageBox.critical(None, e.__class__.__name__, str(e))
    
    def clear_and_generate(self):
        response = QMessageBox.warning(
            self.editor,
            "Action Irreversible",
                "This action cannot be reversed\n"
                f"All timetable information in {self.cls.level.name.full()} {self.cls.name} will be overwritten\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
                            
        if response != QMessageBox.StandardButton.Yes:
            return
        
        SCHOOL.fresh_timetable(self.cls)
        self.generate()
    
    def populate_timetable(self):
        for col, day in enumerate(self.weekdays):
            for row, subject in enumerate(self.timetable[day] + [FreePeriod() for _ in range(self.period_amt - len(self.timetable[day]))]):
                item = TimeTableItem(subject, self.cls, (self.weekdays[col], row + 1) in self.cls.locked_subjects)
                
                self.setItem(row, col, item)
        
        timetable_remains = self.timetable_remains.copy()
        
        self.clear_remains()
        
        for subject in timetable_remains:
            self.addRemainder(subject)
    
    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        
        if item and isinstance(item, TimeTableItem) and not item.free_period and not item.break_time:
            menu = QMenu(self)
            
            lock_period_action = -1
            unlock_period_action = -1
            
            delete_action = menu.addAction("Delete")
            if item.locked:
                unlock_period_action = menu.addAction("Unlock Period")
            else:
                lock_period_action = menu.addAction("Lock Period")
            goto_subject_action = menu.addAction("Go to Subject")
            goto_teacher_action = menu.addAction("Go to Teacher")
            
            action = menu.exec(self.viewport().mapToGlobal(pos))
            
            # TODO: Add warning to the delete action for when
            #       the action is activated when the subject is locked
            if action == delete_action and not item.locked:
                free_period = FreePeriod()
                
                row = self.row(item)
                col = self.column(item)
                
                self.addRemainder(item.subject)
                
                self.setItem(row, col, TimeTableItem(free_period, self.cls))
                
                self.timetable[self.weekdays[col]][row] = free_period
            elif action == lock_period_action:
                item.set_locked_state(True)
                self.cls.locked_subjects[(self.weekdays[item.column()], item.row() + 1)] = item.subject.id
            elif action == unlock_period_action:
                item.set_locked_state(False)
                self.cls.locked_subjects.pop((self.weekdays[item.column()], item.row() + 1))
            elif action == goto_subject_action:
                pass
            elif action == goto_teacher_action:
                pass
    
    def change_subject_amount(self, subject_id: ID, diff: int):
        subject = self.cls.subjects[subject_id]
        
        if diff > 0:
            for _ in range(diff):
                self.addRemainder(subject)
        elif diff < 0:
            diff = -diff
            
            rem_amt = self.timetable_remains.count(subject)
            ttbl_rem_amt = diff - rem_amt if diff > rem_amt else 0
            
            for _ in range(rem_amt if diff > rem_amt else diff):
                self.removeRemainder(self.remainder_labels[self.timetable_remains.index(subject)])
            
            if ttbl_rem_amt:
                for x in range(self.columnCount() * self.rowCount()):
                    row = x // self.columnCount()
                    col = x % self.columnCount()
                    
                    if subject.id == self.timetable[self.weekdays[col]][row].id:
                        free_period = FreePeriod()
                        
                        self.setItem(row, col, TimeTableItem(free_period, self.cls))
                        self.timetable[self.weekdays[col]][row] = free_period
                        
                        ttbl_rem_amt -= 1
                    
                    if not ttbl_rem_amt:
                        break

class SchoolTimetableEditor(BaseWidget):
    def __init__(self):
        super().__init__()
        
        self.remainder_source_ref: Optional[TimeTableItem] = None
        
        self.class_generator_threads: dict[ID, Thread] = {}
        
        # Create scroll area for timetables
        self.scroll_widget = BaseScrollWidget()
        self.scroll_widget.getScrollWidget().setWidgetResizable(True)
        self.scroll_widget.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.central_widget = BaseWidget()
        self.central_widget.addStretch()
        self.central_widget.setSpacing(20)
        
        self.scroll_widget.addWidget(self.central_widget)
        
        # Create timetable for each class
        self.level_randomize_cbs: dict[ID, QCheckBox] = {}
        self.cls_randomize_cbs: dict[ID, QCheckBox] = {}
        self.label_data: dict[ID, QLabel] = {}
        self.timetable_widgets: dict[ID, dict[ID, ClassTimetable]] = {}
        self.classes_widget: dict[ID, tuple[WidgetDropdown, dict[ID, BaseWidget]]] = {}
        self.everyday_widgets: dict[ID, Optional[BaseWidget]] = {}
        self.ttbl_day_trackers: dict[ID, dict[QComboBox, list[str, list[str]]]] = {}
        
        # Create settings for timetables
        self.settings_widget = TimetableSettings(self)
        
        self.addWidget(self.settings_widget)
        self.addWidget(self.scroll_widget)
    
    def remainder_unfocused(self):
        self.remainder_source_ref = None
    
    def make_ds_func(self, label: _ExtrasDraggableSubjectLabel):
        def func(event):
            self.remainder_source_ref = label
            
            drag = QDrag(label)
            mime_data = QMimeData()
            mime_data.setText(label.subject.name.short())
            drag.setMimeData(mime_data)
            
            # Create drag feedback
            pixmap = label.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            
            drag.destroyed.connect(lambda: self.remainder_unfocused())
            
            drag.exec()
        
        return func
    
    def make_class_level_settings(self, cls_level: ClassLevel):
        widget = BaseWidget()
        widget.setFixedWidth(350)
        
        def generating_finished():
            self.class_generator_threads.pop(cls_level.id)
            
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.populate_timetable()
        
        def period_amt_changed(curr_period_amt: int):
            breakperiod_edit.blockSignals(True)
            breakperiod_edit.max_num = curr_period_amt
            breakperiod_edit.blockSignals(False)
            
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.set_period_amt(curr_period_amt)
            
            cls_level.period_amount = curr_period_amt
        
        def break_period_changed(curr_break_period: int):
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.set_break_period(curr_break_period)
            
            cls_level.break_period = curr_break_period
        
        def generate_func(pre_func: Optional[Callable] = None):
            if cls_level.id not in self.class_generator_threads:
                if not self.settings_widget.continue_with_irreversable_action():
                    return
                
                if callable(pre_func):
                    pre_func()
                
                self.window().saved_state_changed.emit(True)
                
                self.class_generator_threads[cls_level.id] = Thread(self.window(), lambda: SCHOOL.generate_timetables([(cls_level.id, cls.id) for cls in cls_level.classes.values()]))
                self.class_generator_threads[cls_level.id].finished.connect(generating_finished)
                self.class_generator_threads[cls_level.id].start()
                
                return
            
            QMessageBox.critical(self, "Threading Error", "Level is already being generated")
        
        def clear_func():
            self.window().saved_state_changed.emit(True)
            
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.clear_timetable()
        
        def randomize(state: bool):
            if not _init:
                self.window().saved_state_changed.emit(True)
            
            if state and next((False for cb in self.level_randomize_cbs.values() if not cb.isChecked()), True):
                self.settings_widget.randomize_button.setChecked(True)
            else:
                self.settings_widget.randomize_button.blockSignals(True)
                self.settings_widget.randomize_button.setChecked(False)
                self.settings_widget.randomize_button.blockSignals(False)
            
            for cls_id in SCHOOL.class_levels[cls_level.id].classes:
                self.cls_randomize_cbs[cls_id].setChecked(state)
        
        def _add_everyday(set_default: bool = True):
            widg = BaseWidget() ; widg.setProperty("class", "Bordered")
            
            if set_default:
                SCHOOL.settings.TIMETABLE_time_settings[cls_level.id]["Everyday"] = SCHOOL.settings.DEFAULT_timetable_time_setting.copy()
            
            evd = SCHOOL.settings.TIMETABLE_time_settings[cls_level.id]["Everyday"]
            
            widg.addWidget(QLabel("<b>Everyday</b>"))
            widg.addWidget(TimetableTimeEditor(self, evd))
            
            self.everyday_widgets[cls_level.id] = widg
            timing_widget.insertWidget(0, widg)
        
        def new_day_added(def_day: Optional[str], time_setting: TimetableTime):
            if def_day is None:
                self.window().saved_state_changed.emit(True)
            
            days = [day for day in cls_level.weekdays if day not in SCHOOL.settings.TIMETABLE_time_settings[cls_level.id] or day == def_day]
            
            if time_setting is None:
                time_setting = SCHOOL.settings.TIMETABLE_time_settings[cls_level.id][days[0]] = SCHOOL.settings.DEFAULT_timetable_time_setting.copy()
            
            days_0 = def_day or days[0]
            
            def _add_day(day: str):
                for cb in self.ttbl_day_trackers[cls_level.id]:
                    if cb != day_cb:
                        if day not in self.ttbl_day_trackers[cls_level.id][cb][1]:
                            cb.addItem(day)
                            self.ttbl_day_trackers[cls_level.id][cb][1].append(day)
            
            def _remove_day(day: str):
                for cb in self.ttbl_day_trackers[cls_level.id]:
                    if cb != day_cb:
                        if day in self.ttbl_day_trackers[cls_level.id][cb][1]:
                            cb.removeItem(self.ttbl_day_trackers[cls_level.id][cb][1].index(day))
                            self.ttbl_day_trackers[cls_level.id][cb][1].remove(day)
            
            def set_day(day: str):
                prev_day = self.ttbl_day_trackers[cls_level.id][day_cb][0]
                
                SCHOOL.settings.TIMETABLE_time_settings[cls_level.id][day] = SCHOOL.settings.TIMETABLE_time_settings[cls_level.id].pop(prev_day)
                
                _remove_day(day)
                
                for d in cls_level.weekdays:
                    if d not in SCHOOL.settings.TIMETABLE_time_settings[cls_level.id]:
                        _add_day(d)
                
                self.ttbl_day_trackers[cls_level.id][day_cb][0] = day
            
            def removed():
                if self.everyday_widgets[cls_level.id] is None:
                    _add_everyday()
                    add_new_day_pb.setDisabled(False)
                
                day_time_widget.delete()
                SCHOOL.settings.TIMETABLE_time_settings[cls_level.id].pop(day_cb.currentText())
                self.ttbl_day_trackers[cls_level.id].pop(day_cb)
                
                _add_day(day_cb.currentText())
            
            day_cb = QComboBox()
            day_cb.addItems(days)
            day_cb.currentTextChanged.connect(set_day)
            self.ttbl_day_trackers[cls_level.id][day_cb] = [days_0, days]
            
            if not def_day:
                _remove_day(days[0])
            
            day_time_widget = BaseWidget() ; day_time_widget.setProperty("class", "Bordered")
            
            cancel_pb = QPushButton("×")
            cancel_pb.setProperty("class", "SettingEntryClose")
            cancel_pb.clicked.connect(removed)
            
            top_widget = BaseWidget(QHBoxLayout) ; top_widget.addWidget(day_cb) ; top_widget.addStretch() ; top_widget.addWidget(cancel_pb)
            
            day_time_widget.addWidget(top_widget)
            day_time_widget.addWidget(TimetableTimeEditor(self, time_setting))
            
            timing_widget.addWidget(day_time_widget)
            
            if len(days) == 1 and self.everyday_widgets[cls_level.id] is not None:
                self.everyday_widgets[cls_level.id].delete()
                self.everyday_widgets[cls_level.id] = None
                
                SCHOOL.settings.TIMETABLE_time_settings[cls_level.id].pop("Everyday")
                add_new_day_pb.setDisabled(True)
            
            if def_day is not None:
                day_cb.blockSignals(True)
                day_cb.setCurrentIndex(days.index(def_day))
                day_cb.blockSignals(False)
            
            QTimer.singleShot(100, lambda: timing_widget.getScrollWidget().verticalScrollBar().setValue(timing_widget.getScrollWidget().verticalScrollBar().maximum()))
        
        _init = True
        
        period_amt_edit = NumberLineEdit(cls_level.period_amount, 1, 20)
        period_amt_edit.setPlaceholderText("Periods Amt")
        period_amt_edit.textChanged.connect(period_amt_changed)
        
        breakperiod_edit = NumberLineEdit(cls_level.break_period, period_amt_edit.min_num, period_amt_edit.number())
        breakperiod_edit.setPlaceholderText("Break period")
        breakperiod_edit.textChanged.connect(break_period_changed)
        
        generate_button = QPushButton("Generate Level")
        generate_button.clicked.connect(lambda: generate_func())
        
        generate_new_button = QPushButton("Generate New Level")
        generate_new_button.clicked.connect(lambda: generate_func(clear_func))
        
        clear_button = QPushButton("Clear Timetable")
        clear_button.clicked.connect(clear_func)
        
        randomize_button = QCheckBox("Randomize")
        randomize_button.clicked.connect(randomize)
        
        timing_area_widget = BaseWidget()
        
        timing_widget = BaseScrollWidget()
        add_new_day_pb = QPushButton("Add new") ; add_new_day_pb.clicked.connect(lambda: new_day_added(None, None))
        
        timing_area_widget.addWidget(timing_widget)
        timing_area_widget.addWidget(add_new_day_pb, alignment=Qt.AlignmentFlag.AlignRight)
        
        for name, content in SCHOOL.settings.TIMETABLE_time_settings[cls_level.id].items():
            if name == "Everyday":
                _add_everyday(False)
            else:
                new_day_added(name, content)
        
        widget.addWidget(LabeledWidget("Period Amount", period_amt_edit))
        widget.addWidget(LabeledWidget("Break Period", breakperiod_edit))
        # widget.addSpacing(5)
        # widget.addWidget(dotw_button)
        widget.addSpacing(10)
        widget.addWidget(generate_button)
        widget.addWidget(generate_new_button)
        widget.addWidget(clear_button)
        widget.addSpacing(10)
        widget.addWidget(randomize_button)
        widget.addSpacing(10)
        widget.addWidget(timing_area_widget)
        
        self.level_randomize_cbs[cls_level.id] = randomize_button
        
        _init = False
        
        return widget
    
    def add_timetable_level(self, cls_level: ClassLevel):
        self.timetable_widgets[cls_level.id] = {}
        
        body_widget = BaseWidget()
        
        level_widget = WidgetDropdown(f"<span style='font-size: 40px'>{cls_level.name.full()}</span>", body_widget)
        level_widget.toogle_widget()
        
        self.ttbl_day_trackers[cls_level.id] = {}
        self.label_data[cls_level.id] = level_widget.title_label
        self.classes_widget[cls_level.id] = level_widget, {}
        
        settings_menu_widget = self.make_class_level_settings(cls_level)
        
        level_widget.header.addWidget(IconToolBarOption(settings_menu_widget, title="☰"))
        
        self.central_widget.insertWidget(len(self.central_widget.getChildren()), level_widget)
    
    def add_timetable_class(self, cls: Class):
        def randomize(state: bool):
            if not _init:
                self.window().saved_state_changed.emit(True)
            
            if state and next((False for cb in self.cls_randomize_cbs.values() if not cb.isChecked()), True):
                self.level_randomize_cbs[cls.level.id].setChecked(True)
            else:
                self.level_randomize_cbs[cls.level.id].blockSignals(True)
                self.level_randomize_cbs[cls.level.id].setChecked(False)
                self.level_randomize_cbs[cls.level.id].blockSignals(False)
                
                self.settings_widget.randomize_button.blockSignals(True)
                self.settings_widget.randomize_button.setChecked(False)
                self.settings_widget.randomize_button.blockSignals(False)
            
            SCHOOL.gen_data.randomize[cls.id] = state
        
        settings_menu = BaseWidget()
        settings_menu.setWindowFlags(Qt.WindowType.Popup)
        
        toogle_button = IconToolBarOption(settings_menu, title="☰")
        
        widget = BaseWidget()
        widget.setProperty("class", "TimetableWidget")
        
        class_header = BaseWidget(QHBoxLayout)
        class_header.setProperty("class", "NoBackground")
        class_header.setContentsMargins(0, 0, 0, 0)
        
        class_name_label = QLabel(cls.name)
        class_name_label.setProperty("class", "Title")
        self.label_data[cls.id] = class_name_label
        
        class_header.addWidget(class_name_label)
        class_header.addStretch()
        class_header.addWidget(toogle_button)
        
        # Create timetable
        class_widget = BaseWidget(QHBoxLayout)
        class_widget.setProperty("class", "NoBackground")
        
        sidebar_widget = BaseWidget()
        sidebar_widget.setProperty("class", "NoBackground")
        
        timetable = ClassTimetable(cls, self)
        self.timetable_widgets[cls.level.id][cls.id] = timetable
        
        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(timetable.generate)
        
        generate_new_button = QPushButton("Generate New")
        generate_new_button.clicked.connect(timetable.clear_and_generate)
        
        clear_button = QPushButton("Clear Timetable")
        clear_button.clicked.connect(timetable.clear_timetable)
        
        randomize_button = QCheckBox("Randomize")
        randomize_button.clicked.connect(randomize)
        _init = True
        if SCHOOL.gen_data.randomize.get(cls.id, False):
            randomize_button.click()
        _init = False
        
        settings_menu.addWidget(generate_button)
        settings_menu.addWidget(generate_new_button)
        settings_menu.addWidget(clear_button)
        settings_menu.addSpacing(20)
        settings_menu.addWidget(randomize_button)
        
        class_widget.addWidget(timetable)
        class_widget.addWidget(sidebar_widget)
        
        sidebar_widget.addWidget(timetable.remainder_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        widget.addWidget(class_header)
        widget.addWidget(class_widget)
        
        self.classes_widget[cls.level.id][0].widget.addWidget(widget)
        self.classes_widget[cls.level.id][1][cls.id] = widget
        self.cls_randomize_cbs[cls.id] = randomize_button
    
    def delete_timetable_level(self, cls_level_id: ID):
        self.classes_widget[cls_level_id][0].delete()
        
        self.classes_widget.pop(cls_level_id)
        self.everyday_widgets.pop(cls_level_id)
        ttbl_content = self.timetable_widgets.pop(cls_level_id)
        self.level_randomize_cbs.pop(cls_level_id)
        
        for cls_id in ttbl_content:
            self.cls_randomize_cbs.pop(cls_id)
    
    def delete_timetable_class(self, cls: Class):
        self.classes_widget[cls.level.id][1][cls.id].delete()
        
        self.timetable_widgets[cls.level.id].pop(cls.id)
        self.classes_widget[cls.level.id][1].pop(cls.id)
        self.cls_randomize_cbs.pop(cls.id)
    
    def set_label_text(self, id: ID, name: str | ClassLevelName):
        self.label_data[id].setText(name if isinstance(name, str) else f"<span style='font-size: 60px'>{name.full()}</span>")



