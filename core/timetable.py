
from dataclasses import dataclass

from core.settings import *

class TimetableGeneratorError(Exception):
    pass

@dataclass
class Margins:
    left: int
    top: int
    right: int
    bottom: int

@dataclass
class TextTheme:
    family: str
    size: int
    bold: bool
    italic: bool
    
    color: str
    letter_spacing: int
    opacity: int
    underline: bool
    overline: bool
    text_alignment: str
    
    stylesheet: Optional[str] = None

@dataclass
class TimetableExportTheme:
    cls_title_text_theme: TextTheme
    ttbl_content_text_theme: TextTheme
    ttbl_heading_text_theme: TextTheme
    
    ttbl_bg_color: str
    ttbl_content_bg_color: str
    ttbl_heading_bg_color: str
    break_bg_color: str
    border_color: str
    
    horizontal_line_thickness: int
    vertical_line_thickness: int
    
    export_mode: int
    export_file_type: str

@dataclass
class Time:
    hour: int
    minute: int
    
    def copy(self):
        return Time(self.hour, self.minute)
    
    def __repr__(self):
        return f"{self.hour}:{"0" if self.minute < 10 else ""}{self.minute}"
    
    def __mul__(self, other: int):
        return Time(self.hour * other, self.minute * other) + 0
    
    def __add__(self, other: "Time | int"):
        if isinstance(other, Time):
            min = other.hour * 60 + self.minute + other.minute
        elif isinstance(other, int):
            min = self.minute + other
        else:
            raise TypeError(f"Cannot add {type(other)} to Time")
        
        return Time(self.hour + min // 60, min % 60)
    
    def __radd__(self, other):
        self.__add__(other)
    
    def __rmul__(self, other):
        self.__mul__(other)

@dataclass
class TimetableTime:
    start_time: Time
    interval: int
    break_time_duration: int
    
    def copy(self):
        return TimetableTime(self.start_time, self.interval, self.break_time_duration)

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

