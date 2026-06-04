
from imports import *

from utils import Thread

from widgets.user_interface import *


class _ExtrasDraggableSubjectLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)
    
    def __init__(self, subject: Subject | CombinedSubject):
        name = subject.name.full()
        
        if isinstance(subject, CombinedSubject):
            name = "/".join([s.name.short() for s in subject.subjects]) if subject.name is None else subject.name.short()
            sub_subject_names = "\n".join([f"\tID: {s.id}\n\tSubject: {s.name.full()}\n" for s in subject.subjects])
        
        super().__init__(name)
        
        self.subject = subject
        
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
    def __init__(self, subject: Subject | CombinedSubject, break_time: bool = False, free_period: bool = False, locked: bool = False):
        super().__init__()
        
        self.subject = subject
        self.break_time = break_time
        self.free_period = free_period
        self.locked = locked
        
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


class TimetableSettings(BaseWidget):
    def __init__(self, editor: 'SchoolTimetableEditor'):
        super().__init__()
        
        self.editor = editor
        
        self._can_generate_new = True
        
        self.settings_menu = MenuFrame()
        
        self.toogle_button = QPushButton("☰")
        self.toogle_button.setProperty("class", "Timetable_DP_OptionText")
        self.toogle_button.clicked.connect(self._toogle_self)
        
        self.addWidget(self.toogle_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        general_settings_widget = BaseWidget(QHBoxLayout)
        
        left_option_widget = BaseWidget()
        
        self.period_amt_edit = NumberLineEdit(10, 1, 20)
        self.period_amt_edit.setPlaceholderText("Period amount")
        self.period_amt_edit.textChanged.connect(self._set_period_amt)
        
        self.breakperiod_edit = NumberLineEdit(7, 1, self.period_amt_edit.number())  # Temporary
        self.breakperiod_edit.setPlaceholderText("Break period")
        self.breakperiod_edit.textChanged.connect(self._set_break_periods)
        
        # left_sub_option_widget = BaseWidget(QHBoxLayout)
        
        # dotw_button = QPushButton("Days of the Week")
        
        # left_sub_option_widget.addWidget(dotw_button)
        
        left_option_widget.addWidget(self.period_amt_edit)
        left_option_widget.addWidget(self.breakperiod_edit)
        # left_option_widget.addWidget(left_sub_option_widget)
        
        right_option_widget = BaseWidget()
        
        generate_button = QPushButton("Generate New School")
        generate_button.clicked.connect(self.generate_new_school_timetable)
        
        clear_button = QPushButton("Clear Timetables")
        clear_button.clicked.connect(self.clear_all_timetables)
        
        right_option_widget.addWidget(generate_button)
        right_option_widget.addWidget(clear_button)
        
        general_settings_widget.addWidget(left_option_widget)
        general_settings_widget.addWidget(right_option_widget)
        
        # Settings Menu
        settings_menu_layout = self.settings_menu.layout()
        
        settings_menu_layout.addWidget(general_settings_widget)
    
    def _set_period_amt(self, period_amt: int):
        for _, cls_level in SCHOOL.class_levels:
            for cls in cls_level.classes.values():
                self.editor.timetable_widgets[cls_level.id][cls.id].set_period_amt(period_amt)
    
    def _set_break_periods(self, break_period: int):
        for _, cls_level in SCHOOL.class_levels:
            for cls in cls_level.classes.values():
                self.editor.timetable_widgets[cls_level.id][cls.id].set_break_period(break_period)
    
    def _toogle_self(self):
        self.settings_menu.set_pos(self.toogle_button.mapToGlobal(QPoint(-470, self.toogle_button.height())))
        self.settings_menu.toogle()
    
    def generating_finished(self):
        self._can_generate_new = True
        
        for lvl_ttbl_content in self.editor.timetable_widgets.values():
            for ttbl in lvl_ttbl_content.values():
                ttbl.populate_timetable()
    
    def clear_all_timetables(self):
        for lvl_ttbl_content in self.editor.timetable_widgets.values():
            for ttbl in lvl_ttbl_content.values():
                ttbl.clear_timetable()
    
    def generate(self):
        for lvl_ttbl_content in self.editor.timetable_widgets.values():
            for ttbl in lvl_ttbl_content.values():
                ttbl.clear_remains()
        
        SCHOOL.generate_timetables()
    
    def continue_with_irreversable_action(self):
        return QMessageBox.StandardButton.Yes == QMessageBox.warning(self, "Action Irreversible", "This action cannot be reversed\n"
                                                                                                  "All information will be overwritten",
                                                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    def generate_new_school_timetable(self):
        if self._can_generate_new:
            if not self.continue_with_irreversable_action():
                QMessageBox.critical(self, "TimetableGeneratorError", "Variables and connections are not sufficient to generate a timetable")
                
                return
            
            self.generate_new = Thread(self.window(), self.generate)
            self.generate_new.finished.connect(self.generating_finished)
            self.generate_new.start()
            
            self._can_generate_new = False
            
            return
        
        QMessageBox.critical(self, "ThreadingError", "School Timetable is already being generated")


class ClassTimetable(QTableWidget):
    def __init__(self, cls: Class, editor: 'SchoolTimetableEditor'):
        super().__init__()
        
        self.cls = cls
        self.editor = editor
        self.timetable, self.timetable_remains = SCHOOL.timetables_data[self.cls.id]
        
        settings_width = 200
        
        self.remainder_widget = BaseScrollWidget()
        self.remainder_widget.setFixedWidth(settings_width)
        self.remainder_widget.getScrollWidget().setFixedWidth(settings_width)
        self.remainder_widget.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.remainder_widget.addStretch()
        
        self.remainder_labels: list[_ExtrasDraggableSubjectLabel] = []
        
        self.period_amt = max(p_amt for p_amt, _ in self.cls.level.weekdays.values())
        self.weekdays_data = self.cls.level.weekdays
        self.weekdays = list(self.weekdays_data)
        
        self.setRowCount(self.period_amt)
        self.setColumnCount(len(self.cls.level.weekdays))
        self.setHorizontalHeaderLabels([day for day in self.cls.level.weekdays])
        self.setVerticalHeaderLabels([f"Period {i+1}" for i in range(self.rowCount())])
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self.rowCount() * 30 + 45)  # Adjust row height + header
        
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
    
    def set_period_amt(self, period_amt: int):
        for col, (day, (prev_period_amt, _)) in enumerate(self.weekdays_data.items()):
            if period_amt - prev_period_amt > 0:
                self.timetable[day] += [FreePeriod() for _ in range(period_amt - prev_period_amt)]
            elif period_amt - prev_period_amt < 0:
                for subj in self.timetable[day][period_amt - prev_period_amt:]:
                    if subj.id not in (FreePeriod.id, BreakPeriod.id):
                        self.timetable[day].remove(subj)
                        
                        self.addRemainder(subj)
            else:
                continue
            
            self.weekdays_data[day] = period_amt, self.weekdays_data[day][1]
        
        self.setRowCount(period_amt)
        self.setVerticalHeaderLabels([f"Period {i + 1}" for i in range(self.rowCount())])
        self.setFixedHeight(self.rowCount() * 30 + 45)
        
        for col in range(self.columnCount()):
            for row in range(self.rowCount()):
                if self.item(row, col) is None:
                    self.setItem(row, col, TimeTableItem(FreePeriod(), False, True))
        
        self.period_amt = period_amt
    
    def set_break_period(self, break_period: int):
        for col, (day, (_, prev_break_period)) in enumerate(self.weekdays_data.items()):
            self.timetable_exchange(self.item(prev_break_period - 1, col), self.item(break_period - 1, col))
            
            self.weekdays_data[day] = self.weekdays_data[day][0], break_period
    
    def update_break_time_color(self):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                
                if item.break_time:
                    item.set_color()
    
    def timetable_exchange(self, source_item: TimeTableItem, target_item: TimeTableItem):
        source_row, source_col = self.row(source_item), self.column(source_item)
        target_row, target_col = self.row(target_item), self.column(target_item)
        
        # Same timetable swap
        self.blockSignals(True)  # Prevent unnecessary updates
        
        # Remove old items
        self.takeItem(source_row, source_col)
        self.takeItem(target_row, target_col)
        
        # Create new items
        new_target = TimeTableItem(source_item.subject, source_item.subject.id == BreakPeriod.id, source_item.subject.id == FreePeriod.id)
        new_source = TimeTableItem(target_item.subject, target_item.subject.id == BreakPeriod.id, target_item.subject.id == FreePeriod.id)
        
        # Set new items
        self.setItem(target_row, target_col, new_target)
        self.setItem(source_row, source_col, new_source)
        
        # Background replacement
        source = self.timetable[self.weekdays[source_col]][source_row]
        target = self.timetable[self.weekdays[target_col]][target_row]
        self.timetable[self.weekdays[source_col]][source_row] = target
        self.timetable[self.weekdays[target_col]][target_row] = source
        
        if source_row == self.weekdays_data[self.weekdays[source_col]][1] - 1:
            self.weekdays_data[self.weekdays[source_col]] = self.weekdays_data[self.weekdays[source_col]][0], target_row + 1
        if target_row == self.weekdays_data[self.weekdays[target_col]][1] - 1:
            self.weekdays_data[self.weekdays[target_col]] = self.weekdays_data[self.weekdays[target_col]][0], source_row + 1
        
        # Force refresh
        self.blockSignals(False)
        self.update()
    
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
            
            if source is not None and  not source.locked and (self.editor.remainder_source_ref is not None or source.subject.id != FreePeriod.id):
                event.accept()
                if self.editor.remainder_source_ref is None:
                    self.current_source: tuple[TimeTableItem, Class] = source, self.cls
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            source_cls: ClassTimetable = event.source()
            
            col = self.columnAt(int(event.position().x()))
            row = self.rowAt(int(event.position().y()))
            
            _, break_time = self.weekdays_data[self.weekdays[col]]
            _, source_break_time = self.weekdays_data[self.weekdays[self.drag_source_col]]
            
            ignore = True
            if self.editor.remainder_source_ref is None:
                ignore = source_cls.cls.id != self.cls.id or (
                    self.drag_source_col != col and (
                        row == break_time - 1 or
                        source_break_time == self.drag_source_row + 1
                        )
                    )
            else:
                ignore = row == break_time - 1
            
            ignore = ignore or (self.weekdays[col], row + 1) in self.cls.locked_subjects
            
            if ignore:
                event.ignore()
            else:
                event.accept()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasText():
            if self.current_source is not None:
                source_item, source_cls = self.current_source
                
                target_row = self.rowAt(int(event.position().y()))
                target_col = self.columnAt(int(event.position().x()))
                target_item = self.item(target_row, target_col)
                
                # Handle swapping
                if target_item is not None and not target_item.locked and isinstance(target_item, TimeTableItem):
                    target_subject = target_item.subject
                    
                    if source_cls.id == self.cls.id:
                        self.timetable_exchange(source_item, target_item)
                        
                        event.accept()
                        
                        del target_item
            elif self.editor.remainder_source_ref is not None:
                row = self.rowAt(int(event.position().y()))
                col = self.columnAt(int(event.position().x()))
                target_item = self.item(row, col)
                
                self.blockSignals(True)  # Prevent unnecessary updates
                
                new_target = TimeTableItem(self.editor.remainder_source_ref.subject)
                
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
            
            self.editor.remainder_source_ref = None
            self.current_source = None
    
    def addRemainder(self, subject: Subject, index: int | None = None):
        remainder_label = _ExtrasDraggableSubjectLabel(subject)
        remainder_label.clicked.connect(self.editor.make_ds_func(remainder_label))
        
        if index is not None:
            self.remainder_widget.insertWidget(index, remainder_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.insert(index - 1, remainder_label)
            self.timetable_remains.insert(index - 1, subject)
        else:
            self.remainder_widget.insertWidget(len(self.remainder_widget.getChildren()) - 1, remainder_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.append(remainder_label)
            self.timetable_remains.append(subject)
    
    def removeRemainder(self, remainder: _ExtrasDraggableSubjectLabel):
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
        SCHOOL.fresh_timetable(self.cls)
        
        self.populate_timetable()
    
    def populate_timetable(self):
        for col, day in enumerate(self.weekdays_data):
            for row, subject in enumerate(self.timetable[day] + [FreePeriod() for _ in range(self.period_amt - len(self.timetable[day]))]):
                item = TimeTableItem(subject, subject.id == BreakPeriod.id, subject.id == FreePeriod.id, (self.weekdays[col], row + 1) in self.cls.locked_subjects)
                
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
                free_period_subject = FreePeriod()
                
                row = self.row(item)
                col = self.column(item)
                
                self.addRemainder(item.subject)
                
                self.setItem(row, col, TimeTableItem(free_period_subject, False, True))
                
                self.timetable[self.weekdays[col]][row] = free_period_subject
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

class SchoolTimetableEditor(BaseWidget):
    def __init__(self):
        super().__init__()
        
        self._leave_updated = True
        
        self.remainder_source_ref: TimeTableItem = None
        
        # self.cls_levels_data: dict[str, dict[str, bool]] = {}
        self.class_generator_threads: dict[ID, Thread] = {}
        
        # Create scroll area for timetables
        self.scroll_area = BaseScrollWidget()
        self.scroll_area.getScrollWidget().setWidgetResizable(True)
        self.scroll_area.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.addStretch()
        self.scroll_area.setSpacing(20)
        
        # Create timetable for each class
        self.label_data: dict[ID, QLabel] = {}
        self.timetable_widgets: dict[ID, dict[ID, ClassTimetable]] = {}
        self.classes_widget: dict[ID, tuple[WidgetDropdown, BaseWidget, dict[str, BaseWidget]]] = {}
        
        # Create settings for timetables
        self.settings_widget = TimetableSettings(self)
        
        self.addWidget(self.settings_widget)
        self.addWidget(self.scroll_area)
    
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
            
            drag.exec()
        
        return func
    
    def make_timetable_settings(self, cls_level: ClassLevel):
        widget_menu = MenuFrame()
        layout = widget_menu.layout()
        
        # break_updateable = True
        
        def generating_finished():
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.populate_timetable()
            
            self.class_generator_threads.pop(cls_level.id)
            
        def period_amt_changed(curr_period_amt: int):
            # global break_updateable
            
            breakperiod_edit.max_num = curr_period_amt
            if curr_period_amt < breakperiod_edit.number():
                # break_updateable = False
                breakperiod_edit.setNumber(curr_period_amt)
                # break_updateable = True
            
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.set_period_amt(curr_period_amt)
        
        def break_period_changed(curr_break_period: int):
            # if break_updateable:
                for ttbl in self.timetable_widgets[cls_level.id].values():
                    ttbl.set_break_period(curr_break_period)
        
        def generate_new_func():
            if cls_level.id not in self.class_generator_threads:
                if not self.settings_widget.continue_with_irreversable_action():
                    QMessageBox.critical(self, "TimetableGeneratorError", "Variables and connections are not sufficient to generate a timetable")
                    
                    return
                
                self.class_generator_threads[cls_level.id] = Thread(self.window(), lambda: SCHOOL.generate_timetables(list(cls_level.classes)))
                self.class_generator_threads[cls_level.id].finished.connect(generating_finished)
                self.class_generator_threads[cls_level.id].start()
                
                return
            
            QMessageBox.critical(self, "Threading Error", "Level is already being generated")
        
        def clear_func():
            for ttbl in self.timetable_widgets[cls_level.id].values():
                ttbl.clear_timetable()
        
        # self.cls_levels_data[cls_level.id] = {
        #     "break-func": break_period_changed,
        #     "period-func": period_amt_changed
        # }
        
        period_amt_edit = NumberLineEdit(max(p_week for p_week, _ in cls_level.weekdays.values()), 1, 20)
        period_amt_edit.setPlaceholderText("Periods Amt")
        period_amt_edit.textChanged.connect(period_amt_changed)
        
        breakperiod_edit = NumberLineEdit(max(b_period for _, b_period in cls_level.weekdays.values()), period_amt_edit.min_num, period_amt_edit.number())
        breakperiod_edit.setPlaceholderText("Break period")
        breakperiod_edit.textChanged.connect(break_period_changed)
        
        # dotw_button = QPushButton("Weekdays")
        # dotw_button.clicked.connect(self.cls_levels_data[cls_level.id]["dotw"].exec)
        
        generate_new_button = QPushButton("Generate New Level")
        generate_new_button.clicked.connect(generate_new_func)
        
        clear_button = QPushButton("Clear Timetable")
        clear_button.clicked.connect(clear_func)
        
        layout.addWidget(period_amt_edit)
        layout.addWidget(breakperiod_edit)
        # layout.addSpacing(5)
        # layout.addWidget(dotw_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(20)
        layout.addWidget(generate_new_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(clear_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        return widget_menu
    
    def add_timetable_level(self, cls_level: ClassLevel):
        self.timetable_widgets[cls_level.id] = {}
        
        body_widget = BaseWidget()
        
        level_widget = WidgetDropdown(f"<span style='font-size: 40px'>{cls_level.name.full()}</span>", body_widget)
        level_widget.toogle_widget()
        self.label_data[cls_level.id] = level_widget.title_label
        
        self.classes_widget[cls_level.id] = level_widget, body_widget, {}
        
        toogle_button = QPushButton("☰")
        toogle_button.setProperty("class", "Timetable_DP_OptionText")
        
        settings_menu_widget = self.make_timetable_settings(cls_level)
        
        def toogle_menu():
            settings_menu_widget.set_pos(toogle_button.mapToGlobal(QPoint(-150, toogle_button.pos().y() + toogle_button.height())))
            settings_menu_widget.toogle()
        
        toogle_button.clicked.connect(toogle_menu)
        
        level_widget.header.addWidget(toogle_button)
        
        self.scroll_area.insertWidget(len(self.scroll_area.getChildren()) - 1, level_widget)
    
    def add_timetable_class(self, cls: Class):
        def generate_individual_taimetable():
            response = QMessageBox.warning(
                self,
                "Action Irreversible",
                    "This action cannot be reversed\n"
                    f"All timetable information in {cls.level.name.full()} {cls.name} will be overwritten\n",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
                                
            if response != QMessageBox.StandardButton.Yes:
                return
            
            SCHOOL.generate_timetables([(cls.level.id, cls.id)])
            self.timetable_widgets[cls.level.id][cls.id].populate_timetable()
        
        widget = BaseWidget()
        widget.setProperty("class", "TimetableWidget")
        
        class_header = QLabel(cls.name)
        class_header.setProperty("class", "Title")
        self.label_data[cls.id] = class_header
        
        # Create timetable
        class_widget = BaseWidget(QHBoxLayout)
        class_widget.setProperty("class", "NoBackground")
        
        sidebar_widget = BaseWidget()
        sidebar_widget.setProperty("class", "NoBackground")
        
        timetable = ClassTimetable(cls, self)
        self.timetable_widgets[cls.level.id][cls.id] = timetable
        
        generate_new_button = QPushButton("Generate New Timetable")
        generate_new_button.clicked.connect(generate_individual_taimetable)
        
        clear_button = QPushButton("Clear Timetalbe")
        clear_button.clicked.connect(timetable.clear_timetable)
        
        class_widget.addWidget(timetable)
        class_widget.addWidget(sidebar_widget)
        
        sidebar_widget.addWidget(timetable.remainder_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        sidebar_widget.addWidget(generate_new_button)
        sidebar_widget.addWidget(clear_button)
        
        widget.addWidget(class_header)
        widget.addWidget(class_widget)
        
        self.classes_widget[cls.level.id][1].addWidget(widget)
        self.classes_widget[cls.level.id][2][cls.id] = widget
    
    def delete_timetable_level(self, cls_level_id: ID):
        self.classes_widget[cls_level_id][0].delete()
        
        self.classes_widget.pop(cls_level_id)
        self.timetable_widgets.pop(cls_level_id)
    
    def delete_timetable_class(self, cls: Class):
        self.classes_widget[cls.level.id][2][cls.id].delete()
        
        self.timetable_widgets[cls.level.id].pop(cls.id)
        self.classes_widget[cls.level.id][2].pop(cls.id)
    
    def set_label_text(self, id: ID, name: str | ClassLevelName):
        self.label_data[id].setText(name if isinstance(name, str) else f"<span style='font-size: 60px'>{name.full()}</span>")



