from imports import *

from widgets.base import *
from widgets.settings_options import *


class SubjectsSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[Subject], timetable_editor: SchoolTimetableEditor):
        entry = entry or Subject(ID.generate_new(), SubjectName("", ""), None, {})
        
        self.timetable_editor = timetable_editor
        
        super().__init__(
            parent,
            "Subject",
            ["Full Name", "Abbreviation"],
            {"Classes": ("Select Classes", SubjectDropdownCheckBoxes), "Teachers": ("Select Teachers", SubjectSelectionList)},
            entry
        )
        
        self.entry = entry
    
    def remove(self):
        for cls in self.entry.classes.values():
            if self.entry.id in cls.subjects:
                self.timetable_editor.timetable_widgets[cls.level.id][cls.id].change_subject_amount(self.entry.id, -cls.level.subjects_occurence[self.entry.id].week_max)
                
                cls.subjects.pop(self.entry.id)
        
        for cls in self.entry.classes.values():
            if self.entry.id in cls.level.subjects_occurence:
                cls.level.subjects_occurence.pop(self.entry.id)
        
        for _, teacher in SCHOOL.teachers:
            if self.entry.id in teacher.subjects:
                teacher.subjects.pop(self.entry.id)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.full_name, (self.entry.name.full_name, self.entry.name.abbrev)
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit]):
        self.entry.name.abbrev = text
        self.entry.name.full_name = text
        
        full_name_e = extended_line_edits[0]
        full_name_e.setText(text)
    
    def extended_name_changed(self, text, index, simple_line_edit):
        match index:
            case 0:
                self.entry.name.full_name = text
                
                if text != simple_line_edit.text():
                    simple_line_edit.setText(text)
            case 1:
                self.entry.name.abbrev = text
    
    def extended_name_empty(self, text, index):
        key = f"E{index}EmptyNameWarning"
        
        match index:
            case 1:
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty (Switch to Short Name View)")

class TeachersSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[Teacher], timetable_editor: SchoolTimetableEditor):
        entry = entry or Teacher(ID.generate_new(), TeacherName("", "", "", ""), {})
        
        self.timetable_editor = timetable_editor
        
        super().__init__(
            parent,
            "Teacher",
            ["Surname", "First Name", "Other Names", "Abbreviation"],
            {"Classes": ("Select Classes", TeacherDropdownCheckBoxes), "Subjects": ("Select Subjects", TeacherSelectionList)},
            entry
        )
        
        self.entry = entry
    
    def remove(self):
        for subject_id, subject in self.entry.subjects.items():
            for cls_id, cls in subject.classes.items():
                if self.entry.id == cls.subjects[subject_id].teacher.id:
                    self.timetable_editor.timetable_widgets[cls.level.id][cls_id].change_subject_amount(subject_id, -cls.level.subjects_occurence[subject_id].week_max)
                    
                    cls.subjects.pop(subject_id)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name.start, (self.entry.name.start, self.entry.name.first, self.entry.name.other, self.entry.name.abbrev)
    
    def simple_name_changed(self, text, extended_line_edits: tuple[QLineEdit, QLineEdit, QLineEdit]):
        self.entry.name.start = text
        self.entry.name.abbrev = text
        
        full_name_e = extended_line_edits[1]
        full_name_e.setText(text)
    
    def extended_name_changed(self, text, index, simple_line_edit):
        match index:
            case 0:
                self.entry.name.start = text
            case 1:
                self.entry.name.first = text
                
                if text != simple_line_edit.text():
                    simple_line_edit.setText(text)
            case 2:
                self.entry.name.other = text
            case 3:
                self.entry.name.abbrev = text
    
    def extended_name_empty(self, text, index):
        key = f"E{index}EmptyNameWarning"
        
        match index:
            case 0:
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.addMessage(Status.WARN, key, f"Surname is empty")
            case 1:
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.removeLinient("EmptyNameWarning")
                    self.status_widget.addMessage(Status.WARN, key, f"First name is empty")
            case 2:
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.addMessage(Status.WARN, key, f"Other name is empty")
            case 3:
                if text:
                    self.status_widget.removeLinient(key)
                else:
                    self.status_widget.addMessage(Status.WARN, key, f"Abbreviation is empty")

class ClassLevelsSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[ClassLevel], timetable_editor: SchoolTimetableEditor):
        entry = entry or ClassLevel(ID.generate_new(), ClassLevelName(), {}, {}, deepcopy(SCHOOL.settings.TIMETABLE_weekdays))
        
        self.entry = entry
        self.timetable_editor = timetable_editor
        
        super().__init__(
            parent,
            "Class Level",
            None,
            {
                "Sub Classes": ("Make and Edit Classes", ClassOptionsMaker, (self.timetable_editor, )),
                "Subject Occurence": ("Edit Subject Occurence", OccuranceEditor, (self.timetable_editor, ))
            },
            self.entry
        )
    
    def remove(self):
        self.timetable_editor.delete_timetable_level(self.entry.id)
        
        SCHOOL.settings.TEACHER_rsma_mapping.pop(self.entry.id)
        SCHOOL.settings.EXPORT_selected_classes.pop(self.entry.id)
        
        for cls_id in self.entry.classes.copy():
            SCHOOL.class_levels.remove_class(self.entry.id, cls_id)
        
        return super().remove()
    
    def get_init_text(self):
        return self.entry.name, None
    
    def simple_name_changed(self, text, _):
        self.entry.name = ClassLevelName(text)
        self.timetable_editor.set_label_text(self.entry.id, text)



class SubjectsMainWidget(BaseSettingWidget):
    def __init__(self, timetable_editor: SchoolTimetableEditor):
        self.timetable_editor = timetable_editor
        
        super().__init__("Subject")
    
    def get_global(self):
        return SCHOOL.subjects
    
    def get_widget_type(self):
        return SubjectsSettingEntry, (self.timetable_editor, )
    
    def add(self, entry: Subject = None, index = None):
        new_entry = super().add(entry, index)
        
        if entry is None:
            SCHOOL.subjects.add(new_entry)

class TeachersMainWidget(BaseSettingWidget):
    def __init__(self, timetable_editor: SchoolTimetableEditor):
        self.timetable_editor = timetable_editor
        
        super().__init__("Teacher")
    
    def get_global(self):
        return SCHOOL.teachers
    
    def get_widget_type(self):
        return TeachersSettingEntry, (self.timetable_editor, )
    
    def add(self, entry: Teacher = None, index = None):
        new_entry = super().add(entry, index)
        
        if entry is None:
            SCHOOL.teachers.add(new_entry)

class ClassLevelsMainWidget(BaseSettingWidget):
    def __init__(self, timetable_editor: SchoolTimetableEditor):
        self.timetable_editor = timetable_editor
        
        super().__init__("Class")
    
    def get_global(self):
        return SCHOOL.class_levels
    
    def get_widget_type(self):
        return ClassLevelsSettingEntry, (self.timetable_editor, )
    
    def add(self, entry: ClassLevel = None, index = None):
        new_entry: ClassLevel = super().add(entry, index)
        
        if entry is None:
            SCHOOL.class_levels.add(new_entry)
        
        self.timetable_editor.add_timetable_level(new_entry)
        
        for cls in new_entry.classes.values():
            self.timetable_editor.add_timetable_class(cls)



