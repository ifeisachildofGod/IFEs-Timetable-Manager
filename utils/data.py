
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
    
    def add(self, cls: Class):
        self.classes[cls.id] = cls


@dataclass
class Settings:
    GENERAL_periodamt: int
    TEACHER_rsma_mapping: dict[ID, Optional[int]]
    TEACHER_default_max_classes: int
    TIMETABLE_breakperiod: int
    TIMETABLE_weekdays: list[str]


