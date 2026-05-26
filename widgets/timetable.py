
from imports import *

from widgets.user_interface import *
from utils import Thread


class _TimetableSettings(BaseWidget):
    def __init__(self, editor: 'SchoolTimetableEditor', progress_bar: ProgressBar, info: dict[str, list | dict[int, str]]):
        super().__init__()
        
        self.info = info
        
        self.editor = editor
        
        self._can_generate_new = True
        
        self.settings_menu = MenuFrame()
        
        self.toogle_button = QPushButton("☰")
        self.toogle_button.setProperty("class", "Timetable_DP_OptionText")
        self.toogle_button.clicked.connect(self._toogle)
        
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
        
        def closed_func():
            self.info = self.days_of_the_week_selector.get()
        
        self.days_of_the_week_selector = OptionSelector("Days of the week", self.info)
        self.days_of_the_week_selector.closed.connect(closed_func)
        
        dotw_button = QPushButton("Days of the Week")
        dotw_button.clicked.connect(self.days_of_the_week_selector.exec)
        
        left_sub_option_widget.addWidget(dotw_button)
        
        left_option_widget.addWidget(self.period_amt_edit)
        left_option_widget.addWidget(self.breakperiod_edit)
        left_option_widget.addWidget(left_sub_option_widget)
        
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
    
    def _generating_finished(self):
        self._can_generate_new = True
        self.editor._set_school_timetable()
    
    def _toogle(self):
        self.settings_menu.set_pos(self.toogle_button.mapToGlobal(QPoint(-470, self.toogle_button.height())))
        self.settings_menu.toogle()
    
    def clear_all_timetables(self):
        for ttbl in self.editor.timetable_widgets.values():
            ttbl.clear_timetable()
    
    def _generate(self):
        for ttbl in self.editor.timetable_widgets.values():
            ttbl.clear_remainder()
        
        self.editor.school.generateNewSchoolTimetables()
    
    def _continue_with_irreversable_action(self):
        return QMessageBox.StandardButton.Yes == QMessageBox.warning(self, "Action Irreversible", "This action cannot be reversed\n"
                                                                                                  "All information will be overwritten",
                                                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    def generate_new_school_timetable(self):
        if self._can_generate_new:
            self._can_generate_new = False
            
            max_subject_amt = 0
            for timetable_editor in self.editor.timetable_widgets.values():
                max_subject_amt += timetable_editor.get_total_subject_amount()
                        
            if not max_subject_amt:
                QMessageBox.critical(self, "Generator Error", "Variables and connections are not sufficient to generate a timetable")
                
                self._can_generate_new = True
                return
            
            if not self._continue_with_irreversable_action():
                self._can_generate_new = True
                return
            
            def total_subject_func():
                total_subjects = 0
                for timetable_editor in self.editor.timetable_widgets.values():
                    total_subjects += timetable_editor.get_max_subject_amount()
                
                return total_subjects
            
            self.progress_bar.set_max(lambda: max_subject_amt)
            self.progress_bar.set_var_func(total_subject_func)
            self.progress_bar.start(100)
            
            self.generate_new = Thread(self.editor.main_window, self._generate)
            self.generate_new.finished.connect(self._generating_finished)
            self.generate_new.start()
        else:
            QMessageBox.warning(self, "Generating", "Timetable is already being generated")

class _TimeTableItem(QTableWidgetItem):
    def __init__(self, subject: Subject, break_time: bool = False, free_period: bool = False):
        super().__init__()
        self.subject = subject
        self.break_time = break_time
        self.free_period = free_period
        
        self.setFlags(self.flags() & Qt.ItemFlag.ItemIsEnabled)
        
        if self.break_time:
            self.set_color()
        elif self.free_period:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable)
        
        # I check if subject is None seperately bcos of when the break time is checked
        
        if self.break_time:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled & ~Qt.ItemFlag.ItemIsEnabled & ~Qt.ItemFlag.ItemIsSelectable)
        elif not self.free_period:
            locked = self.subject.lockedPeriod is not None
            
            if locked:
                color = QColor(THEME_MANAGER.parse_stylesheet("{fg4}"))
                self.setBackground(color)
            
            self.setText(self.subject.name)
            self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if isinstance(self.subject, Subject):
                self.setToolTip(f"Name: {self.subject.name}\nID: {self.subject.id}\nTeacher: {self.subject.teacher.name}{"\nSubject Locked" if locked else ""}")
            else:
                name = "/".join([s.name for s in self.subject.subjects]) if self.subject.name is None else self.subject.name
                sub_subject_names = "\n".join([f"\tName: {s.name}\n\tID: {s.id}\n" for s in self.subject.subjects])
                
                self.setToolTip(f"Name: {name}\nID: {self.subject.id}\nSubjects: {sub_subject_names}{"\nSubject Locked" if locked else ""}")

    def set_color(self, color: str | None = None):
        color = QColor(THEME_MANAGER.parse_stylesheet("{fg1}") if color is None else color)
        self.setBackground(color)

class _ExtrasDraggableSubjectLabel(QLabel):
    clicked = pyqtSignal(QMouseEvent)
    
    def __init__(self, subject: Subject):
        super().__init__(subject.name)
        self.subject = subject
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("class", 'RemSubjectItem')
        if isinstance(self.subject, Subject):
            self.setToolTip(f"Name: {self.subject.name}\nID: {self.subject.id}\nTeacher: {self.subject.teacher.name}")
        else:
            name = "/".join([s.name for s in self.subject.subjects]) if self.subject.name is None else self.subject.name
            sub_subject_names = "\n".join([f"\tName: {s.name}\n\tID: {s.id}\n" for s in self.subject.subjects])
            
            self.setToolTip(f"Name: {name}\nID: {self.subject.id}\nSubjects: {sub_subject_names}")
        
        self.setFixedSize(150, 40)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event)


class ClassTimetable(QTableWidget):
    def __init__(self, cls: Class, editor: 'SchoolTimeTableEditor', remainder_layout: QVBoxLayout):
        super().__init__()
        
        self.cls = cls
        self.editor = editor
        self.timetable = cls.timetable
        
        self.remainder_layout = remainder_layout
        self.remainder_labels: list[_ExtrasDraggableSubjectLabel] = []
        
        self.periods = max(self.timetable.periodsPerDay)
        
        # Configure table
        self.setRowCount(max(self.timetable.periodsPerDay))
        self.setColumnCount(len(self.timetable.weekInfo))
        self.setHorizontalHeaderLabels([day[0] for day in self.timetable.weekInfo])
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
        
        for col in range(len(self.timetable.table)):
            self.timetable.correct(col)
        
        # Variables
        self.current_source = None
    
    def get_max_subject_amount(self):
        periods, break_periods, _ = self.editor.school.project["levels"][self.cls.index][1]
        
        max_subject_amt = 0
        
        for index, total_periods in enumerate(periods):
            max_subject_amt += total_periods - (1 if break_periods[index] <= total_periods else 0)
        
        return max_subject_amt
    
    def get_total_subject_amount(self):
        total_subject_amt = 0
        
        for subjects in self.cls.timetable.table.values():
            total_subject_amt += sum(s.total for s in subjects) - 1  # 1 is subtracted to acount for the break period
        
        return total_subject_amt
    
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
        new_target = _TimeTableItem(source_item.subject, source_item.subject.id == BREAK_PERIOD_ID, source_item.subject.id == FREE_PERIOD_ID)
        new_source = _TimeTableItem(target_item.subject, target_item.subject.id == BREAK_PERIOD_ID, target_item.subject.id == FREE_PERIOD_ID)
        
        # Set new items
        self.setItem(target_row, target_col, new_target)
        self.setItem(source_row, source_col, new_source)
        
        # Middle timetable replacement
        self.timetable.swap(source_row, source_col, target_row, target_col)
        
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
            
            if source is not None and (self.editor.remainder_source_ref is not None or source.subject.id != FREE_PERIOD_ID):
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
                    self.add_remainder(new_source, self.remainder_layout.indexOf(self.editor.remainder_source_ref))
                    
                    self.timetable.replace(Subject(FREE_PERIOD_ID, "Free", 1, 0, None, self.cls), row, col)
                
                # Remove remainder widget
                self.remove_remainder(self.editor.remainder_source_ref)
                
                self.remainder_layout.update()
                
                self.blockSignals(False)
                
                replacement_subject = self.editor.remainder_source_ref.subject.copy()
                replacement_subject.total = 1
                
                self.timetable.replace(replacement_subject, row, col)
                
                event.accept()
            
            self.editor.remainder_source_ref = None
            self.current_source = None
    
    def add_remainder(self, remainder: _ExtrasDraggableSubjectLabel, index: int | None = None):
        remainder.subject.lockedPeriod = None
        
        if index is not None:
            self.remainder_layout.insertWidget(index, remainder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.insert(index - 1, remainder)
            self.timetable.remainderContent.insert(index - 1, remainder.subject)
        else:
            self.remainder_layout.insertWidget(self.remainder_layout.count() - 1, remainder, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            self.remainder_labels.append(remainder)
            self.timetable.remainderContent.append(remainder.subject)
    
    def remove_remainder(self, remainder: _ExtrasDraggableSubjectLabel):
        self.remainder_labels.remove(remainder)
        self.remainder_layout.removeWidget(remainder)
        self.timetable.remainderContent.remove(remainder.subject)
        
        remainder.deleteLater()
    
    def clear_remainder(self):
        for widg in self.remainder_layout.parentWidget().findChildren(_ExtrasDraggableSubjectLabel):
            self.remainder_layout.removeWidget(widg)
            widg.deleteLater()
        
        for widg in self.remainder_labels.copy():
            self.remainder_labels.remove(widg)
            widg.deleteLater()
        
        self.timetable.remainderContent.clear()
    
    def save_timetable(self):
        """Save current grid state back to timetable"""
        for col in range(self.columnCount()):
            subjects = []
            for row in range(self.rowCount()):
                item = self.item(row, col)
                if isinstance(item, _TimeTableItem) and item.subject:
                    if (subjects and subjects[-1].id != item.subject.id) or not subjects:
                        subjects.append(item.subject)
                        
                        if item.subject.id not in (FREE_PERIOD_ID, BREAK_PERIOD_ID):
                            coords = [
                                (col, row),
                                (item.subject.total, item.subject.perWeek),
                                len([1 for label in self.remainder_labels if label.subject.id == item.subject.id])
                            ]
                            
                            self.editor.school.project["subjects"][item.subject.id][1][str(self.cls.index)][2][self.cls.classID][1].append(coords)
    
    def clear_timetable(self):
        for day, period_amt, break_period in self.timetable.weekInfo:
            for subject in self.timetable.table[day]:
                if subject.id not in (FREE_PERIOD_ID, BREAK_PERIOD_ID):
                    for _ in range(subject.total):
                        self.timetable.remainderContent.append(subject)
            
            self.timetable.table[day] = (
                [Subject(FREE_PERIOD_ID, "Free", 1, 1, None, self.cls) for _ in range(break_period - 1)] +
                [Subject(BREAK_PERIOD_ID, "Break", 1, 1, None, self.cls)] +
                [Subject(FREE_PERIOD_ID, "Free", 1, 1, None, self.cls) for _ in range(period_amt - break_period)]
            )
        
        self.timetable.remainderContent.sort(key=lambda subj: subj.name)
        
        self.populate_timetable()
    
    def populate_timetable(self):
        """Load the timetable data into the grid"""
        for col, (day, _, _) in enumerate(self.timetable.weekInfo):
            total_s_names = list(flatten([[subj for _ in range(subj.total)] for subj in self.timetable.table[day]]))
            subjects = total_s_names + [Subject(FREE_PERIOD_ID, "Free", 1, 1, None, self.cls) for _ in range(max(self.timetable.periodsPerDay) - len(total_s_names))]
            
            for row, subject in enumerate(subjects):
                item = _TimeTableItem(subject, subject.id == BREAK_PERIOD_ID, subject.id == FREE_PERIOD_ID)
                self.setItem(row, col, item)
        
        rem_subjects = [subj for subj in self.timetable.remainderContent if subj.id != FREE_PERIOD_ID]
        
        self.clear_remainder()
        
        for subject in rem_subjects:
            subject_label = _ExtrasDraggableSubjectLabel(subject)
            subject_label.clicked.connect(self.editor.make_ds_func(subject_label))
            
            self.add_remainder(subject_label)
    
    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        
        if item and isinstance(item, _TimeTableItem) and not item.free_period and not item.break_time:
            menu = QMenu(self)
            
            lock_action = None
            unlock_action = None
            
            delete_action = menu.addAction("Delete")
            if item.subject.lockedPeriod:
                unlock_action = menu.addAction("Unlock Period")
            else:
                lock_action = menu.addAction("Lock to Period")
            goto_subject_action = menu.addAction("Go to Subject")
            goto_teacher_action = menu.addAction("Go to Teacher")
            
            action = menu.exec(self.viewport().mapToGlobal(pos))
            
            if action == delete_action:
                free_period_subject = Subject(FREE_PERIOD_ID, "Free", 1, 0, None, self.cls)
                
                row = self.row(item)
                col = self.column(item)
                
                # Move to remainders if deleted
                subject = item.subject.copy()
                subject.perWeek = 1
                
                subject_label = _ExtrasDraggableSubjectLabel(subject)
                subject_label.clicked.connect(self.editor.make_ds_func(subject_label))
                
                self.add_remainder(subject_label)
                
                self.setItem(row, col, _TimeTableItem(free_period_subject, False, True))
                
                self.timetable.replace(free_period_subject, row, col)
            elif lock_action is not None and action == lock_action:
                item.subject.lockedPeriod = [self.row(item), 1]  # Lock to current period
            elif unlock_action is not None and action == unlock_action:
                item.subject.lockedPeriod = None
            elif action == goto_subject_action:
                pass
            elif action == goto_teacher_action:
                pass

class SchoolTimetableEditor(BaseWidget):
    def __init__(self):
        super().__init__()
        
        self.info = info["variables"] if info is not None else {"DOTW": DOTW_DATA}
        
        self.school = school
        self.main_window = main_window
        
        progress_bar_widget = BaseWidget()
        
        self.progress_bar = ProgressBar(progress_bar_widget)
        
        progress_label = QLabel("Generating...")
        progress_label.setStyleSheet("font-weight: bold;")
        
        progress_bar_widget.addWidget(progress_label)
        progress_bar_widget.addWidget(self.progress_bar)
        progress_bar_widget.addStretch()
        
        self._leave_updated = True
        
        self.remainder_source_ref: _TimeTableItem = None
        
        self.cls_levels_data: dict[str, dict[str, bool | OptionSelector]] = {}
        self.class_generator_threads: dict[str, Thread] = {}
        
        # Create scroll area for timetables
        self.scroll_area = BaseScrollWidget()
        self.scroll_area.getScrollWidget().setWidgetResizable(True)
        self.scroll_area.getScrollWidget().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSpacing(20)
        
        # Create timetable for each class
        self.timetable_parent_widget: dict[str, BaseWidget] = {}
        self.timetable_widgets: dict[str, ClassTimetable] = {}
        self.classes_widget: dict[int, tuple[BaseWidget, dict[str, BaseWidget]]] = {}
        
        for cls in self.school.classes.values():
            widget = self._make_timetable_for_each_class(cls)
            self.classes_widget[cls.index][0].addWidget(widget)
        
        # Create settings for timetables
        self.settings_widget = _TimetableSettings(self, self.progress_bar, self.info["DOTW"])
        
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
    
    def _make_timetable_settings(self, lvl_index: int):
        widget_menu = MenuFrame()
        layout = widget_menu.layout()
        
        break_updateable = True
        
        def _generating_finished():
            for ttbl in self.timetable_widgets.values():
                if ttbl.cls.index == lvl_index:
                    ttbl.populate_timetable()
            
            self.class_generator_threads.pop(lvl_index)
            
        def period_amt_changed(curr_period_amt: int):
            global break_updateable
            
            breakperiod_edit.max_num = curr_period_amt
            if curr_period_amt < breakperiod_edit.number():
                break_updateable = False
                breakperiod_edit.setNumber(curr_period_amt)
                break_updateable = True
            
            for ttbl in self.timetable_widgets.values():
                if ttbl.cls.index == lvl_index:
                    for col, (day, prev_period_amt, _) in enumerate(ttbl.cls.timetable.weekInfo):
                        if curr_period_amt < ttbl.cls.timetable.weekInfo[col][2]:
                            ttbl.timetable_exchange(ttbl.item(ttbl.cls.timetable.weekInfo[col][2] - 1, col), ttbl.item(ttbl.cls.timetable.weekInfo[col][2] - 2, col))
                        
                        Timetable.spread(ttbl.cls.timetable.table[day])
                        if prev_period_amt > curr_period_amt:
                            for s in ttbl.cls.timetable.table[day][curr_period_amt:]:
                                if s.id not in (BREAK_PERIOD_ID, FREE_PERIOD_ID):
                                    ttbl.add_remainder(_ExtrasDraggableSubjectLabel(s))
                            ttbl.cls.timetable.table[day][curr_period_amt:] = []
                        elif prev_period_amt < curr_period_amt:
                            rem_free_period = Subject(FREE_PERIOD_ID, "Free", curr_period_amt - prev_period_amt, 0, None, ttbl.cls)
                            
                            ttbl.cls.timetable.table[day].append(rem_free_period)
                        Timetable.flatten(ttbl.cls.timetable.table[day])
                        
                        ttbl.cls.timetable.weekInfo[col][1] = curr_period_amt
                        ttbl.cls.periodsPerDay[col] = curr_period_amt
                        ttbl.cls.timetable.periodsPerDay[col] = curr_period_amt
                        
                        ttbl.timetable.correct(col)
                    
                    ttbl.setRowCount(curr_period_amt)
                    ttbl.setVerticalHeaderLabels([f"Period {i + 1}" for i in range(ttbl.rowCount())])
                    ttbl.setFixedHeight(ttbl.rowCount() * 30 + 45)
                    
                    for col in range(ttbl.columnCount()):
                        for row in range(ttbl.rowCount()):
                            if ttbl.item(row, col) is None:
                                ttbl.setItem(row, col, _TimeTableItem(Subject(FREE_PERIOD_ID, "Free", 1, 0, None, ttbl.cls), False, True))
        
        def break_period_changed(curr_break_period: int):
            if break_updateable:
                for ttbl in self.timetable_widgets.values():
                    if ttbl.cls.index == lvl_index:
                        for col, (day, period_amt, prev_break_period) in enumerate(ttbl.cls.timetable.weekInfo):
                            prev_break_index = ttbl.cls.timetable.idFind(BREAK_PERIOD_ID, col)
                            
                            break_before_rem_periods = prev_break_period - sum(s.total for s in ttbl.cls.timetable.table[day][:prev_break_index]) - 1
                            if break_before_rem_periods:
                                ttbl.cls.timetable.table[day].insert(prev_break_index, Subject(FREE_PERIOD_ID, "Free", break_before_rem_periods, 0, None, ttbl.cls))
                            break_after_rem_periods = period_amt - sum(s.total for s in ttbl.cls.timetable.table[day])
                            if break_after_rem_periods:
                                ttbl.cls.timetable.table[day].append(Subject(FREE_PERIOD_ID, "Free", break_after_rem_periods, 0, None, ttbl.cls))
                            
                            prev_break_index = ttbl.cls.timetable.idFind(BREAK_PERIOD_ID, col)
                            
                            break_subject = ttbl.cls.timetable.table[day][prev_break_index]
                            
                            rem_periods = max(curr_break_period - sum(s.total for s in ttbl.cls.timetable.table[day]), 0)
                            if rem_periods:
                                free_subj = Subject(FREE_PERIOD_ID, "Free", rem_periods, 0, None, ttbl.cls)
                                ttbl.cls.timetable.table[day].append(free_subj)
                            
                            Timetable.spread(ttbl.cls.timetable.table[day])
                            ttbl.cls.timetable.table[day].pop(next(index for index, subj in enumerate(ttbl.cls.timetable.table[day]) if subj.id == break_subject.id))
                            ttbl.cls.timetable.table[day].insert(curr_break_period - 1, break_subject)
                            Timetable.flatten(ttbl.cls.timetable.table[day])
                            
                            ttbl.timetable_exchange(ttbl.item(ttbl.cls.timetable.weekInfo[col][2] - 1, col), ttbl.item(curr_break_period - 1, col))
        
        def generate_new_func():
            classes = []
            
            for ttbl in self.timetable_widgets.values():
                if ttbl.cls.index == lvl_index:
                    classes.append(ttbl.cls)
            
            def generate_new_level():
                for cls in classes:
                    self.school.generateTimetable(cls)
            
            if lvl_index not in self.class_generator_threads:
                response = QMessageBox.warning(self, "Action Irreversible", "This action cannot be reversed\n"
                                                                            "All information will be overwritten",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if response != QMessageBox.StandardButton.Yes:
                    return
                self.progress_bar.set_max(lambda: sum(ttbl.cls.timetable.periodsPerDay) - len(ttbl.cls.timetable.periodsPerDay))
                self.progress_bar.set_var_func(lambda: sum([sum([s.total for s in subjects]) - 1 for _, subjects in ttbl.cls.timetable.table.items()]))
                self.progress_bar.start(100)
                
                self.class_generator_threads[lvl_index] = Thread(self.main_window, generate_new_level)
                self.class_generator_threads[lvl_index].finished.connect(_generating_finished)
                self.class_generator_threads[lvl_index].start()
        
        def clear_func():
            for ttbl in self.timetable_widgets.values():
                if ttbl.cls.index == lvl_index:
                    ttbl.clear_timetable()
        
        self.cls_levels_data[lvl_index] = {
            "break-func": break_period_changed,
            "period-func": period_amt_changed,
            "dotw": OptionSelector("Day of the week", DOTW_DATA.copy())
        }
        
        period_amt_edit = NumberLineEdit(self.school.project["levels"][lvl_index][1][0][0], 1, 20)
        period_amt_edit.setPlaceholderText("Periods Amt")
        period_amt_edit.textChanged.connect(period_amt_changed)
        
        breakperiod_edit = NumberLineEdit(self.school.project["levels"][lvl_index][1][1][0], period_amt_edit.min_num, period_amt_edit.number())
        breakperiod_edit.setPlaceholderText("Break period")
        breakperiod_edit.textChanged.connect(break_period_changed)
        
        dotw_button = QPushButton("Weekdays")
        dotw_button.clicked.connect(self.cls_levels_data[lvl_index]["dotw"].exec)
        
        generate_new_button = QPushButton("Generate New Level")
        generate_new_button.clicked.connect(generate_new_func)
        
        clear_button = QPushButton("Clear Timetable")
        clear_button.clicked.connect(clear_func)
        
        layout.addWidget(period_amt_edit)
        layout.addWidget(breakperiod_edit)
        layout.addSpacing(5)
        layout.addWidget(dotw_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(20)
        layout.addWidget(generate_new_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(clear_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        return widget_menu
    
    def _make_timetable_for_each_class(self, cls: Class):
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
            
            self.school.generateTimetable(cls)
            self.timetable_widgets[cls.id].populate_timetable()
        
        widget = BaseWidget()
        widget.setProperty("class", "TimetableWidget")
        
        settings_width = 200
        
        class_header = QLabel(cls.className)
        class_header.setProperty("class", "Title")
        
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
        self.timetable_widgets[cls.id] = timetable
        self.timetable_parent_widget[cls.id] = widget
        
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
        
        if cls.index not in self.classes_widget:
            level_widget = BaseWidget()
            
            self.classes_widget[cls.index] = level_widget, {}
            
            level_widget.setProperty("class", "TimetableWidget")
            
            section_header = BaseWidget(QHBoxLayout)
            section_header.setProperty("class", "SectionHeader")
            section_header.setStyleSheet("QWidget.SectionHeader {background: none} QLabel {background: none}")
            
            toogle_button = QPushButton("☰")
            toogle_button.setProperty("class", "Timetable_DP_OptionText")
            
            settings_menu_widget = self._make_timetable_settings(cls.index)
            
            def toogle_menu():
                settings_menu_widget.set_pos(toogle_button.mapToGlobal(QPoint(-150, toogle_button.pos().y() + toogle_button.height())))
                settings_menu_widget.toogle()
            
            toogle_button.clicked.connect(toogle_menu)
            
            section_header.addWidget(QLabel(f"<span style='font-size: 60px'>{cls.namingConvention[cls.index]}</span>"))
            section_header.addWidget(toogle_button, alignment=Qt.AlignmentFlag.AlignRight)
            
            level_widget.addWidget(section_header)
            
            self.scroll_area.addWidget(level_widget)
        
        self.classes_widget[cls.index][1][cls.classID] = widget
        
        return widget





