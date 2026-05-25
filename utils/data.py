
import random

from typing import Generator, Optional
from dataclasses import dataclass


class ID(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.parents = []
    
    def __add__(self, value):
        id = ID(value)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    def __radd__(self, other):
        return self.__add__(other)
    
    @staticmethod
    def generate_new():
        tmp = random.randint(0, 500000)
        
        return ID(id(tmp))

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
class Class:
    id: ID
    name: str
    
    level: "ClassLevel"
    subjects: dict[ID, "Subject"]
    
    def delete(self):
        self.level.classes.pop(id)
        
        for s_id in self.subjects:
            SUBJECTS[s_id].classes.pop(id)
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


@dataclass
class Settings:
    DEFAULT_max_classes: int
    DEFAULT_occurance_data: tuple[int, int]
    TEACHER_rsma_mapping: dict[ID, Optional[int]]
    TIMETABLE_weekdays: dict[str, tuple[int, int]]
    THEME: str
    
    def set(self, value):
        self.__dict__ = value.__dict__



class Global:
    def __init__(self):
        self.data = {}
    
    def get(self):
        return self.data
    
    def add(self, entry):
        self.data[entry.id] = entry
    
    def remove(self, id):
        self.data.pop(id)
    
    def set(self, value):
        self.__dict__ = value.__dict__
    
    def __len__(self):
        return self.data.__len__()
    
    def __iter__(self):
        return ((k, v) for k, v in self.data.items())
    
    def __getitem__(self, key: ID):
        return self.data.__getitem__(key)

class GlobalSubjects(Global):
    def __iter__(self) -> Generator[tuple[ID, Subject], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> Subject:
        return super().__getitem__(key)
    
    def add(self, entry: Subject):
        return super().add(entry)
    
    def remove(self, id: ID):
        for _, cls_lvl in CLASS_LEVELS:
            if id in cls_lvl.subjects_occurence:
                cls_lvl.subjects_occurence.pop(id)
        
        for _, teacher in TEACHERS:
            if id in teacher.subjects:
                teacher.subjects.pop(id)
        
        return super().remove(id)

class GlobalTeachers(Global):
    def __iter__(self) -> Generator[tuple[ID, Teacher], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> Teacher:
        return super().__getitem__(key)
    
    def add(self, entry: Teacher):
        return super().add(entry)
    
    def remove(self, id: ID):
        return super().remove(id)

class GlobalClassLevels(Global):
    def __iter__(self) -> Generator[tuple[ID, ClassLevel], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> ClassLevel:
        return super().__getitem__(key)
    
    def add(self, entry: ClassLevel):
        SETTINGS.TEACHER_rsma_mapping[entry.id] = None
        
        return super().add(entry)
    
    def remove(self, id: ID):
        SETTINGS.TEACHER_rsma_mapping.pop(id)
        
        for _, subject in SUBJECTS:
            for cls in subject.classes.copy().values():
                if id == cls.level.id:
                    subject.classes.pop(cls.id)
        
        return super().remove(id)


SUBJECTS = GlobalSubjects()
TEACHERS = GlobalTeachers()
CLASS_LEVELS = GlobalClassLevels()

SETTINGS = Settings(
    3,
    (2, 3),
    {},
    {"Monday": (10, 7), "Tuesday": (10, 7), "Wednesday": (10, 7), "Thursday": (10, 7), "Friday": (10, 7)},
    "dark-blue"
)



