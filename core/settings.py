
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
        return self.abbrev
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
        return self.abbrev
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
    
    def delete(self):
        self.level.classes.pop(id)
        
        for s_id in self.subjects:
            self.school.subjects[s_id].classes.pop(id)
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


