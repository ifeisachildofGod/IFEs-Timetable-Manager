
from typing import Optional
from dataclasses import dataclass

from .base import Time

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
class TimetableTime:
    start_time: Time
    interval: int
    break_time_duration: int
    
    def copy(self):
        return TimetableTime(self.start_time, self.interval, self.break_time_duration)

class TimetableGeneratorError(Exception):
    pass




