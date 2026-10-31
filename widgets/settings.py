
from matplotlib.colors import get_named_colors_mapping

from AttendanceApp.base_widgets import BaseDataDisplayWidget
from AttendanceApp.communication import BaseCommSystem
from AttendanceApp.data_display_widgets import BarWidget, GraphWidget
from imports import *

from .base import *
from .settings_options import *

from AttendanceApp import AttendanceManager


_T = TypeVar("_T")


class _Prefect_PostEditor(BaseSettingDialog):
    def __init__(self, parent: StaffMainWidget, title: str, attendance_manager: AttendanceManager, post_cb: QComboBox):
        super().__init__(title)
        
        self.setFixedSize(650, 450)
        
        self.__init = True
        
        self.post_cb = post_cb
        self.attendance_manager = attendance_manager
        
        self.i_parent = parent
        
        self.post_widgets = []
        
        self.main_widget = BaseFlowGridWidget(4)
        self.main_widget.setVerticalSpacing(4)
        self.main_widget.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        add_new_pb = QPushButton("Add New")
        add_new_pb.clicked.connect(lambda: self.add_post(None))
        
        self.addWidget(self.main_widget)
        self.addWidget(add_new_pb, alignment=Qt.AlignmentFlag.AlignRight)
        
        for post_id in SCHOOL.posts:
            self.add_post(post_id)
        
        self.__init = False
    
    def _make_entry_action_funcs(self, entry: EditableCancelableEntry, id: ID):
        def update():
            post = SCHOOL.posts[id] = entry.get_text()
            
            index = self.post_cb.count() - 1
            curr_index = self.post_cb.currentIndex()
            
            for i in range(self.post_cb.count()):
                if self.post_cb.itemData(i) == id:
                    self.post_cb.removeItem(i)
                    
                    index = i
                    
                    break
            
            self.post_cb.insertItem(index, post, userData=id)
            
            if index == curr_index:
                self.post_cb.setCurrentIndex(index)
            
            self.i_parent.window().saved_state_changed.emit(True)
        
        def remove():
            SCHOOL.posts.pop(id)
            
            self.main_widget.removeWidget(entry)
            entry.deleteLater()
            
            for prefect_id, prefect in SCHOOL.prefects.items():
                if id == prefect.post_id:
                    prefect.post_id = None
                    self.attendance_manager.update_staff_list_prefect_post_name(prefect_id)
            
            curr_index = self.post_cb.currentIndex()
            
            for i in range(self.post_cb.count()):
                if self.post_cb.itemData(i) == id:
                    self.post_cb.removeItem(i)
                    
                    if i == curr_index:
                        self.post_cb.setCurrentIndex(self.post_cb.count() - 1)
                    
                    break
            
            self.i_parent.window().saved_state_changed.emit(True)
        
        return update, remove
    
    def add_post(self, post_id: Optional[ID]):
        p_id = post_id or NEW_ID()
        
        if p_id not in SCHOOL.posts:
            SCHOOL.posts[p_id] = ""
        
        post_name = SCHOOL.posts[p_id]
        
        post_entry = EditableCancelableEntry(post_name)
        
        update_option, remove_option = self._make_entry_action_funcs(post_entry, p_id)
        
        post_entry.finished_editing_signal.connect(update_option)
        post_entry.deleted.connect(remove_option)
        
        self.main_widget.addWidget(post_entry)
        
        if post_id is None:
            post_entry.start_editing()
        
        if not self.__init:
            self.i_parent.window().saved_state_changed.emit(True)

class _Staff_CardScanScreen(BaseWidget):
    iud_changed = pySignal(ID)
    comm_signal = pySignal(str)
    
    def __init__(self, entry: _T, parent: SettingsScreen, comm_system: BaseCommSystem):
        super().__init__()
        
        top_widget = BaseWidget(QHBoxLayout)
        
        self.cancel_button = BaseWidget() ; self.cancel_button.addWidget(QLabel("<span style='font-size: 30px; font-weight: bold;'>×</span>"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.cancel_button.setFixedSize(40, 40)
        self.cancel_button.setContentsMargins(0, 0, 0, 0)
        self.cancel_button.setProperty("class", "CancelButton NoBG SpecialBG1Hover BorderRadiused")
        self.cancel_button.enableCursorPointing()
        self.cancel_button.clicked.connect(self.go_back)
        
        top_widget.addStretch()
        top_widget.addWidget(self.cancel_button)
        
        self.entry = entry
        self._parent = parent
        self.comm_system = comm_system
        
        self.just_scanned = False
        
        scan_img = Image("AttendanceApp/src/images/scan.png", height=330)
        scan_img.setStyleSheet("margin-bottom: 20px;")
        
        instruction_label = QLabel("Scan RFID card")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_label = QLabel(f"""
            <span style='font-size: 20px; font-weight: 500; text-align: left;'>
                <span style='font-weight: bold; color: {THEME_MANAGER.pallete_get('fg2')};'>ID:</span>{self.entry.id} <br>
                <span style='font-weight: bold; color: {THEME_MANAGER.pallete_get('fg2')};'>Name:</span>{self.entry.name.full()}
            </span>
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.addWidget(top_widget)
        self.addWidget(scan_img, alignment=Qt.AlignmentFlag.AlignCenter)
        self.addWidget(instruction_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.addWidget(info_label, Qt.AlignmentFlag.AlignCenter)
        
        self.comm_signal.connect(self.scanned)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.comm_system.connection_changed_signal.connect(self.connection_changed)
        self.is_iud_changed = False
        
        for opt_info in self._parent.i_parent.window().option_buttons:
            if opt_info is not None:
                btn, _ = opt_info
                btn.clicked.connect(self.clean_up)
    
    def _deactivate_just_scanned(self):
        self.just_scanned = False
    
    def clean_up(self):
        self._parent.stack.removeWidget(self)
        self.deleteLater()
        
        self._parent.card_scan_screen_closed.emit()
        self._parent.card_scan_screen = None
        
        for opt_info in self._parent.i_parent.window().option_buttons:
            if opt_info is not None:
                btn, _ = opt_info
                btn.clicked.disconnect(self.clean_up)
    
    def go_back(self):
        if self.is_iud_changed:
            self.comm_system.send_message("REGISTERED")
            
            self.just_scanned = True
            QTimer.singleShot(500, self._deactivate_just_scanned)
        
        self._parent.stack.setCurrentIndex(1)
        self.clean_up()
    
    def connection_changed(self, state: bool):
        if not state and self._parent.stack.indexOf(self) == self._parent.stack.currentIndex():
            self.go_back()
    
    def scanned(self, iud: str):
        if self._parent.stack.currentIndex() == self._parent.stack.indexOf(self):
            for staff in list(SCHOOL.teachers.values()) + list(SCHOOL.prefects.values()):
                if staff.IUD == iud:
                    self.comm_system.send_message("UNREGISTERED")
                    self.just_scanned = True
                    
                    QTimer.singleShot(1000, lambda: self.comm_system.send_message("Card has already_ been assigned "))
                    
                    QMessageBox.warning(self, "KeyError", f"Card of IUD {iud} has already been assigned to the {"teacher" if isinstance(staff, Teacher) else "prefect"}: {staff.name.full()}")
                    
                    QTimer.singleShot(500, self._deactivate_just_scanned)
                    self.is_iud_changed = False
                    self.go_back()
                    
                    return
            
            self.entry.IUD = ID(iud)
            self.iud_changed.emit(self.entry.IUD)
            
            self.is_iud_changed = True
            self.go_back()
            self.is_iud_changed = False
            
            self.window().saved_state_changed.emit(True)



class SubjectsSettingEntry(BaseSettingEntry[Subject]):
    def __init__(self, parent: SubjectsMainWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Subject",
            ["Full Name", "Abbreviation"],
            [
                ("Teachers who can teach this subject", (Subject_SelectionList, (self.timetable_editor, self.attendance_manager), None)),
                ("Classes offering this subject", (Subject_DropdownCheckBoxes, (self.timetable_editor, self.attendance_manager, ), Qt.AlignmentFlag.AlignCenter)),
            ],
            entry,
            stack
        )

        self.addProperty("class", "SubjectSettingsEntry")
    
    def open_settings(self):
        settings_screen = super().open_settings()
        
        if self.entry.name.abbrev:
            settings_screen.toogle_name_format()
        
        return settings_screen
    
    def new(self):
        return Subject(NEW_ID(), SubjectName("", ""), None, {})
    
    def remove(self):
        delete_subject(self.id, self.timetable_editor, self.attendance_manager, self.i_parent)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, (self.entry.name.first, self.entry.name.abbrev)
    
    def get_repr_text(self):
        return f"{self.entry.name.first.strip() if self.entry.name.first else (self.entry.name.abbrev.strip() if self.entry.name.abbrev else "")}{f" ({self.entry.name.abbrev})" if self.entry.name.abbrev and self.entry.name.first else ""}"
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit]):
        self.entry.name.first = text
        
        full_name_e = extended_line_edits[0]
        full_name_e.setText(text)
    
    def extended_name_changed(self, index, text, simple_line_edit):
        match index:
            case 0:
                self.entry.name.first = text
                
                if text != simple_line_edit.text():
                    simple_line_edit.setText(text)
            case 1:
                self.entry.name.abbrev = text
        
        subject_name_update(self.id, self.timetable_editor, self.attendance_manager, self.i_parent)
    
    def extended_name_empty(self, index, text):
        key = f"E{index}EmptyNameWarning"
        
        match index:
            case 1:
                if self.settings_screen:
                    if text:
                        self.settings_screen.status_widget.removeLinient(key)
                    else:
                        self.settings_screen.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty (Switch to Short Name View)")

class CombinedSubjectsSettingEntry(BaseSettingEntry[CombinedSubject]):
    def __init__(self, parent: SubjectsMainWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Combined Subject",
            None,
            [
                ("Child subjects under this combined subject", (CombinedSubject_SelectionList, (self.timetable_editor, self.attendance_manager), None)),
                ("Classes offering this combined subject", (CombinedSubject_DropdownCheckBoxes, (self.timetable_editor, self.attendance_manager), Qt.AlignmentFlag.AlignCenter)),
            ],
            entry,
            stack
        )
        
        self.addProperty("class", "CombinedSubjectSettingsEntry")
    
    def open_settings(self):
        settings_screen = super().open_settings()
        
        if self.entry.subjects:
            settings_screen.simple_name_changed(settings_screen.simple_line_edit.text())
        
        return settings_screen
    
    def new(self):
        return CombinedSubject(NEW_ID(), CombinedSubjectName(None, None), [], {}, SCHOOL.settings.DEFAULT_occurance_data)
    
    def remove(self):
        delete_combined_subject(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, None

    def get_repr_text(self):
        return self.entry.name.first.strip() if self.entry.name.first else (self.entry.name.abbrev.strip() if self.entry.name.abbrev else "")
    
    def simple_name_changed(self, text, _):
        if text:
            self.entry.name.first = text
            self.entry.name.abbrev = None
        else:
            self.entry.name.first = None
            self.entry.name.abbrev = "/".join([s.name.short() for s in self.entry.subjects]) or None
        
        combined_subject_name_update(self.id, self.timetable_editor, self.attendance_manager, self)
    
    def simple_name_empty(self, text):
        if not self.entry.subjects:
            super().simple_name_empty(text)

class StaffSettingEntry[_T](BaseSettingEntry[_T]):
    card_scan_screen_opened = pySignal()
    card_scan_screen_closed = pySignal()
    
    def __init__(
        self,
        i_parent: BaseSettingWidget[_T],
        general_entry_name: str,
        extended_placeholders: list[str],
        custom_settings_format: list[tuple[str, tuple[type[BaseWidget], tuple, Qt.AlignmentFlag] | tuple[QWidget, Qt.AlignmentFlag]]],
        entry: Optional[_T],
        stack: QStackedWidget,
        attendance_manager: AttendanceManager
    ):
        
        self.card_scan_screen = None
        
        self.attendance_manager = attendance_manager
        
        super().__init__(i_parent, general_entry_name, extended_placeholders, custom_settings_format, entry, stack)
    
    def open_settings(self):
        settings_screen = super().open_settings()
        
        def open_card_scan():
            if not self.attendance_manager.comm_system.connected:
                QMessageBox.warning(self, "CardScannerError", "No device connected")
                
                return
            
            self.card_scan_screen = _Staff_CardScanScreen(self.entry, self, self.attendance_manager.comm_system)
            
            self.stack.addWidget(self.card_scan_screen)
            self.stack.setCurrentWidget(self.card_scan_screen)
            
            self.card_scan_screen_opened.emit()
        
        iud_set_btn = QPushButton("Set Teacher IUD")
        iud_set_btn.clicked.connect(open_card_scan)
        
        settings_screen.top_widget.addWidget(iud_set_btn)
        
        if self.entry.name.second or self.entry.name.third or self.entry.name.abbrev:
            settings_screen.toogle_name_format()
        
        return settings_screen
    
    def get_staff_attendance_data(self) -> tuple[dict[str, tuple[int, int], dict[str, float]]]:
        raise NotImplementedError()
    
    def get_staff_punctuality_data(self) -> list[tuple[int, str, list[float]]]:
        raise NotImplementedError()
    
    def new_stats_widgets(self) -> BaseWidget:
        raise NotImplementedError()
    
    def new_charts_widgets(self) -> BaseWidget:
        raise NotImplementedError()
    
    def get_init_text(self):
        return self.entry.name.first, (self.entry.name.first, self.entry.name.second, self.entry.name.third, self.entry.name.abbrev)
    
    def get_repr_text(self):
        return f"{self.entry.name.full().strip()}{f" ({self.entry.name.abbrev})" if self.entry.name.abbrev is not None and self.entry.name.abbrev.strip() else ""}"
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit, QLineEdit]):
        full_name_e = extended_line_edits[0]
        full_name_e.setText(text)
        
        for le in extended_line_edits[1:]:
            le.blockSignals(True)
            le.setText("")
            le.blockSignals(False)
        
        self.entry.name.second = None
        self.entry.name.third = None
        self.entry.name.abbrev = None
    
    def extended_name_changed(self, index, text, simple_line_edit):
        match index:
            case 0:
                self.entry.name.first = text
            case 1:
                self.entry.name.second = text
            case 2:
                self.entry.name.third = text
            case 3:
                self.entry.name.abbrev = text
        
        teacher_name_update(self.id, self.timetable_editor, self.attendance_manager)
        
        if self.settings_screen and self.settings_screen.extended_edits_widget.isVisible():
            simple_line_edit.blockSignals(True)
            simple_line_edit.setText(f"{self.entry.name.first or ""}{" " + self.entry.name.second if self.entry.name.second is not None else ""}{" " + self.entry.name.third if self.entry.name.third is not None else ""}")
            simple_line_edit.blockSignals(False)
    
    def extended_name_empty(self, index, text):
        if self.settings_screen:
            key = f"E{index}EmptyNameWarning"

            if text:
                self.settings_screen.status_widget.removeLinient(key)
            
            match index:
                case 0:
                    if not text and self.settings_screen.extended_edits_widget.isVisible():
                        self.settings_screen.status_widget.addMessage(Status.WARN, key, f"Surname is empty")
                case 1:
                    if not text:
                        self.settings_screen.status_widget.addMessage(Status.WARN, key, f"First name is empty")
                case 2:
                    if not text:
                        self.settings_screen.status_widget.addMessage(Status.WARN, key, f"Other name is empty")
                case 3:
                    if not text:
                        self.settings_screen.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty")

class ClassLevelsSettingEntry(BaseSettingEntry[ClassLevel]):
    def __init__(self, parent: ClassLevelsMainWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Class Level",
            None,
            [
                ("Create and edit the classes in this level", (ClassLevel_ClassMaker, (self.timetable_editor, self.attendance_manager), Qt.AlignmentFlag.AlignCenter)),
                ("Edit occurence of the subjects under this level during the week", (ClassLevel_OccuranceEditor, (self.timetable_editor, self.attendance_manager), Qt.AlignmentFlag.AlignCenter))
            ],
            entry,
            stack
        )
        
        self.addProperty("class", "ClassLevelSettingsEntry")
    
    def new(self):
        return ClassLevel(NEW_ID(), ClassLevelName(), {}, {}, SCHOOL.settings.TIMETABLE_weekdays.copy(), SCHOOL.settings.DEFAULT_period_amount, SCHOOL.settings.DEFAULT_break_period)
    
    def remove(self):
        delete_class_level(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name, None
    
    def get_repr_text(self):
        return self.entry.name.full()
    
    def simple_name_changed(self, text, _):
        self.entry.name = ClassLevelName(text)
        
        class_level_name_update(self.id, self.timetable_editor, self.attendance_manager)


class TeachersSettingEntry(StaffSettingEntry[Teacher]):
    def __init__(self, parent: StaffMainWidget, entry: Optional[Teacher], timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        
        super().__init__(
            parent,
            "Teacher",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            [
                ("Assing the subjects this teacher generally teaches", (Teacher_SelectionList, (self.timetable_editor, attendance_manager), None)),
                ("Assign a particular subject and class to this teacher", (Teacher_DropdownCheckBoxes, (self.timetable_editor, attendance_manager), Qt.AlignmentFlag.AlignCenter)),
                ("General Information and Statistics", (self.new_stats_widgets, None)),
                ("Attendance and Punctuality", (self.new_charts_widgets, None)),
            ],
            entry,
            stack,
            attendance_manager
        )
        
        self.addProperty("class", "TeacherSettingsEntry")
    
    def get_staff_attendance_data(self):
        weeks_data = {}
        
        teacher_working_days = list(set(flatten([[d for t, d, _ in s.get_periods() if t.id == self.entry.id] for s in self.entry.subjects.values()])))

        for attendance in self.entry.attendance:
            if BaseDataDisplayWidget.is_entry_countable(attendance, teacher_working_days, SCHOOL.attendance.teacher_attendance_time_settings.timeline_dates):
                curr_index = DAYS_OF_THE_WEEK.index(attendance.period.day)
                
                days = teacher_working_days
                
                if attendance.period.date - curr_index < 1:
                    start_date = 1
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) < abs(attendance.period.date - curr_index) + 1)]
                else:
                    start_date = attendance.period.date - curr_index
                
                if attendance.period.date - curr_index + 6 > MONTHS_OF_THE_YEAR[attendance.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[attendance.period.month]
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) > MONTHS_OF_THE_YEAR[attendance.period.month] - (attendance.period.date - curr_index))]
                else:
                    end_date = attendance.period.date - curr_index + 6
                
                if start_date != end_date:
                    name_key = f"{attendance.period.month} {attendance.period.year}\n{positionify(start_date)} to {positionify(end_date)}"
                else:
                    name_key = f"{attendance.period.year}\n{positionify(start_date)} {attendance.period.month}"
                
                if days:
                    if name_key not in weeks_data:
                        weeks_data[name_key] = [0, len(days)]
                    
                    weeks_data[name_key][0] += 1
        
        return weeks_data, {key: amt_attended / total * 100 for key, (amt_attended, total) in weeks_data.items()}
    
    def get_staff_punctuality_data(self):
        attendance_time_settings = SCHOOL.attendance.teacher_attendance_time_settings
        working_days = list(set(flatten([[d for t, d, _ in s.get_periods() if t.id == self.entry.id] for s in self.entry.subjects.values()])))
        
        full_y_plot_points = []
        for index, day in enumerate(working_days):
            y_plot_points = [attendance_time_settings.check_in_time.in_minutes() - attendance.period.time.in_minutes() for attendance in self.entry.attendance if BaseDataDisplayWidget.is_entry_countable(attendance, [day], attendance_time_settings.timeline_dates)]
            
            if y_plot_points:
                full_y_plot_points.append([index, day, y_plot_points])
        
        return full_y_plot_points
    
    def new_stats_widgets(self):
        stats_widget = BaseScrollWidget(QHBoxLayout)

        stats_widget.setContentsMargins(50, 20, 50, 20)
        stats_widget.setMinimumHeight(200)
        stats_widget.setSpacing(150)
        
        weeks_data, plot_data = self.get_staff_attendance_data()
        
        full_y_plot_points = self.get_staff_punctuality_data()
        
        full_y_plot_points = list(flatten([p for _, _, p in full_y_plot_points]))
        
        if full_y_plot_points:
            score_list = [1 + int(p) / 60 for p in full_y_plot_points]
            
            p_score_factor = sum(score_list) / len(score_list)
            
            r = max(min((1 - (p_score_factor)) * 255, 255), 0)
            g = max(min(p_score_factor * 255, 255), 0)
            b = 10
        else:
            r = g = b = 255
        
        cins = [att.period.time.in_seconds() for att in self.entry.attendance if att.is_check_in]
        avg_cit = Time(0, 0, sum(cins) / len(cins) if cins else 0)
        avg_cit.normalize()
        avg_cit.second = int(avg_cit.second)
        
        couts = [att.period.time.in_seconds() for att in self.entry.attendance if not att.is_check_in]
        avg_cot = Time(0, 0, sum(couts) / len(couts) if couts else 0)
        avg_cot.normalize()
        avg_cot.second = int(avg_cot.second)
        
        disabled_color = THEME_MANAGER.pallete_get("disabled")
        
        attendance_amt_widget = QLabel(
            f"""
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Total Attendance:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(sum(amt_attended for amt_attended, _ in weeks_data.values())) if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Attendance:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(int(sum(list(plot_data.values())) / len(plot_data))) + "%" if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Punctuality Score:  </span>
                <span style='font-size: 15px; font-weight: 900; color: rgb({r}, {g}, {b});'>
                    {round(p_score_factor, 2) if full_y_plot_points else "No Data"}
                </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-in Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cit.to_str() if cins else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-out Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cot.to_str() if couts else "No Data"}
                    </span>
            </span>
            <br>
            """)
        
        duties_widget = BaseWidget()
        
        duty_days_map: dict[str, dict[str, QLabel]] = {}
        
        for subject in self.entry.subjects.values():
            cls_displayed_list = []
            
            for cls_id, cls in subject.classes.items():
                subject_periods = []
                
                for day, periods in cls.timetable.table.items():
                    for s in periods:
                        if isinstance(s, Subject):
                            if self.entry.id == s.teacher.id and day not in subject_periods:
                                subject_periods.append(day)
                        elif isinstance(s, CombinedSubject):
                            if next((True for s_s in s.subjects if s_s.id == subject.id and s_s.teacher is not None and s_s.teacher.id == self.entry.id), False):
                                subject_periods.append(day)
                    
                for day in subject_periods:
                    k = day, cls_id
                    
                    if k not in cls_displayed_list:
                        cls_displayed_list.append(k)
                    else:
                        continue
                    
                    if day not in duty_days_map:
                        duty_days_map[day] = QLabel()
                        duties_widget.addWidget(LabeledField(day, duty_days_map[day]))
                    
                    duty_days_map[day].setText(
                        duty_days_map[day].text() + f"""
                            <span>
                                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>{cls.level.name.full()} {cls.name}:  </span>
                                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>{subject.name.full()}</span>
                            </span>
                            <br>
                        """
                    )
        
        stats_widget.addWidget(LabeledField("Classes", duties_widget), alignment=Qt.AlignmentFlag.AlignTop, stretch=5)
        stats_widget.addWidget(attendance_amt_widget, alignment=Qt.AlignmentFlag.AlignTop, stretch=5)
        
        return stats_widget
    
    def new_charts_widgets(self):
        attendance_widget = BarWidget("Monthly Attendance Chart", "Time (Weeks)", "Attendance (%)") ; attendance_widget.bar_canvas.axes.set_ylim(0, 110)
        punctuality_widget = GraphWidget("Monthly Punctuality Graph", "Scan Interval", "Punctuality (Minutes)")

        chart_widget = BaseWidget()
        chart_widget.setContentsMargins(10, 0, 10, 0)
        
        chart_widget.addWidget(attendance_widget)
        chart_widget.addWidget(punctuality_widget)

        staff_list = list(SCHOOL.teachers)

        attendance_widget.clear()
        punctuality_widget.clear()
        
        color = list(get_named_colors_mapping().values())[staff_list.index(self.entry.id) % len(list(get_named_colors_mapping().values()))]
        
        _, plot_data = self.get_staff_attendance_data()
        
        attendance_widget.add_data(f"{self.entry.name.full()} Attendance Data", color, plot_data)
        
        for index, day, y_plot_points in self.get_staff_punctuality_data():
            punctuality_widget.plot(None, y_plot_points, label=day, marker='o', color=list(get_named_colors_mapping().values())[index + 200])

        return chart_widget
    
    def new(self):
        return Teacher(NEW_ID(), StaffName("", "", "", ""), None, "AttendanceApp/src/profile-images/t_id1.png", [], {})
    
    def remove(self):
        delete_teacher(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()

class PrefectsSettingEntry(StaffSettingEntry[Prefect]):
    def __init__(self, parent: StaffMainWidget, entry: Optional[Prefect], attendance_manager: AttendanceManager, stack: QStackedWidget):
        super().__init__(
            parent,
            "Prefect",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            [
                ("Select Class", (Prefect_ClassSelector, (attendance_manager, ), Qt.AlignmentFlag.AlignCenter)),
                ("Select Post", (self.get_post_cb, None)),
                ("Set Duties", (Prefect_DutyAssigner, (attendance_manager, ), Qt.AlignmentFlag.AlignCenter)),
                ("Attendane and Punctuality Statistics", (self.new_stats_widgets, Qt.AlignmentFlag.AlignCenter)),
                ("Attendance Chart and Punctuality Graph", (self.new_charts_widgets, None))
            ],
            entry,
            stack,
            attendance_manager
        )
        
        self.addProperty("class", "PrefectSettingsEntry")
    
    def _post_changed_func(self, post_id: ID):
        self.entry.post_id = post_id
        self.attendance_manager.update_staff_list_prefect_post_name(self.entry.id)
        
        self.i_parent.window().saved_state_changed.emit(True)
    
    def get_staff_attendance_data(self):
        timeline_dates = SCHOOL.attendance.prefect_attendance_time_settings.timeline_dates
        
        weeks_data = {}
        prefect_working_days = list(self.entry.duties)
        
        for attendance in self.entry.attendance:
            if BaseDataDisplayWidget.is_entry_countable(attendance, prefect_working_days, timeline_dates):
                curr_index = DAYS_OF_THE_WEEK.index(attendance.period.day)
                
                days = prefect_working_days
                
                if attendance.period.date - curr_index < 1:
                    start_date = 1
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) < abs(attendance.period.date - curr_index) + 1)]
                else:
                    start_date = attendance.period.date - curr_index
                
                if attendance.period.date - curr_index + 6 > MONTHS_OF_THE_YEAR[attendance.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[attendance.period.month]
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) > MONTHS_OF_THE_YEAR[attendance.period.month] - (attendance.period.date - curr_index))]
                else:
                    end_date = attendance.period.date - curr_index + 6
                
                if start_date != end_date:
                    name_key = f"{attendance.period.month} {attendance.period.year}\n{positionify(start_date)} to {positionify(end_date)}"
                else:
                    name_key = f"{attendance.period.year}\n{positionify(start_date)} {attendance.period.month}"
                
                if days:
                    if name_key not in weeks_data:
                        weeks_data[name_key] = [0, len(days)]
                    
                    weeks_data[name_key][0] += 1
        
        return weeks_data, {key: amt_attended / total * 100 for key, (amt_attended, total) in weeks_data.items()}
    
    def get_staff_punctuality_data(self):
        attendance_time_settings = SCHOOL.attendance.prefect_attendance_time_settings
        working_days = list(self.entry.duties)
        
        full_y_plot_points = []
        for index, day in enumerate(working_days):
            y_plot_points = [attendance_time_settings.check_in_time.in_minutes() - attendance.period.time.in_minutes() for attendance in self.entry.attendance if BaseDataDisplayWidget.is_entry_countable(attendance, [day], attendance_time_settings.timeline_dates)]
            
            if y_plot_points:
                full_y_plot_points.append([index, day, y_plot_points])
        
        return full_y_plot_points
    
    def new_stats_widgets(self):
        weeks_data, plot_data = self.get_staff_attendance_data()
        
        full_y_plot_points = self.get_staff_punctuality_data()
        
        full_y_plot_points = list(flatten([p for _, _, p in full_y_plot_points]))
        
        if full_y_plot_points:
            score_list = [1 + int(p) / 60 for p in full_y_plot_points]
            
            p_score_factor = sum(score_list) / len(score_list)
            
            r = max(min((1 - (p_score_factor)) * 255, 255), 0)
            g = max(min(p_score_factor * 255, 255), 0)
            b = 10
        else:
            r = g = b = 255
        
        cins = [att.period.time.in_seconds() for att in self.entry.attendance if att.is_check_in]
        avg_cit = Time(0, 0, sum(cins) / len(cins) if cins else 0)
        avg_cit.normalize()
        avg_cit.second = int(avg_cit.second)
        
        couts = [att.period.time.in_seconds() for att in self.entry.attendance if not att.is_check_in]
        avg_cot = Time(0, 0, sum(couts) / len(couts) if couts else 0)
        avg_cot.normalize()
        avg_cot.second = int(avg_cot.second)
        
        disabled_color = THEME_MANAGER.pallete_get("disabled")
        
        attendance_amt_widget = QLabel(
            f"""
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Total Attendance:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(sum(amt_attended for amt_attended, _ in weeks_data.values())) if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Attendance:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(int(sum(list(plot_data.values())) / len(plot_data))) + "%" if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Punctuality Score:  </span>
                <span style='font-size: 15px; font-weight: 900; color: rgb({r}, {g}, {b});'>
                    {round(p_score_factor, 2) if full_y_plot_points else "No Data"}
                </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-in Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cit.to_str() if cins else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-out Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cot.to_str() if couts else "No Data"}
                    </span>
            </span>
            <br>
            """)

        return attendance_amt_widget
    
    def new_charts_widgets(self):
        attendance_widget = BarWidget("Monthly Attendance Chart", "Time (Weeks)", "Attendance (%)") ; attendance_widget.bar_canvas.axes.set_ylim(0, 110)
        punctuality_widget = GraphWidget("Monthly Punctuality Graph", "Scan Interval", "Punctuality (Minutes)")

        chart_widget = BaseWidget()
        chart_widget.setContentsMargins(10, 0, 10, 0)
        
        chart_widget.addWidget(attendance_widget)
        chart_widget.addWidget(punctuality_widget)

        staff_list = list(SCHOOL.prefects)

        attendance_widget.clear()
        punctuality_widget.clear()
        
        color = list(get_named_colors_mapping().values())[staff_list.index(self.entry.id) % len(list(get_named_colors_mapping().values()))]
        
        _, plot_data = self.get_staff_attendance_data()
        
        attendance_widget.add_data(f"{self.entry.name.full()} Attendance Data", color, plot_data)
        
        for index, day, y_plot_points in self.get_staff_punctuality_data():
            punctuality_widget.plot(None, y_plot_points, label=day, marker='o', color=list(get_named_colors_mapping().values())[index + 200])

        return chart_widget
    
    def get_post_cb(self):
        widget = BaseWidget(QHBoxLayout)
        
        other_prefect_post_ids = [prefect.post_id for prefect in SCHOOL.prefects.values() if prefect.id != self.entry.id and prefect.post_id is not None]
        
        post_combobox = QComboBox()
        
        for p_id, post in SCHOOL.posts.items():
            if p_id not in other_prefect_post_ids:
                post_combobox.addItem(post, userData=p_id)
        
        post_combobox.addItem("None", userData=None)
        
        post_combobox.setCurrentIndex(next(i for i in range(post_combobox.count()) if self.entry.post_id == post_combobox.itemData(i)))
        
        post_editor = _Prefect_PostEditor(self, "Edit School Prefect Posts", self.attendance_manager, post_combobox)
        
        edit_posts_button = QPushButton("Edit Prefect Posts")
        edit_posts_button.clicked.connect(lambda: post_editor.exec())
        
        if self.entry.post_id is not None:
            post_combobox.setCurrentText(SCHOOL.posts[self.entry.post_id])
        else:
            post_combobox.setCurrentIndex(post_combobox.count() - 1)
        
        post_combobox.currentIndexChanged.connect(lambda i: self._post_changed_func(post_combobox.itemData(i)))
        
        widget.addWidget(post_combobox)
        widget.addStretch()
        widget.addWidget(edit_posts_button)
        
        return widget
    
    def new(self):
        return Prefect(NEW_ID(), StaffName("", "", "", ""), None, "AttendanceApp/src/profile-images/t_id1.png", [], None, None, {})
    
    def remove(self):
        self.attendance_manager.staff_list_widget.delete_staff(self.entry)
        
        return super().remove()




class SubjectsMainWidget(BaseSettingWidget[Subject | CombinedSubject]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, page_tracker: list[QPushButton | BaseWidget], option_buttons: QPushButton):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Subject", "Combined Subject"], page_tracker, option_buttons)
    
    def init_saved_variables(self):
        for entry in self.get_global().values():
            b_index = None
            
            if isinstance(entry, Subject):
                b_index = 0
            elif isinstance(entry, CombinedSubject):
                b_index = 1
            
            assert b_index is not None, f"Invalid entry type: {entry.__class__.__name__}"
            
            self.add(entry, button_index=b_index)
    
    def enter_pressed(self, key: int, id: Optional[ID] = None):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if id is not None:
                entry = self.get_global()[id]
                
                if isinstance(entry, Subject):
                    b_index = 0
                elif isinstance(entry, CombinedSubject):
                    b_index = 1
            else:
                choice_prompt = QMessageBox(self)
                choice_prompt.setWindowTitle("Staff Type")
                choice_prompt.setText("          Which staff do you want to create?          ")
                choice_prompt.setIcon(QMessageBox.Icon.Question)

                choice_prompt.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                subject_btn = choice_prompt.addButton("Subject", QMessageBox.ButtonRole.AcceptRole)
                c_subject_btn = choice_prompt.addButton("   Combined Subject   ", QMessageBox.ButtonRole.AcceptRole)

                choice_prompt.exec()
                
                if choice_prompt.clickedButton() == subject_btn:
                    b_index = 0
                elif choice_prompt.clickedButton() == c_subject_btn:
                    b_index = 1
                else:
                    return
            
            self.add(focus=True, index=list(self.widgets).index(id) + 1 if id is not None else None, button_index=b_index)
    
    def get_global(self):
        return SCHOOL.subjects
    
    def get_widget_type(self, button_index):
        widget_type = None
        
        match button_index:
            case 0:
                widget_type = SubjectsSettingEntry
            case 1:
                widget_type = CombinedSubjectsSettingEntry
        
        assert widget_type is not None, f"Invalid button index: {button_index}"
        
        return widget_type, (self.timetable_editor, self.attendance_manager)
    
    def add(self, entry = None, index = None, focus = None, button_index = None):
        final_entry = super().add(entry, index, focus, button_index)
        
        if entry is None:
            SCHOOL.subjects.add(final_entry, index)
        
        if isinstance(final_entry, Subject):
            self.attendance_manager.attendance_chart_widget.add_subject(final_entry.id)
            self.attendance_manager.punctuality_graph_widget.add_subject(final_entry.id)
        
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)

class StaffMainWidget(BaseSettingWidget[Teacher | Prefect]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, page_tracker: list[QPushButton | BaseWidget], option_buttons: QPushButton):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Teacher", "Prefect"], page_tracker, option_buttons)
        
        time_settings_widget = BaseWidget(QHBoxLayout)
        
        time_settings_widget.addWidget(LabeledField("Teacher Attendance Time Settings", self.get_timing_settings(SCHOOL.attendance.teacher_attendance_time_settings)))
        time_settings_widget.addWidget(LabeledField("Prefect Attendance Time Settings", self.get_timing_settings(SCHOOL.attendance.prefect_attendance_time_settings)))
        
        self.central_widget.insertWidget(0, time_settings_widget)
    
    def enter_pressed(self, key: int, id: Optional[ID] = None):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if id is not None:
                entry = self.get_global()[id]
                
                if isinstance(entry, Teacher):
                    b_index = 0
                elif isinstance(entry, Prefect):
                    b_index = 1
            else:
                choice_prompt = QMessageBox(self)
                choice_prompt.setWindowTitle("Staff Type")
                choice_prompt.setText("Which staff do you want to create?")
                choice_prompt.setIcon(QMessageBox.Icon.Question)

                choice_prompt.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                teacher_btn = choice_prompt.addButton("Teacher", QMessageBox.ButtonRole.AcceptRole)
                prefect_btn = choice_prompt.addButton("Prefect", QMessageBox.ButtonRole.AcceptRole)

                choice_prompt.exec()
                
                if choice_prompt.clickedButton() == teacher_btn:
                    b_index = 0
                elif choice_prompt.clickedButton() == prefect_btn:
                    b_index = 1
                else:
                    return
            
            self.add(focus=True, index=list(self.widgets).index(id) + 1 if id is not None else None, button_index=b_index)
    
    def get_global(self):
        return SCHOOL.teachers, SCHOOL.prefects
    
    def get_widget_type(self, button_index):
        widget_type = None
        params = None
        
        match button_index:
            case 0:
                widget_type = TeachersSettingEntry
                params = self.timetable_editor, self.attendance_manager
            case 1:
                widget_type = PrefectsSettingEntry
                params = self.attendance_manager,
        
        assert widget_type is not None and params is not None, f"Invalid button index: {button_index}"
        
        return widget_type, params
        
    def add(self, entry = None, index = None, focus = None, button_index = None):
        final_entry = super().add(entry, index, focus, button_index)
        
        if entry is None:
            if isinstance(final_entry, Teacher):
                SCHOOL.teachers.add(final_entry, index)
            elif isinstance(final_entry, Prefect):
                SCHOOL.prefects.add(final_entry, index)
            else:
                raise TypeError(f"Invalid staff entry type: {final_entry.__class__.__name__}")
        
        self.attendance_manager.staff_list_widget.add_staff(final_entry)
        
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)
    
    def get_timing_settings(self, staff_attendance_time_settings: StaffAttendanceTimeSettings):
        _init = True
        
        main_widget = BaseWidget(QHBoxLayout)
        main_widget.setContentsMargins(0, 5, 0, 0)
        
        def _make_ct_changed_func(target_time: Time):
            def func(time: QTime):
                target_time.hour = time.hour()
                target_time.minute = time.minute()
                
                _update_cot_sb_limit()
                _update_cit_sb_limit()
                
                self.window().saved_state_changed.emit(True)
            
            return func
        
        def _update_cit_sb_limit():
            cibim = staff_attendance_time_settings.check_in_border_interval_minutes
            cobim = staff_attendance_time_settings.check_out_border_interval_minutes
            
            interval = cibim + cobim
            
            cit_editor.setMinimumTime(QTime(cibim // 60, cibim % 60))
            cit_editor.setMaximumTime(QTime(staff_attendance_time_settings.check_out_time.hour - interval // 60, staff_attendance_time_settings.check_out_time.minute - interval % 60))
        
        def _update_cot_sb_limit():
            cibim = staff_attendance_time_settings.check_in_border_interval_minutes
            cobim = staff_attendance_time_settings.check_out_border_interval_minutes
            
            interval = cibim + cobim
            
            cot_editor.setMinimumTime(QTime(staff_attendance_time_settings.check_in_time.hour + interval // 60, staff_attendance_time_settings.check_in_time.minute + interval % 60))
            cot_editor.setMaximumTime(QTime(24 - cobim // 60, 24 - cobim % 60))
        
        def cibm_changed_func(value: int):
            staff_attendance_time_settings.check_in_border_interval_minutes = value
            
            _update_cit_sb_limit()
            _update_cot_sb_limit()
            
            self.window().saved_state_changed.emit(True)
        
        def cobm_changed_func(value: int):
            staff_attendance_time_settings.check_out_border_interval_minutes = value
            
            _update_cit_sb_limit()
            _update_cot_sb_limit()
            
            self.window().saved_state_changed.emit(True)
        
        def add_timeline(timeline: Optional[tuple[Period, Period]] = None):
            def remove_func():
                timeline_widget.removeWidget(widget)
                widget.deleteLater()
                
                staff_attendance_time_settings.timeline_dates.remove(timeline_periods)
                
                self.window().saved_state_changed.emit(True)
            
            timeline_periods = timeline
            
            if timeline_periods is None:
                timeline_periods = Period.str_to_period(time.ctime()), Period.str_to_period(time.ctime())
                staff_attendance_time_settings.timeline_dates.append(timeline_periods)
            
            widget = BaseWidget()
            widget.setSpacing(0)
            widget.setContentsMargins(8, 5, 8, 5)
            widget.setProperty("class", "SpecialBG1 BorderRadiused")
            
            cancel_pb = QPushButton("×")
            cancel_pb.setProperty("class", "SettingEntryClose")
            cancel_pb.clicked.connect(remove_func)
            
            central_widget = BaseWidget(QHBoxLayout)
            central_widget.setProperty("class", "NoBG")
            
            central_widget.addWidget(GeneralPeriodEditor(self.window(), timeline_periods[0], max_period=timeline_periods[1]), alignment=Qt.AlignmentFlag.AlignCenter)
            central_widget.addSpacing(15)
            central_widget.addWidget(GeneralPeriodEditor(self.window(), timeline_periods[1], min_period=timeline_periods[0]), alignment=Qt.AlignmentFlag.AlignCenter)
            
            widget.addWidget(cancel_pb, alignment=Qt.AlignmentFlag.AlignRight)
            widget.addWidget(central_widget)
            
            timeline_widget.insertWidget(len(timeline_widget.getChildren()), widget)
            timeline_widget.scroll_to(widget, 100)
            
            if not _init:
                self.window().saved_state_changed.emit(False)

        time_widget = BaseWidget()
        time_widget.setSpacing(10) ; time_widget.setContentsMargins(0, 0, 0, 0)
        
        cit_editor = QTimeEdit(QTime(staff_attendance_time_settings.check_in_time.hour, staff_attendance_time_settings.check_in_time.minute))
        cit_editor.timeChanged.connect(_make_ct_changed_func(staff_attendance_time_settings.check_in_time))
        cot_editor = QTimeEdit(QTime(staff_attendance_time_settings.check_out_time.hour, staff_attendance_time_settings.check_out_time.minute))
        cot_editor.timeChanged.connect(_make_ct_changed_func(staff_attendance_time_settings.check_out_time))
        
        time_widget.addWidget(LabeledWidget("<span style='font-size: 12px;'>C-In Time</span>", cit_editor))
        time_widget.addWidget(LabeledWidget("<span style='font-size: 12px;'>C-Out Time</span>", cot_editor))
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        time_border_widget = BaseWidget()
        time_border_widget.setSpacing(10) ; time_border_widget.setContentsMargins(0, 0, 0, 0)
        
        citsi_sb = QSpinBox()
        citsi_sb.setSuffix("min")
        citsi_sb.setValue(staff_attendance_time_settings.check_in_border_interval_minutes)
        citsi_sb.setRange(0, 60 * 6)
        citsi_sb.valueChanged.connect(cibm_changed_func)
        cotsi_sb = QSpinBox()
        cotsi_sb.setSuffix("min")
        cotsi_sb.setValue(staff_attendance_time_settings.check_out_border_interval_minutes)
        cotsi_sb.setRange(0, 60 * 6)
        cotsi_sb.valueChanged.connect(cobm_changed_func)
        
        time_border_widget.addWidget(LabeledWidget("<span style='font-size: 12px;'>C-In Window</span>", citsi_sb))
        time_border_widget.addWidget(LabeledWidget("<span style='font-size: 12px;'>C-Out Window</span>", cotsi_sb))
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        timeline_editing_widget = BaseWidget()
        timeline_editing_widget.setProperty("class", "SpecialBG2")
        timeline_editing_widget.setContentsMargins(5, 3, 5, 3)
        timeline_editing_widget.setFixedHeight(350)
        
        timeline_widget = BaseScrollWidget()
        timeline_widget.setSpacing(15)
        timeline_widget.setContentsMargins(5, 3, 5, 3)
        timeline_widget.addStretch()
        
        add_timeline_pb = QPushButton("Add Timeline")
        add_timeline_pb.clicked.connect(lambda: add_timeline())
        
        for timeline_date in staff_attendance_time_settings.timeline_dates:
            add_timeline(timeline_date)
        
        timeline_editing_widget.addWidget(timeline_widget)
        timeline_editing_widget.addWidget(add_timeline_pb, alignment=Qt.AlignmentFlag.AlignRight)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        
        main_widget.addStretch()
        main_widget.addWidget(time_widget)
        main_widget.addStretch()
        main_widget.addWidget(time_border_widget)
        main_widget.addStretch()
        main_widget.addWidget(IconToolBarOption(title=f"Timelines", content=timeline_editing_widget, default_bg=THEME_MANAGER.process_stylesheet("{pressed__bg3}")))
        main_widget.addStretch()
        
        _init = False
        
        return main_widget

class ClassLevelsMainWidget(BaseSettingWidget[ClassLevel]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, page_tracker: list[QPushButton | BaseWidget], option_buttons: QPushButton):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Class Level"], page_tracker, option_buttons)
    
    def get_global(self):
        return SCHOOL.class_levels
    
    def get_widget_type(self):
        return ClassLevelsSettingEntry, (self.timetable_editor, self.attendance_manager)
    
    def add(self, entry = None, index = None, focus = None, button_index = None):
        final_entry = super().add(entry, index, focus)
        
        if entry is None:
            SCHOOL.class_levels.add(final_entry, index)
            
            self.timetable_editor.add_timetable_level(final_entry)
            
            for cls in final_entry.classes.values():
                self.timetable_editor.add_timetable_class(cls)
        
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)
