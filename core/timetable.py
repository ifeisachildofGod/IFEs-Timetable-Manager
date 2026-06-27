
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
    weekday_text_theme: TextTheme
    break_text_theme: TextTheme
    
    ttbl_bg_color: str
    ttbl_cell_bg_color: str
    weekday_bg_color: str
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

