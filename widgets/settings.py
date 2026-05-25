from imports import *

from widgets.base_widgets import *
from widgets.settings_options import *


class SubjectsSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[Subject] = None):
        entry = entry or Subject(ID.generate_new(), SubjectName("", ""), None, {})
        
        super().__init__(
            parent,
            "Enter Subject Name",
            ["Full Name", "Abbreviation"],
            {"Classes": ("Select Classes", SubjectDropdownCheckBoxes), "Teachers": ("Select Teachers", SubjectSelectionList)},
            entry
        )
        
        self.entry = entry
    
    def get_init_text(self):
        return self.entry.name.full_name, (self.entry.name.full_name, self.entry.name.abbrev)
    
    def simple_name_changed(self, text):
        self.entry.name.abbrev = text
        self.entry.name.full_name = text
    
    def extended_name_changed(self, text, index):
        match index:
            case 0:
                self.entry.name.full_name = text
            case 1:
                self.entry.name.abbrev = text

class TeachersSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[Teacher] = None):
        entry = entry or Teacher(ID.generate_new(), TeacherName("", "", "", ""), {})
        
        super().__init__(
            parent,
            "Enter Teacher Name",
            ["Surname", "First Name", "Other Names"],
            {"Classes": ("Select Classes", TeacherDropdownCheckBoxes), "Subjects": ("Select Subjects", TeacherSelectionList)},
            entry
        )
        
        self.entry = entry
    
    def get_init_text(self):
        return self.entry.name.start, (self.entry.name.start, self.entry.name.first, self.entry.name.other, self.entry.name.abbrev)
    
    def simple_name_changed(self, text):
        self.entry.name.start = text
        self.entry.name.abbrev = text
    
    def extended_name_changed(self, text, index):
        match index:
            case 0:
                self.entry.name.start = text
            case 1:
                self.entry.name.first = text
            case 2:
                self.entry.name.other = text
            case 3:
                self.entry.name.abbrev = text

class ClassLevelsSettingEntry(BaseSettingEntry):
    def __init__(self, parent: BaseSettingWidget, entry: Optional[ClassLevel] = None):
        entry = entry or ClassLevel(ID.generate_new(), ClassLevelName(), {}, {})
        
        super().__init__(
            parent,
            "Enter Class Level Name",
            None,
            {"Sub Classes": ("Make and Edit Classes", ClassOptionsMaker), "Subject Occurence": ("Edit Subject Occurence", OccuranceEditor)},
            entry
        )
        
        self.entry = entry
    
    def get_init_text(self):
        return self.entry.name, None
    
    def simple_name_changed(self, text):
        self.entry.name = ClassLevelName(text)



class SubjectsMainWidget(BaseSettingWidget):
    def __init__(self):
        super().__init__("Subject")
    
    def get_widget_type(self):
        return SubjectsSettingEntry
    
    def add(self, entry = None, index = None):
        new_entry = super().add(entry, index)
        
        if entry is None:
            SUBJECTS.add(new_entry)
    
    def remove(self, widget):
        id = super().remove(widget)
        
        SUBJECTS.remove(id)

class TeachersMainWidget(BaseSettingWidget):
    def __init__(self):
        super().__init__("Teacher")
    
    def get_widget_type(self):
        return TeachersSettingEntry
    
    def add(self, entry = None, index = None):
        new_entry = super().add(entry, index)
        
        if entry is None:
            TEACHERS.add(new_entry)
    
    def remove(self, widget):
        id = super().remove(widget)
        
        TEACHERS.remove(id)

class ClassLevelsMainWidget(BaseSettingWidget):
    def __init__(self):
        super().__init__("Class")
    
    def get_widget_type(self):
        return ClassLevelsSettingEntry
    
    def add(self, entry = None, index = None):
        new_entry = super().add(entry, index)
        
        if entry is None:
            CLASS_LEVELS.add(new_entry)
    
    def remove(self, widget):
        id = super().remove(widget)
        
        CLASS_LEVELS.remove(id)


