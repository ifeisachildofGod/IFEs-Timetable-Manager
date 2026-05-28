
from imports import *

from widgets.user_interface import *
from utils import Thread


class _TimeTableItem(QTableWidgetItem):
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
            if self.locked:
                self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled | ~Qt.ItemFlag.ItemIsEnabled | ~Qt.ItemFlag.ItemIsSelectable)
            
            self.setText(self.subject.name.abbrev())
            self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if isinstance(self.subject, Subject):
                self.setToolTip(f"Name: {self.subject.name.full()}\nID: {self.subject.id}\nTeacher: {self.subject.teacher.name.full()}{"\nSubject Locked" if locked else ""}")
            else:
                name = "/".join([s.name.short() for s in self.subject.subjects]) if self.subject.name is None else self.subject.name.full()
                sub_subject_names = "\n".join([f"\tName: {s.name.full()}\n\tID: {s.id}\n" for s in self.subject.subjects])
                
                self.setToolTip(f"Name: {name}\nID: {self.subject.id}\nSubjects: {sub_subject_names}{"\nSubject Locked" if self.locked else ""}")
    
    def set_locked_state(self, state: bool):
        self.locked = state
        
        self.set_color(self.orig_color if not self.locked else None)
        
        if self.locked:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled | ~Qt.ItemFlag.ItemIsEnabled | ~Qt.ItemFlag.ItemIsSelectable)
        else:
            self.setFlags(self.orig_flags)
    
    def set_color(self, color: str | None = None):
        if self.break_time:
            color = QColor(THEME_MANAGER.pallete_get("fg2"))
        elif self.locked:
            color = QColor(THEME_MANAGER.pallete_get("fg3"))
        elif self.subject is None:
            color = QColor(THEME_MANAGER.pallete_get("disabled"))
        
        if color:
            self.setBackground(color)

class _ExtrasDraggableSubjectLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)
    
    def __init__(self, subject: Subject | CombinedSubject):
        super().__init__(subject.name)
        self.subject = subject
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("class", 'RemSubjectItem')
        if isinstance(self.subject, Subject):
            self.setToolTip(f"Name: {self.subject.name}\nID: {self.subject.id}\nTeacher: {self.subject.teacher.name}")
        else:
            name = "/".join([s.name.short() for s in self.subject.subjects]) if self.subject.name is None else self.subject.name.short()
            sub_subject_names = "\n".join([f"\tName: {s.name.full()}\n\tID: {s.id}\n" for s in self.subject.subjects])
            
            self.setToolTip(f"Name: {name}\nID: {self.subject.id}\nSubjects: {sub_subject_names}")
        
        self.setFixedSize(150, 40)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event)


class TimetableSettings(BaseWidget):
    def __init__(self, editor: 'SchoolTimetableEditor', progress_bar: ProgressBar):
        super().__init__()
        
        self.editor = editor
        
        self._can_generate_new = True
        
        self.settings_menu = MenuFrame()
        
        self.toogle_button = QPushButton("☰")
        self.toogle_button.setProperty("class", "Timetable_DP_OptionText")
        self.toogle_button.clicked.connect(self._toogle_self)
        
        self.addWidget(self.toogle_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        general_settings_widget = BaseWidget(QHBoxLayout)
        
        self.progress_bar = progress_bar
        
        left_option_widget = BaseWidget()
        
        update_break_period = True
        
        def periodamt_number_changed(number: int):
            global update_break_period
            
            for level_index in self.editor.classes_widget:
                self.editor.cls_levels_data[level_index]["period-func"](number)
            
            self.breakperiod_edit.max_num = number
            if self.breakperiod_edit.max_num < self.breakperiod_edit.number():
                update_break_period = False
                self.breakperiod_edit.setNumber(self.breakperiod_edit.max_num)
                update_break_period = True
        
        def breakperiod_number_changed(number: int):
            if update_break_period:
                for level_index in self.editor.classes_widget:
                    self.editor.cls_levels_data[level_index]["break-func"](number)
        
        self.period_amt_edit = NumberLineEdit(10, 1, 20)
        self.period_amt_edit.setPlaceholderText("Period amount")
        self.period_amt_edit.textChanged.connect(periodamt_number_changed)
        
        self.breakperiod_edit = NumberLineEdit(7, 1, self.period_amt_edit.number())  # Temporary
        self.breakperiod_edit.setPlaceholderText("Break period")
        self.breakperiod_edit.textChanged.connect(breakperiod_number_changed)
        
        left_sub_option_widget = BaseWidget(QHBoxLayout)
        
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
    
    def _number_edit_updates(self, name: str):
        def number_changed(number: int):
            for level_index in self.editor.classes_widget:
                self.editor.cls_levels_data[level_index][name](number)
            
            self.breakperiod_edit.max_num = self.period_amt_edit.number()
        
        return number_changed
    
    def _toogle_self(self):
        self.settings_menu.set_pos(self.toogle_button.mapToGlobal(QPoint(-470, self.toogle_button.height())))
        self.settings_menu.toogle()
    
    def generating_finished(self):
        self._can_generate_new = True
        
        for lvl_ttbl_content in self.timetable_widgets.values():
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
            max_subject_amt = sum(sum(sum(cls_lvl.subjects_occurence[s_id] for s_id in cls.subjects) for cls in cls_lvl.classes.values()) for _, cls_lvl in SCHOOL.class_levels)
            
            if not max_subject_amt or not self.continue_with_irreversable_action():
                if not max_subject_amt:
                    QMessageBox.critical(self, "TimetableGeneratorError", "Variables and connections are not sufficient to generate a timetable")
                
                return
            
            self.progress_bar.set_max(lambda: max_subject_amt)
            self.progress_bar.set_var_func(lambda: sum(sum(len(SCHOOL.timetables_data[cls_id]) for cls_id in cls_lvl.classes) for _, cls_lvl in SCHOOL.class_levels))
            self.progress_bar.start(100)
            
            self.generate_new = Thread(self.window(), self.generate)
            self.generate_new.finished.connect(self.generating_finished)
            self.generate_new.start()
            
            self._can_generate_new = False
            
            return
        
        QMessageBox.critical(self, "ThreadingError", "School Timetable is already being generated")

class ClassTimetable(QTableWidget):
    def __init__(self, cls: Class, editor: 'SchoolTimetableEditor', remainder_widget: BaseWidget):
        super().__init__()
        
        self.cls = cls
        self.editor = editor
        self.timetable, self.timetable_remains = SCHOOL.timetables_data[self.cls.id]
        
        self.remainder_widget = remainder_widget
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
    
    def set_period_amt(self, period_amt: int):
        for col, (day, (prev_period_amt, _)) in enumerate(self.weekdays_data.values()):
            if period_amt - prev_period_amt > 0:
                self.timetable[day] += [FreePeriod() for _ in range(period_amt - prev_period_amt)]
            elif period_amt > prev_period_amt < 0:
                for subj in self.timetable[day][period_amt - prev_period_amt:]:
                    self.timetable[day].remove(subj)
                    
                    self.add_remainder(subj)
            else:
                continue
            
            self.weekdays_data[day][0] = period_amt
        
        self.setRowCount(period_amt)
        self.setVerticalHeaderLabels([f"Period {i + 1}" for i in range(self.rowCount())])
        self.setFixedHeight(self.rowCount() * 30 + 45)
        
        for col in range(self.columnCount()):
            for row in range(self.rowCount()):
                if self.item(row, col) is None:
                    self.setItem(row, col, _TimeTableItem(FreePeriod(), False, True))
        
        self.period_amt = period_amt
    
    def set_breakperiod(self, break_period: int):
        for col, (_, prev_break_period) in enumerate(self.weekdays_data.values()):
            self.timetable_exchange(self.item(prev_break_period - 1, col), self.item(break_period - 1, col))
    
    def update_break_time_color(self):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                
                if item.break_time:
                    item.set_color()
    
    def timetable_exchange(self, source_item: _TimeTableItem, target_item: _TimeTableItem):
        source_row, source_col = self.row(source_item), self.column(source_item)
        target_row, target_col = self.row(target_item), self.column(target_item)
        
        # Same timetable swap
        self.blockSignals(True)  # Prevent unnecessary updates
        
        # Remove old items
        self.takeItem(source_row, source_col)
        self.takeItem(target_row, target_col)
        
        # Create new items
        new_target = _TimeTableItem(source_item.subject, source_item.subject.id == BreakPeriod.id, source_item.subject.id == FreePeriod)
        new_source = _TimeTableItem(target_item.subject, target_item.subject.id == BreakPeriod.id, target_item.subject.id == FreePeriod)
        
        # Set new items
        self.setItem(target_row, target_col, new_target)
        self.setItem(source_row, source_col, new_source)
        
        # Background replacement
        source = self.timetable[self.weekdays[source_col]][source_row]
        target = self.timetable[self.weekdays[target_col]][target_row]
        self.timetable[self.weekdays[source_col]][source_row] = target
        self.timetable[self.weekdays[target_col]][target_row] = source
        
        if source_row == self.weekdays_data[self.weekdays[source_col]][1] - 1:
            self.weekdays_data[self.weekdays[source_col]][1] = target_row + 1
        if target_row == self.weekdays_data[self.weekdays[target_col]][1] - 1:
            self.weekdays_data[self.weekdays[target_col]][1] = source_row + 1
        
        # Force refresh
        self.blockSignals(False)
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item and isinstance(item, _TimeTableItem) and item.subject:
                self.drag_source_col = self.column(item)
                self.drag_source_row = self.row(item)
                
                # Store original position
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(item.subject.name)
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
            
            source: _TimeTableItem = self.item(row, col)
            
            if source is not None and (self.editor.remainder_source_ref is not None or source.subject.id != FreePeriod.id):
                event.accept()
                if self.editor.remainder_source_ref is None:
                    self.current_source: _TimeTableItem = source
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            source_cls: ClassTimetable = event.source()
            
            col = self.columnAt(int(event.position().x()))
            row = self.rowAt(int(event.position().y()))
            
            ignore = True
            if self.editor.remainder_source_ref is None:
                ignore = source_cls.cls.id != self.cls.id or (
                    self.drag_source_col != col and (
                        row == self.cls.breakTimePeriods[col] - 1 or
                        self.cls.breakTimePeriods[self.drag_source_col] == self.drag_source_row + 1
                        )
                    )
            else:
                ignore = row == self.cls.breakTimePeriods[col] - 1
            
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
                
                source_class = self.editor.timetable_widgets[self.cls.id].cls
                
                # Handle swapping
                if target_item is not None and isinstance(target_item, _TimeTableItem):
                    target_subject = target_item.subject
                    
                    if source_class == self.cls:
                        self.timetable_exchange(self.current_source, target_item)
                        
                        event.accept()
                        
                        del target_item
            elif self.editor.remainder_source_ref is not None:
                row = self.rowAt(int(event.position().y()))
                col = self.columnAt(int(event.position().x()))
                target_item = self.item(row, col)
                
                self.blockSignals(True)  # Prevent unnecessary updates
                
                new_target = _TimeTableItem(self.editor.remainder_source_ref.subject)
                
                self.takeItem(row, col)
                self.setItem(row, col, new_target)
                
                if isinstance(target_item, _TimeTableItem) and not target_item.free_period:
                    target_subject = target_item.subject
                    
                    # Create new items
                    new_source = _ExtrasDraggableSubjectLabel(target_subject)
                    new_source.clicked.connect(self.editor.make_ds_func(new_source))
                    
                    # Set new items
                    self.add_remainder(new_source, self.remainder_widget.indexOf(self.editor.remainder_source_ref))
                    
                    self.timetable[self.weekdays[col]][row] = FreePeriod()
                
                # Remove remainder widget
                self.remove_remainder(self.editor.remainder_source_ref)
                
                self.remainder_widget.update()
                
                self.blockSignals(False)
                
                self.timetable[self.weekdays[row]][col] = self.editor.remainder_source_ref.subject
                
                event.accept()
            
            self.editor.remainder_source_ref = None
            self.current_source = None
    
    def add_remainder(self, remainder: _ExtrasDraggableSubjectLabel, index: int | None = None):
        if index is not None:
            self.remainder_widget.insertWidget(index, remainder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.insert(index - 1, remainder)
            self.timetable_remains.insert(index - 1, remainder.subject)
        else:
            self.remainder_widget.insertWidget(self.remainder_widget.getLayout().count() - 1, remainder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.append(remainder)
            self.timetable_remains.append(remainder.subject)
    
    def remove_remainder(self, remainder: _ExtrasDraggableSubjectLabel):
        self.remainder_labels.remove(remainder)
        self.remainder_widget.removeWidget(remainder)
        self.timetable_remains.remove(remainder.subject)
        
        remainder.deleteLater()
    
    def clear_remains(self):
        for widg in self.remainder_widget.getChildren():
            self.remainder_widget.removeWidget(widg)
            widg.deleteLater()
        
        for widg in self.remainder_labels.copy():
            self.remainder_labels.remove(widg)
            widg.deleteLater()
        
        self.timetable_remains.clear()
    
    def clear_timetable(self):
        SCHOOL.fresh_timetable(self.cls)
        self.populate_timetable()
    
    def populate_timetable(self):
        for col, day in enumerate(self.weekdays_data):
            for row, subject in enumerate(self.timetable[day] + [FreePeriod() for _ in range(self.period_amt - len(self.timetable[day]))]):
                item = _TimeTableItem(subject, subject.id == BreakPeriod.id, subject.id == FreePeriod.id, subject.id in self.cls.locked_subjects)
                self.setItem(row, col, item)
        
        self.clear_remains()
        
        for subject in self.timetable_remains:
            subject_label = _ExtrasDraggableSubjectLabel(subject)
            subject_label.clicked.connect(self.editor.make_ds_func(subject_label))
            
            self.add_remainder(subject_label)
    
    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        
        if item and isinstance(item, _TimeTableItem) and not item.free_period and not item.break_time:
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
            
            if action == delete_action:
                free_period_subject = FreePeriod()
                
                row = self.row(item)
                col = self.column(item)
                
                subject_label = _ExtrasDraggableSubjectLabel(item.subject)
                subject_label.clicked.connect(self.editor.make_ds_func(subject_label))
                
                self.add_remainder(subject_label)
                
                self.setItem(row, col, _TimeTableItem(free_period_subject, False, True))
                
                self.timetable[self.weekdays[col]][row] = free_period_subject
            elif action == lock_period_action:
                item.set_locked_state(True)
                self.cls.locked_subjects[item.subject.id] = self.weekdays[item.column()], item.row()
            elif action == unlock_period_action:
                item.set_locked_state(False)
                self.cls.locked_subjects.pop(item.subject.id)
            elif action == goto_subject_action:
                pass
            elif action == goto_teacher_action:
                pass


class SchoolTimetableEditor(BaseWidget):
    def __init__(self):
        super().__init__()
        
        progress_bar_widget = BaseWidget()
        
        self.progress_bar = ProgressBar(progress_bar_widget)
        
        progress_label = QLabel("Generating...")
        progress_label.setStyleSheet("font-weight: bold;")
        
        progress_bar_widget.addWidget(progress_label)
        progress_bar_widget.addWidget(self.progress_bar)
        progress_bar_widget.addStretch()
        
        self._leave_updated = True
        
        self.remainder_source_ref: _TimeTableItem = None
        
        # self.cls_levels_data: dict[str, dict[str, bool]] = {}
        self.class_generator_threads: dict[ID, Thread] = {}
        
        # Create scroll area for timetables
        self.scroll_area = BaseScrollWidget()
        self.scroll_area.getScrollWidget().setWidgetResizable(True)
        self.scroll_area.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSpacing(20)
        
        # Create timetable for each class
        self.label_data: dict[ID, QLabel] = {}
        self.timetable_widgets: dict[ID, dict[ID, ClassTimetable]] = {}
        self.classes_widget: dict[ID, tuple[BaseWidget, dict[str, BaseWidget]]] = {}
        
        for _, cls_level in SCHOOL.class_levels:
            self.add_timetable_level(cls_level)
            
            for cls in cls_level.classes.values():
                self.add_timetable_class(cls)
        
        # Create settings for timetables
        self.settings_widget = TimetableSettings(self, self.progress_bar)
        
        self.addWidget(self.settings_widget)
        self.addWidget(progress_bar_widget)
        self.addWidget(self.scroll_area)
    
    def make_ds_func(self, label: _ExtrasDraggableSubjectLabel):
        def func(event):
            self.remainder_source_ref = label
            
            drag = QDrag(label)
            mime_data = QMimeData()
            mime_data.setText(label.subject.name)
            drag.setMimeData(mime_data)
            
            # Create drag feedback
            pixmap = label.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            
            drag.exec()
        
        return func
    
    def _make_timetable_settings(self, cls_level: ClassLevel):
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
                    ttbl.set_breakperiod(curr_break_period)
        
        def generate_new_func():
            if cls_level.id not in self.class_generator_threads:
                max_subject_amt = sum(sum(cls_level.subjects_occurence[s_id].week_max for s_id in cls.subjects) for cls in cls_level.classes.values())
                
                if not max_subject_amt or not self.settings_widget.continue_with_irreversable_action():
                    if not max_subject_amt:
                        QMessageBox.critical(self, "TimetableGeneratorError", "Variables and connections are not sufficient to generate a timetable")
                    return
                
                self.progress_bar.set_max(lambda: max_subject_amt)
                self.progress_bar.set_var_func(lambda: sum(len(SCHOOL.timetables_data[cls.id][0]) - 1 for cls in cls_level.classes.values()))
                self.progress_bar.start(100)
                
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
        
        body_widget = BaseWidget(QHBoxLayout)
        
        level_widget = WidgetDropdown(f"<span style='font-size: 60px'>{cls_level.name.full()}</span>", body_widget)
        self.label_data[cls_level.id] = level_widget.title_label
        
        self.classes_widget[cls_level.id] = body_widget, {}
        
        section_header = BaseWidget(QHBoxLayout)
        section_header.setProperty("class", "SectionHeader")
        section_header.setStyleSheet("QWidget.SectionHeader {background: none} QLabel {background: none}")
        
        toogle_button = QPushButton("☰")
        toogle_button.setProperty("class", "Timetable_DP_OptionText")
        
        settings_menu_widget = self._make_timetable_settings(cls_level)
        
        def toogle_menu():
            settings_menu_widget.set_pos(toogle_button.mapToGlobal(QPoint(-150, toogle_button.pos().y() + toogle_button.height())))
            settings_menu_widget.toogle()
        
        toogle_button.clicked.connect(toogle_menu)
        
        level_widget.header.addWidget(section_header)
        
        self.scroll_area.addWidget(level_widget)
        
    def add_timetable_class(self, cls: Class):
        def generate_individual_taimetable():
            response = QMessageBox.warning(
                self,
                "Action Irreversible",
                    "This action cannot be reversed\n"
                    "All information will be overwritten\n"
                    f"Are you sure you want to generate new timetable for {cls.name}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
                                
            if response != QMessageBox.StandardButton.Yes:
                return
            
            SCHOOL.generate_timetables([cls.id])
            self.timetable_widgets[cls.level.id][cls.id].populate_timetable()
        
        widget = BaseWidget()
        widget.setProperty("class", "TimetableWidget")
        
        settings_width = 200
        
        class_header = QLabel(cls.name)
        class_header.setProperty("class", "Title")
        self.label_data[cls.id] = class_header
        
        # Create timetable
        class_widget = BaseWidget(QHBoxLayout)
        class_widget.setProperty("class", "NoBackground")
        
        sidebar_widget = BaseWidget()
        sidebar_widget.setProperty("class", "NoBackground")
        
        remainder_widget = BaseScrollWidget()
        remainder_widget.setFixedWidth(settings_width)
        remainder_widget.getScrollWidget().setFixedWidth(settings_width)
        remainder_widget.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        timetable = ClassTimetable(cls, self, remainder_widget)
        self.timetable_widgets[cls.level.id][cls.id] = timetable
        
        remainder_title = QLabel("Remaining Subjects")
        remainder_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        generate_new_button = QPushButton("Generate New Timetable")
        generate_new_button.clicked.connect(generate_individual_taimetable)
        
        clear_button = QPushButton("Clear Timetalbe")
        clear_button.clicked.connect(timetable.clear_timetable)
        
        remainder_widget.addWidget(remainder_title, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        remainder_widget.addStretch()
        
        class_widget.addWidget(timetable)
        class_widget.addWidget(sidebar_widget)
        
        sidebar_widget.addWidget(remainder_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        sidebar_widget.addWidget(generate_new_button)
        sidebar_widget.addWidget(clear_button)
        
        widget.addWidget(class_header)
        widget.addWidget(class_widget)
        
        self.classes_widget[cls.level.id][0].addWidget(widget)
        self.classes_widget[cls.level.id][1][cls.id] = widget
    
    def delete_timetable_level(self, cls_level: ClassLevel):
        self.classes_widget[cls_level.id][0].delete()
        
        self.classes_widget.pop(cls_level.id)
        self.timetable_widgets.pop(cls_level.id)
    
    def delete_timetable_class(self, cls: Class):
        self.classes_widget[cls.level.id][1][cls.id].delete()
        
        self.timetable_widgets[cls.level.id].pop(cls.id)
        self.classes_widget[cls.level.id][1].pop(cls.id)
    
    def set_label_text(self, id: ID, name: str | ClassLevelName):
        self.label_data[id].setText(name if isinstance(name, str) else f"<span style='font-size: 60px'>{name.full()}</span>")



