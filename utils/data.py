
import random

from typing import Optional
from dataclasses import dataclass

from core import ID


@dataclass
class SubjectOccurrence:
    day_max: int
    week_max: int


@dataclass
class Class:
    id: ID
    name: str
    
    level: "ClassLevel"
    subjects: dict[ID, "Subject"]


@dataclass
class Entry:
    id: ID

@dataclass
class SubjectName:
    full: str
    abbrev: Optional[str]

@dataclass
class TeacherName:
    start: str
    first: Optional[str]
    other: Optional[str]
    abbrev: str

@dataclass
class Subject(Entry):
    name: SubjectName
    
    teacher: Optional["Teacher"]
    classes: dict[ID, Class]
    
    occurance: Optional[SubjectOccurrence]
    
    def passCopy(self):
        return Subject(self.id, self.name, None, self.classes, SubjectOccurrence(self.occurance.day_max, self.occurance.week_max) if self.occurance else None)

@dataclass
class Teacher(Entry):
    name: TeacherName
    
    subjects: dict[ID, Subject]

@dataclass
class ClassLevel(Entry):
    name: str
    classes: dict[ID, Class]


@dataclass
class Settings:
    GENERAL_periodamt: int
    TEACHER_rsma_mapping: dict[ID, Optional[int]]
    TEACHER_default_max_classes: int
    TIMETABLE_breakperiod: int
    TIMETABLE_weekdays: dict[str, tuple[int, int]]
    THEME: str
    
    def set(self, value):
        self.__dict__ = value.__dict__


