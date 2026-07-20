
from typing import Any
from dataclasses import dataclass

from imports import *


@dataclass
class AppData:
    prefect_cit: Time
    prefect_cot: Time
    
    teacher_cit: Time
    teacher_cot: Time
    
    teacher_cin_border_interval_minutes: float | int
    teacher_cout_border_interval_minutes: float | int
    
    prefect_cin_border_interval_minutes: float | int
    prefect_cout_border_interval_minutes: float | int
    
    teacher_timeline_dates: list[tuple[Period, Period]]
    prefect_timeline_dates: list[tuple[Period, Period]]
    
    teachers: dict[str, Teacher]
    prefects: dict[str, Prefect]
    
    variables: dict[str, Any]
    
    attendance_data: list[AttendanceEntry]
    
    def __init__(self, /, **kwds):
        self.__dict__ = kwds
        
        assert \
            self.prefect_cit.in_minutes() + self.prefect_cin_border_interval_minutes < self.prefect_cot.in_minutes() - self.prefect_cout_border_interval_minutes,\
            f"\nPrefect Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.prefect_cit.in_minutes() + self.prefect_cin_border_interval_minutes}\nCheck-Out lower border: {self.prefect_cot.in_minutes() - self.prefect_cout_border_interval_minutes}"
        
        assert \
            self.teacher_cit.in_minutes() + self.teacher_cin_border_interval_minutes < self.teacher_cot.in_minutes() - self.teacher_cout_border_interval_minutes,\
            f"\nTeacher Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.teacher_cit.in_minutes() + self.teacher_cin_border_interval_minutes}\nCheck-Out lower border: {self.teacher_cot.in_minutes() - self.teacher_cout_border_interval_minutes}"




