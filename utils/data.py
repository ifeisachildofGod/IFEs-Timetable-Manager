
from dataclasses import dataclass
from enum import Enum
import random
from typing import Optional


class ID(str):
    def __init__(self):
        super().__init__()
    
    def __add__(self, value):
        return ID(f"{self}->{value}")
    
    @staticmethod
    def generate_new():
        tmp = random.randint()
        
        return ID(id(tmp))


@dataclass
class SubjectOccurrence:
    day_max: int
    week_max: int


@dataclass
class Class:
    id: ID
    name: str
    
    subjects: dict[ID, "Subject"]


@dataclass
class Entry:
    id: ID
    name: str
    

@dataclass
class Subject(Entry):
    teacher: Optional["Teacher"]
    classes: dict[ID, Class]
    
    occurance: Optional[SubjectOccurrence]

@dataclass
class Teacher(Entry):
    subjects: dict[ID, Subject]

@dataclass
class ClassLevel(Entry):
    classes: dict[ID, Class]



@dataclass
class Settings:
    GENERAL_periodamt: int
    TEACHER_rsma_mapping: dict[ID, Optional[int]]
    TIMETABLE_breakperiod: int
    TIMETABLE_weekdays: int


class Signal(Enum):
    SubjectAdd = "SubjectAdd"
    TeacherAdd = "TeacherAdd"
    ClassLevelAdd = "ClassLevelAdd"
    
    SubjectRemove = "SubjectRemove"
    TeacherRemove = "TeacherRemove"
    ClassLevelRemove = "ClassLevelRemove"

class SignalType(Enum):
    SOURCE = "SOURCE"
    RECIEVER = "RECIEVER"

