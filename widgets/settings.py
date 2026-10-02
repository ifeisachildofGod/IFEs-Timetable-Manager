from imports import *

from .base import *
from .settings_options import *

from AttendanceApp import AttendanceManager


class SubjectsSettingEntry(BaseSettingEntry[Subject]):
    def __init__(self, parent: BaseSettingWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Subject",
            ["Full Name", "Abbreviation"],
            {
                "Offering Classes": ("Classes offering {name}", SubjectDropdownCheckBoxes, (self.timetable_editor, self.attendance_manager, )),
                "Assign Teachers": ("Teachers teaching {name}", SubjectSelectionList, (self.timetable_editor, self.attendance_manager))
            },
            entry
        )
    
    def new(self):
        return Subject(NEW_ID(), SubjectName("", ""), None, {})
    
    def remove(self):
        delete_subject(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.full_name, (self.entry.name.full_name, self.entry.name.abbrev)
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit]):
        self.entry.name.full_name = text
        
        full_name_e = extended_line_edits[0]
        full_name_e.setText(text)
    
    def extended_name_changed(self, index, text, simple_line_edit):
        match index:
            case 0:
                self.entry.name.full_name = text
                
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
    def __init__(self, parent: BaseSettingWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Subject",
            None,
            {
                "Offering Classes": ("Classes offering {name}", CombinedSubjectDropdownCheckBoxes, (self.timetable_editor, self.attendance_manager)),
                "Child Subjects": ("Subjects under {name}", CombinedSubjectSelectionList, (self.timetable_editor, self.attendance_manager))
            },
            entry
        )
        
        if self.entry.subjects:
            self.simple_name_changed(self.simple_line_edit.text(), None)
    
    def new(self):
        return CombinedSubject(NEW_ID(), None, CombinedSubjectName(None, None), [], {}, SCHOOL.settings.DEFAULT_occurance_data)
    
    def remove(self):
        delete_combined_subject(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.full_name, None
    
    def simple_name_changed(self, text, _):
        if text:
            self.entry.name.full_name = text
            self.entry.name.abbrev = None
        else:
            self.entry.name.full_name = None
            self.entry.name.abbrev = "/".join([s.name.short() for s in self.entry.subjects]) or None
        
        combined_subject_name_update(self.id, self.timetable_editor, self.attendance_manager, self)
    
    def simple_name_empty(self, text):
        if not self.entry.subjects:
            super().simple_name_empty(text)

class TeachersSettingEntry(BaseSettingEntry[Teacher]):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[Teacher], timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Teacher",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            {
                "Assign Classes": ("Classes taught by {name}", TeacherDropdownCheckBoxes, (self.timetable_editor, self.attendance_manager)),
                "Assign Subjects": ("Subjects {name} teaches", TeacherSelectionList, (self.timetable_editor, self.attendance_manager))
            },
            entry
        )
    
    def new(self):
        return Teacher(NEW_ID(), None, StaffName("", "", "", ""), "AttendanceApp/src/profile-images/t_id1.png", [], {})
    
    def remove(self):
        delete_teacher(self.id, self.timetable_editor, self.attendance_manager)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.start, (self.entry.name.start, self.entry.name.first, self.entry.name.other, self.entry.name.abbrev)
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit, QLineEdit]):
        full_name_e = extended_line_edits[0]
        full_name_e.setText(text)
        
        for le in extended_line_edits[1:]:
            le.blockSignals(True)
            le.setText("")
            le.blockSignals(False)
        
        self.entry.name.first = None
        self.entry.name.other = None
        self.entry.name.abbrev = None
    
    def extended_name_changed(self, index, text, simple_line_edit):
        match index:
            case 0:
                self.entry.name.start = text
            case 1:
                self.entry.name.first = text
            case 2:
                self.entry.name.other = text
            case 3:
                self.entry.name.abbrev = text
        
        teacher_name_update(self.id, self.timetable_editor, self.attendance_manager)
        
        if self.extended_edits_widget.isVisible():
            simple_line_edit.blockSignals(True)
            simple_line_edit.setText(f"{self.entry.name.start or ""}{" " + self.entry.name.first if self.entry.name.first is not None else ""}{" " + self.entry.name.other if self.entry.name.other is not None else ""}")
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
    def __init__(self, parent: BaseSettingWidget, entry, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        super().__init__(
            parent,
            "Class Level",
            None,
            {
                "Create and Edit Classes": ("Classes under {name}", ClassOptionsMaker, (self.timetable_editor, self.attendance_manager)),
                "Edit Subjects Occurences": ("Edit {name} subjects occurences", OccuranceEditor, (self.timetable_editor, self.attendance_manager))
            },
            entry
        )
    
    def new(self):
        return ClassLevel(NEW_ID(), ClassLevelName(), {}, {}, SCHOOL.settings.TIMETABLE_weekdays.copy(), SCHOOL.settings.DEFAULT_period_amount, SCHOOL.settings.DEFAULT_break_period)
    
    def remove(self):
        delete_class_level(self.id, self.timetable_editor, self.attendance_manager)
        
        # for cancel_pb_dict in self.timetable_editor.combination_widgets[self.id].subject_cancel_button_widgets:
        #     for pb in cancel_pb_dict["classes"].copy():
        #         pb.click()
        
        # for cls in self.entry.classes.values():
        #     for subject in cls.subjects.values():
        #         if isinstance(subject, Subject):
        #             subjects = [subject]
        #         elif isinstance(subject, CombinedSubject):
        #             subjects = subject.subjects
                
        #         for subject in subjects:
        #             if subject.teacher:
        #                 for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
        #                     if subject.teacher.id in teacher_filtered_dict:
        #                         teacher_filtered_dict[subject.teacher.id].remove_class(subject.id, cls.id)
        
        # self.timetable_editor.delete_timetable_level(self.id)
        
        # for cls_id in self.entry.classes.copy():
        #     SCHOOL.class_levels.remove_class(self.id, cls_id)
        
        # SCHOOL.settings.TEACHER_rsma_mapping.pop(self.id)
        # SCHOOL.settings.EXPORT_selected_classes.pop(self.id)
        # SCHOOL.settings.TIMETABLE_time_settings.pop(self.id)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name, None
    
    def simple_name_changed(self, text, _):
        self.entry.name = ClassLevelName(text)
        
        class_level_name_update(self.id, self.timetable_editor, self.attendance_manager)


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


