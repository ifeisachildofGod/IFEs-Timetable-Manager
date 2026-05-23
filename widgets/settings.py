from imports import *

from widgets.base_widgets import *
from widgets.settings_options import *


class SubjectsSettingEntry(BaseSettingEntry):
    def __init__(self, simple_placeholder, extended_placeholders, option_dialogs, entry=None):
        if entry is None:
            id = ID.generate_new()
            
            Hook.setDynamicID(id)
            entry = Subject(id, "", None, {}, None)
        
        super().__init__(simple_placeholder, extended_placeholders, option_dialogs, entry)

class TeachersSettingEntry(BaseSettingEntry):
    def __init__(self, simple_placeholder, extended_placeholders, option_dialogs, entry=None):
        if entry is None:
            id = ID.generate_new()
            
            Hook.setDynamicID(id)
            entry = Teacher(id, "", {})
        
        super().__init__(simple_placeholder, extended_placeholders, option_dialogs, entry)

class ClassLevelsSettingEntry(BaseSettingEntry):
    def __init__(self, simple_placeholder, extended_placeholders, option_dialogs, entry=None):
        if entry is None:
            id = ID.generate_new()
            
            Hook.setDynamicID(id)
            entry = ClassLevel(id, "", {})
        
        super().__init__(simple_placeholder, extended_placeholders, option_dialogs, entry)



class Subjects(BaseSettingWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window, "Subject", "Enter Subject Name", ["Full Name", "Abbreviation"], {"Classes": ("Select Classes", SubjectDropdownCheckBoxes), "Teachers": ("Select Teachers", SubjectSelectionList)})
    
    def get_widget_type(self):
        return SubjectsSettingEntry
    
    @Hook(Signal.SubjectAdd, SignalType.SOURCE)
    def add(self, entry = None, index = None):
        return super().add(entry, index)
    
    @Hook(Signal.SubjectRemove, SignalType.SOURCE)
    def remove(self, widget):
        return super().remove(widget)


class Teachers(BaseSettingWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window, "Teacher", "Enter Teacher Name", ["Surname", "First Name", "Other Names"], {"Classes": ("Select Classes", TeacherDropdownCheckBoxes), "Subjects": ("Select Subjects", SubjectSelectionList)})
    
    def get_widget_type(self):
        return TeachersSettingEntry
    
    @Hook(Signal.TeacherAdd, SignalType.SOURCE)
    def add(self, entry = None, index = None):
        return super().add(entry, index)
    
    @Hook(Signal.TeacherRemove, SignalType.SOURCE)
    def remove(self, widget):
        return super().remove(widget)


class Classes(BaseSettingWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__(main_window, "Class", "Enter Class Level Name", None, {"Sub Classes": ("Make and Edit Classes", ClassOptionsMaker), "Subject Occurence": ("Edit Subject Occurence", SubjectSelection)})
    
    def get_widget_type(self):
        return ClassLevelsSettingEntry
    
    @Hook(Signal.ClassLevelAdd, SignalType.SOURCE)
    def add(self, entry = None, index = None):
        return super().add(entry, index)
    
    @Hook(Signal.ClassLevelRemove, SignalType.SOURCE)
    def remove(self, widget):
        return super().remove(widget)


