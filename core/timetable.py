
from dataclasses import dataclass

from core.settings import *

class TimetableGeneratorError(Exception):
    pass


@dataclass
class GeneratingData:
    randomize: bool
    #                             ClassID    SubjectID    Day    DayWeight  PeriodProclivity
    subject_positioning_weights: dict[str, dict[str, dict[str, tuple[float, int]]]]
    
    #                          ClassID    SubjectID    Day  Weight
    subject_clumping_weights: dict[str, dict[str, dict[str, float]]]
    
    #                       SubjectID  ClassIDs
    combined_subjects: dict[list[str], list[str]]


@dataclass
class FreePeriod:
    id: str = "FreePeriodID"
    
    name: SubjectName = "Free"
    teacher: "Teacher | None" = None
    
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        
        self.name = SubjectName("Free", "Free")

@dataclass
class BreakPeriod:
    id: str = "BreakPeriodID"
    
    name: str = "Break"
    teacher: "Teacher | None" = None
    
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        
        self.name = SubjectName("Break", "Break")


# Objects
TimetableFW = dict[str, list[Subject | CombinedSubject | BreakPeriod | FreePeriod]]

