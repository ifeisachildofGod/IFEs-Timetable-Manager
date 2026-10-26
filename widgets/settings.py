
from imports import *

from .base import *
from .settings_options import *

from AttendanceApp import AttendanceManager


class _Prefect_PostEditor(BaseSettingDialog):
    def __init__(self, parent: PrefectsMainWidget, title: str, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.setFixedSize(650, 450)
        
        self.__init = True
        
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
            SCHOOL.posts[id] = entry.get_text()
            
            self.i_parent.window().saved_state_changed.emit(True)
        
        def remove():
            SCHOOL.posts.pop(id)
            
            self.main_widget.removeWidget(entry)
            entry.deleteLater()
            
            for prefect_id, prefect in SCHOOL.prefects.items():
                if id == prefect.post_id:
                    prefect.post_id = None
                    self.attendance_manager.update_staff_list_prefect_post_name(prefect_id)
            
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
        
        if self.entry.name.abbrev:
            self.toogle_name_format(False)
    
    def new(self):
        return Subject(NEW_ID(), SubjectName("", ""), None, {})
    
    def remove(self):
        delete_subject(self.id, self.timetable_editor, self.attendance_manager, self.i_parent)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, (self.entry.name.first, self.entry.name.abbrev)
    
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
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty (Switch to Short Name View)")

class CombinedSubjectsSettingEntry(BaseSettingEntry[CombinedSubject]):
    def __init__(self, parent: SubjectsMainWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Subject",
            None,
            [
                ("Child subjects under this combined subject", (CombinedSubject_SelectionList, (self.timetable_editor, self.attendance_manager), None)),
                ("Classes offering this combined subject", (CombinedSubject_DropdownCheckBoxes, (self.timetable_editor, self.attendance_manager), Qt.AlignmentFlag.AlignCenter)),
            ],
            entry,
            stack
        )
        
        if self.entry.subjects:
            self.simple_name_changed(self.simple_line_edit.text(), None)
    
    def new(self):
        return CombinedSubject(NEW_ID(), CombinedSubjectName(None, None), [], {}, SCHOOL.settings.DEFAULT_occurance_data)
    
    def remove(self):
        delete_combined_subject(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, None
    
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

class TeachersSettingEntry(BaseSettingEntry[Teacher]):
    def __init__(self, parent: TeachersMainWidget, entry: Optional[Teacher], timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Teacher",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            [
                ("Assing the subjects this teacher generally teaches", (Teacher_SelectionList, (self.timetable_editor, self.attendance_manager), None)),
                ("Assign a particular subject and class to this teacher", (Teacher_DropdownCheckBoxes, (self.timetable_editor, self.attendance_manager), Qt.AlignmentFlag.AlignCenter)),
            ],
            entry,
            stack
        )
        
        if self.entry.name.second or self.entry.name.third or self.entry.name.abbrev:
            self.toogle_name_format(False)
    
    def new(self):
        return Teacher(NEW_ID(), StaffName("", "", "", ""), None, "AttendanceApp/src/profile-images/t_id1.png", [], {})
    
    def remove(self):
        delete_teacher(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, (self.entry.name.first, self.entry.name.second, self.entry.name.third, self.entry.name.abbrev)
    
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
        
        if self.extended_edits_widget.isVisible():
            simple_line_edit.blockSignals(True)
            simple_line_edit.setText(f"{self.entry.name.first or ""}{" " + self.entry.name.second if self.entry.name.second is not None else ""}{" " + self.entry.name.third if self.entry.name.third is not None else ""}")
            simple_line_edit.blockSignals(False)
    
    def extended_name_empty(self, index, text):
        key = f"E{index}EmptyNameWarning"
        
        if text:
            self.status_widget.removeLinient(key)
        
        match index:
            case 0:
                if not text and self.extended_edits_widget.isVisible():
                    self.status_widget.addMessage(Status.WARN, key, f"Surname is empty")
            case 1:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"First name is empty")
            case 2:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"Other name is empty")
            case 3:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty")

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
                ("Edit occurence of the subjects under this level during the week", (ClassLevel_OccuranceEditor, (self.timetable_editor, self.attendance_manager), None))
            ],
            entry,
            stack
        )
    
    def new(self):
        return ClassLevel(NEW_ID(), ClassLevelName(), {}, {}, SCHOOL.settings.TIMETABLE_weekdays.copy(), SCHOOL.settings.DEFAULT_period_amount, SCHOOL.settings.DEFAULT_break_period)
    
    def remove(self):
        delete_class_level(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name, None
    
    def simple_name_changed(self, text, _):
        self.entry.name = ClassLevelName(text)
        
        class_level_name_update(self.id, self.timetable_editor, self.attendance_manager)

class PrefectsSettingEntry(BaseSettingEntry[Prefect]):
    def __init__(self, parent: PrefectsMainWidget, entry: Optional[Prefect], attendance_manager: AttendanceManager, stack: QStackedWidget):
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Prefect",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            [
                ("Select Class", (Prefect_ClassSelector, (self.attendance_manager, ), Qt.AlignmentFlag.AlignCenter)),
                ("Select Post", (self.get_post_cb, Qt.AlignmentFlag.AlignLeft)),
                ("Set Duties", (Prefect_DutyAssigner, (self.attendance_manager, ), Qt.AlignmentFlag.AlignCenter))
            ],
            entry,
            stack
        )
    
    def get_post_cb(self):
        post_combobox = QComboBox()
        
        other_prefect_post_ids = [prefect.post_id for prefect in SCHOOL.prefects.values() if prefect.id != self.entry.id]
        
        for p_id, post in SCHOOL.posts.items():
            if p_id not in other_prefect_post_ids:
                post_combobox.addItem(post, userData=p_id)
        
        post_combobox.addItem("None", userData=None)
        
        if self.entry.post_id is not None:
            post_combobox.setCurrentText(SCHOOL.posts[self.entry.post_id])
        else:
            post_combobox.setCurrentIndex(post_combobox.count() - 1)
        
        post_combobox.currentIndexChanged.connect(lambda: self.attendance_manager.update_staff_list_prefect_post_name(self.entry.id))
        
        if self.entry.name.second or self.entry.name.third or self.entry.name.abbrev:
            self.toogle_name_format(False)
        
        return post_combobox
    
    def new(self):
        return Prefect(NEW_ID(), StaffName("", "", "", ""), None, "AttendanceApp/src/profile-images/t_id1.png", [], None, None, {})
    
    def remove(self):
        self.attendance_manager.staff_list_widget.delete_staff(self.entry)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.first, (self.entry.name.first, self.entry.name.second, self.entry.name.third, self.entry.name.abbrev)
    
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
        
        self.attendance_manager.update_staff_list_staff_name(self.id)
        
        if self.extended_edits_widget.isVisible():
            simple_line_edit.blockSignals(True)
            simple_line_edit.setText(f"{self.entry.name.first or ""}{" " + self.entry.name.second if self.entry.name.second is not None else ""}{" " + self.entry.name.third if self.entry.name.third is not None else ""}")
            simple_line_edit.blockSignals(False)
    
    def extended_name_empty(self, index, text):
        key = f"E{index}EmptyNameWarning"
        
        if text:
            self.status_widget.removeLinient(key)
        
        match index:
            case 0:
                if not text and self.extended_edits_widget.isVisible():
                    self.status_widget.addMessage(Status.WARN, key, f"Surname is empty")
            case 1:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"First name is empty")
            case 2:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"Other name is empty")
            case 3:
                if not text:
                    self.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty")


class SubjectsMainWidget(BaseSettingWidget[Subject | CombinedSubject]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Subject", "Combined Subject"])
    
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
                b_index = 0
            
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

class TeachersMainWidget(BaseSettingWidget[Teacher]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Teacher"])
    
    def get_global(self):
        return SCHOOL.teachers
    
    def get_widget_type(self):
       return TeachersSettingEntry, (self.timetable_editor, self.attendance_manager)
    
    def add(self, entry = None, index = None, focus = None, button_index = None):
        final_entry = super().add(entry, index, focus)
        
        if entry is None:
            SCHOOL.teachers.add(final_entry, index)
        
        self.attendance_manager.staff_list_widget.add_staff(final_entry)
        
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)

class ClassLevelsMainWidget(BaseSettingWidget[ClassLevel]):
    def __init__(self, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(["Class Level"])
    
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

class PrefectsMainWidget(BaseSettingWidget[Prefect]):
    def __init__(self, attendance_manager: AttendanceManager):
        self.attendance_manager = attendance_manager
        
        super().__init__(["Prefect"])
        
        post_editor = _Prefect_PostEditor(self, "Edit School Prefect Posts", self.attendance_manager)
        
        edit_posts_button = QPushButton("Edit Prefect Posts")
        edit_posts_button.clicked.connect(lambda: post_editor.exec())
        
        self.add_buttons_widget.insertWidget(0, edit_posts_button)
    
    def get_global(self):
        return SCHOOL.prefects
    
    def get_widget_type(self):
        return PrefectsSettingEntry, (self.attendance_manager, )
    
    def add(self, entry = None, index = None, focus = None, button_index = None):
        final_entry = super().add(entry, index, focus)
        
        if entry is None:
            SCHOOL.prefects.add(final_entry, index)
        
        self.attendance_manager.staff_list_widget.add_staff(final_entry)
        
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)
