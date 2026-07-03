
from core.base import ID

from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class Entry:
    id: ID



@dataclass
class SubjectOccurrance:
    day_max: int
    week_max: int
@dataclass
class SubjectName:
    full_name: str
    abbrev: str
    
    def full(self):
        return self.full_name
    
    def short(self):
        return self.abbrev if self.abbrev else self.full_name
@dataclass
class Subject(Entry):
    name: SubjectName
    
    teacher: Optional["Teacher"]
    classes: dict[ID, "Class"]
    
    def passCopy(self):
        return Subject(self.id, self.name, None, self.classes)
@dataclass
class CombinedSubject(Entry):
    name: Optional[SubjectName]
    
    subjects: list[Subject]
    teacher: Optional["CombinedTeacher"]
    
    def passCopy(self):
        return CombinedSubject(self.id, self.subjects, None)


@dataclass
class TeacherName:
    start: str
    first: Optional[str]
    other: Optional[str]
    abbrev: str
    
    def full(self):
        return f"{self.start} {self.first} {self.other}" if None not in (self.first, self.other) else self.start
    
    def short(self):
        return self.abbrev if self.abbrev else self.start
@dataclass
class Teacher(Entry):
    name: TeacherName
    
    subjects: dict[ID, Subject]
@dataclass
class CombinedTeacher(Entry):
    teachers: list[Teacher]



@dataclass
class Class:
    id: ID
    name: str
    
    level: "ClassLevel"
    subjects: dict[ID, "Subject | CombinedSubject"]
    
    locked_subjects: dict[tuple[str, int], ID]
    
    school: Any
    
    def delete_subject(self, id: ID):
        self.subjects.pop(id)
        
        for v, s_id in self.locked_subjects.copy().items():
            if s_id == id:
                self.locked_subjects.pop(v)
    
    def delete(self):
        self.level.classes.pop(self.id)
        
        for s_id in self.subjects:
            self.school.subjects[s_id].classes.pop(self.id)
class ClassLevelName(str):
    def __init__(self, *args):
        super().__init__()
    
    def full(self):
        return str(self)
    
    def short(self):
        return str(self)
@dataclass
class ClassLevel(Entry):
    name: ClassLevelName
    
    classes: dict[ID, Class]
    subjects_occurence: dict[ID, SubjectOccurrance]
    
    weekdays: dict[str, tuple[int, int]]
    
    def delete_subject(self, id: ID, teacher_id: Optional[ID] = None):
        for cls in self.classes.values():
            if id in cls.subjects:
                if (cls.subjects[id].teacher.id == teacher_id if teacher_id is not None else True):
                    cls.delete_subject(id)


