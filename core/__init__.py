
"""Core framework backbone"""

import random
from dataclasses import dataclass
from typing import Optional, TypeVar

from core.main import *
from core.timing_and_timetable import *


_T = TypeVar("_T")


@dataclass
class AppData:
    prefect_attendance_time_settings: StaffAttendanceTimeSettings
    teacher_attendance_time_settings: StaffAttendanceTimeSettings
    
    attendance_data: list[AttendanceEntry]
    
    def __init__(self, /, **kwds):
        self.__dict__ = kwds
        
        assert \
            self.prefect_attendance_time_settings.check_in_time.in_minutes() + self.prefect_attendance_time_settings.check_in_border_interval_minutes < self.prefect_attendance_time_settings.check_out_time.in_minutes() - self.prefect_attendance_time_settings.check_out_border_interval_minutes,\
            f"\nPrefect Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.prefect_attendance_time_settings.check_in_time.in_minutes() + self.prefect_attendance_time_settings.check_in_border_interval_minutes}\nCheck-Out lower border: {self.prefect_attendance_time_settings.check_out_time.in_minutes() - self.prefect_attendance_time_settings.check_out_border_interval_minutes}"
        
        assert \
            self.teacher_attendance_time_settings.check_in_time.in_minutes() + self.teacher_attendance_time_settings.check_in_border_interval_minutes < self.teacher_attendance_time_settings.check_out_time.in_minutes() - self.teacher_attendance_time_settings.check_out_border_interval_minutes,\
            f"\nTeacher Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.teacher_attendance_time_settings.check_in_time.in_minutes() + self.teacher_attendance_time_settings.check_in_border_interval_minutes}\nCheck-Out lower border: {self.teacher_attendance_time_settings.check_out_time.in_minutes() - self.teacher_attendance_time_settings.check_out_border_interval_minutes}"


class Global(dict[ID, _T]):
    def __init__(self, school: "School | None" = None):
        super().__init__()
        
        self.school = school
    
    def set_school(self, school: "School"):
        self.school = school
    
    def add(self, entry: _T, index: Optional[int] = None):
        assert entry.id not in self, f"{entry.__class__.__name__} (ID: {entry.id}) exists already as {self[entry.id].__class__.__name__} {self[entry.id].name.full()}"
        
        if index is None:
            self[entry.id] = entry
        else:
            items = list(self.items())
            items.insert(index, (entry.id, entry))
            
            self.clear()
            self.update(dict(items))
    
    def remove(self, id: ID):
        self.pop(id)


class GlobalSubjects(Global[Subject | CombinedSubject]):
    pass

class GlobalTeachers(Global[Teacher]):
    pass

class GlobalPrefects(Global[Prefect]):
    pass

class GlobalClassLevels(Global[ClassLevel]):
    def add(self, entry: ClassLevel, index: Optional[int] = None):
        self.school.settings.TEACHER_rsma_mapping[entry.id] = None
        self.school.settings.TIMETABLE_time_settings[entry.id] = {"Everyday": SCHOOL.settings.DEFAULT_timetable_time_setting.copy()}
        self.school.settings.EXPORT_selected_classes[entry.id] = []
        
        return super().add(entry, index)
    
    def add_class(self, id: ID, cls: Class):
        self[id].classes[cls.id] = cls
        
        cls.timetable.clear()
    
    def remove_class(self, id: ID, cls_id: CLASS_ID):
        if cls_id in SCHOOL.settings.EXPORT_selected_classes[id]:
            SCHOOL.settings.EXPORT_selected_classes[id].remove(cls_id)
        
        self[id].classes[cls_id].delete()


@dataclass
class Settings:
    THEME: str
    
    DEFAULT_period_amount: int
    DEFAULT_break_period: int
    DEFAULT_max_classes: int
    DEFAULT_occurance_data: tuple[int, int]
    DEFAULT_timetable_time_setting: TimetableTime
    
    TEACHER_rsma_mapping: dict[ID, Optional[int]]
    
    TIMETABLE_weekdays: list[str]
    TIMETABLE_time_settings: dict[ID, dict[str, TimetableTime]]
    
    EXPORT_timetable_export_theme: TimetableExportTheme
    EXPORT_attendance_settings: AttendanceExportSettings
    EXPORT_selected_classes: dict[ID, list[ID]]
    
    ID_index: int
    auto_save: bool


class School:
    def __init__(self):
        self.subjects = GlobalSubjects(self)
        self.teachers = GlobalTeachers(self)
        self.prefects = GlobalPrefects(self)
        self.class_levels = GlobalClassLevels(self)
        
        self.gen_data = GeneratingData({}, {}, {}, {})
        self.settings = Settings(
            "dark-blue",
            10, 7, 3, (1, 1), TimetableTime(Time(8, 10, 0), 35, 35),
            {},
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], {},
            TimetableExportTheme(
                None, None, None,
                "white", "white", "black", "black", "black",
                1, 1,
                0, "PNG"
            ),
            AttendanceExportSettings(None, None, "CSV", [False, False, False, False, False, False]),
            {}, 0, False
        )
        self.attendance = AppData(
            prefect_attendance_time_settings = StaffAttendanceTimeSettings(
                check_in_time = Time(7, 0, 0),
                check_out_time = Time(15, 0, 0),
                check_in_border_interval_minutes = 60,
                check_out_border_interval_minutes = 60,
                timeline_dates = [
                    (
                        Period(time=Time(0, 0, 0), day="Thursday", date=1, month="January", year=2026),
                        Period(time=Time(0, 0, 0), day="Thursday", date=31, month="December", year=2026)
                    )
                ]
            ),
            teacher_attendance_time_settings = StaffAttendanceTimeSettings(
                check_in_time = Time(7, 0, 0),
                check_out_time = Time(15, 0, 0),
                check_in_border_interval_minutes = 60,
                check_out_border_interval_minutes = 60,
                timeline_dates = [
                    (
                        Period(time=Time(0, 0, 0), day="Thursday", date=1, month="January", year=2026),
                        Period(time=Time(0, 0, 0), day="Thursday", date=31, month="December", year=2026)
                    )
                ]
            ),
            
            attendance_data = [],
        )
        
        self.posts: dict[ID, str] = {}
        
        assert \
            self.attendance.prefect_attendance_time_settings.check_in_time.in_minutes() + self.attendance.prefect_attendance_time_settings.check_in_border_interval_minutes < self.attendance.prefect_attendance_time_settings.check_out_time.in_minutes() - self.attendance.prefect_attendance_time_settings.check_out_border_interval_minutes,\
            f"\nPrefect Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.attendance.prefect_attendance_time_settings.check_in_time.in_minutes() + self.attendance.prefect_attendance_time_settings.check_in_border_interval_minutes}\nCheck-Out lower border: {self.attendance.prefect_attendance_time_settings.check_out_time.in_minutes() - self.attendance.prefect_attendance_time_settings.check_out_border_interval_minutes}"
        
        assert \
            self.attendance.teacher_attendance_time_settings.check_in_time.in_minutes() + self.attendance.teacher_attendance_time_settings.check_in_border_interval_minutes < self.attendance.teacher_attendance_time_settings.check_out_time.in_minutes() - self.attendance.teacher_attendance_time_settings.check_out_border_interval_minutes,\
            f"\nTeacher Check-In and Check-Out times overlap:\n\nCheck-In upper border: {self.attendance.teacher_attendance_time_settings.check_in_time.in_minutes() + self.attendance.teacher_attendance_time_settings.check_in_border_interval_minutes}\nCheck-Out lower border: {self.attendance.teacher_attendance_time_settings.check_out_time.in_minutes() - self.attendance.teacher_attendance_time_settings.check_out_border_interval_minutes}"
        
        self._log_data = {}
    
    def set(self, school: "School"):
        self.subjects.update(school.subjects)
        self.teachers.update(school.teachers)
        self.prefects.update(school.prefects)
        self.class_levels.update(school.class_levels)
        
        self.settings.__dict__.update(school.settings.__dict__)
        self.gen_data.__dict__.update(school.gen_data.__dict__)
        self.attendance.__dict__.update(school.attendance.__dict__)
        
        self.posts.update(school.posts)
    
    def detect_clashes(self):
        """
        Returns {
            ((Day, PeriodIndex), (SubjectID, TeacherID)): [Class, ...]
        }
        """
        
        clashes: dict[tuple[tuple[str, int], tuple[ID, ID]], list[Class]] = {}
        
        days_uid_tracker: dict[str, dict[tuple[str, int], list[tuple[tuple[ID, ID], Class]]]] = {}
        
        for class_level in self.class_levels.values():
            for c_id, cls in class_level.classes.items():
                for day, periods in cls.timetable.table.items():
                    if day not in days_uid_tracker:
                        days_uid_tracker[day] = {}
                        
                        for i, subj in enumerate(periods):
                            if subj.id in (FreePeriod.id, BreakPeriod.id):
                                continue
                            
                            if isinstance(subj, CombinedSubject):
                                subjs = [s for s in subj.subjects if s.teacher is not None]
                            elif isinstance(subj, Subject):
                                if subj.teacher is None:
                                    continue
                                
                                subjs = [subj]
                            
                            if i not in days_uid_tracker:
                                days_uid_tracker[day][i] = []
                            
                            for s in subjs:
                                days_uid_tracker[day][i].append(((s.id, s.teacher.id), s.classes[c_id]))
                        
                        continue
                    
                    for i, subj in enumerate(periods):
                        if subj.id in (FreePeriod.id, BreakPeriod.id):
                            continue
                        
                        if isinstance(subj, CombinedSubject):
                            subjs = [s for s in subj.subjects]
                        elif isinstance(subj, Subject):
                            assert subj.teacher is not None
                            
                            subjs = [subj]
                        
                        for s in subjs:
                            if s.teacher is None:
                                continue
                            
                            key = (day, i), (s_uid := (s.id, s.teacher.id))
                            cls = s.classes[c_id]
                            
                            if i in days_uid_tracker[day]:
                                clash_data = next(((j, uid, c) for j, (uid, c) in enumerate(days_uid_tracker[day][i]) if (s_uid == uid) and c.id != cls.id), None)
                                
                                if clash_data is not None:
                                    clash_subject_index, (o_s_id, _), o_cls = clash_data
                                    
                                    is_combined = next(
                                        (
                                            True
                                            for s_list, c_list in
                                            self.gen_data.combined_subjects[class_level.id]
                                            if (subj.id in s_list and o_s_id in s_list) and (cls.id in c_list and o_cls.id in c_list)
                                        ),
                                        False
                                    )
                                    
                                    if is_combined:
                                        continue
                                    
                                    if key not in clashes:
                                        clashes[key] = []
                                    
                                    clash_cls = days_uid_tracker[day][i][clash_subject_index][1]
                                    
                                    if clash_cls not in clashes[key]:
                                        clashes[key].append(clash_cls)
                                    
                                    clashes[key].append(cls)
                                else:
                                    days_uid_tracker[day][i].append((s_uid, cls))
        
        return clashes
    
    def detect_islands(self):
        islands: dict[ID, tuple[ClassLevel, list[tuple[ID, str, int]]]] = {}
        
        for class_level in self.class_levels.values():
            for c_id, cls in class_level.classes.items():
                for day, periods in cls.timetable.table.items():
                    seen_subjects = []
                    
                    for subject_index, subject in enumerate(periods):
                        subj_id = subject.id
                        
                        if subj_id in (FreePeriod.id, BreakPeriod.id):
                            continue
                        
                        prev_subj_id = periods[subject_index - 1].id if subject_index > 0 else None
                        next_subj_id = periods[subject_index + 1].id if subject_index < len(periods) - 1 else None
                        
                        if subj_id not in (prev_subj_id, next_subj_id) and subj_id in seen_subjects:
                            if c_id not in islands:
                                islands[c_id] = class_level, []
                            
                            islands[c_id][1].append(((subj_id, day, subject_index)))
                            if seen_subjects.count(subj_id) == 1:
                                islands[c_id][1].append(((subj_id, day, periods.index(subject))))
                        
                        seen_subjects.append(subj_id)
            
        return islands
    
    def template(self):
        subjects_template = "\n".join([subject.template(self) for subject in self.subjects.values()])
        teachers_template = "\n".join([teacher.template(self) for teacher in self.teachers.values()])
        cls_lvls_template = "--".join([cls_lvl.template(self) for cls_lvl in self.class_levels.values()])
        prefects_template = ", ".join([f"({post_id} - {post})" for post_id, post in self.posts.items()]) + "\n" + "\n".join([prefect.template(self) for prefect in self.prefects.values()])
        
        return f"{subjects_template}\n---\n{teachers_template}\n---\n{cls_lvls_template}\n---\n{prefects_template}"
    
    @staticmethod
    def from_template(template: str):
        template = "\n".join([(line + " ")[:line.find("#")] for line in template.splitlines()])
        
        school = School()
        
        subject_str, teacher_str, cls_lvl_str, full_prefect_str = template.strip().split("---")
        
        subject_str_split = subject_str.strip().split("\n")
        
        for subj_template in subject_str_split:
            if ":" not in subj_template:
                subject = Subject.from_template(subj_template.strip(), school)
                
                school.subjects.add(subject)
        
        for i, subj_template in enumerate(subject_str_split):
            if ":" in subj_template:
                combinded_subject = CombinedSubject.from_template(subj_template.strip(), school)
                
                school.subjects.add(combinded_subject, i)
        
        for teacher_template in teacher_str.strip().split("\n"):
            teacher = Teacher.from_template(teacher_template.strip(), school)
            
            school.teachers.add(teacher)
        
        for cls_lvl_template in cls_lvl_str.strip().split("--"):
            cls_lvl = ClassLevel.from_template(cls_lvl_template.strip(), school)
            
            school.class_levels.add(cls_lvl)
        
        posts_template, *prefect_str_list = full_prefect_str.strip().split("\n")
        
        school.posts = {ID(post_data[0].strip()): post_data[1].strip() for post_template in posts_template.strip().split(",") if (post_data := post_template.strip().removeprefix("(").removesuffix(")").split("-"))}
        
        for prefect_template in prefect_str_list:
            prefect = Prefect.from_template(prefect_template.strip(), school)
            
            school.prefects.add(prefect)
        
        return school


SCHOOL = School()


if __name__ == "__main__":
    def display_school(sch: School):
        for cls_lvl in sch.class_levels.values():
            for cls in cls_lvl.classes.values():
                print(cls_lvl.name.full(), cls.name)
                for day, periods in cls.timetable.table.items():
                    print(day, end=": ")
                    print(*[(p.name.full() if not isinstance(p, CombinedSubject) else "/".join([s.name for s in p.subjects])) for p in periods], sep=", ")
                
                if cls.timetable.table_remains:
                    print()
                    print("Remainders:", ", ".join([s.name.full() for s in cls.timetable.table_remains]))
                    print()
                print()
    
    with open(r"test.save\test.frmwk") as file:
        data = file.read()
    
    sch = School.from_template(data)
    
    print("Started Generating")
    for cls_lvl in sch.class_levels.values():
        for cls in cls_lvl.classes.values():
            cls.timetable.generate()
    print("Started Clash detection")
    print(sch.detect_clashes())
    print("Ended")
    print()
    
    display_school(sch)


def NEW_ID():
    SCHOOL.settings.ID_index += 1
    _id = ID(SCHOOL.settings.ID_index)
    
    return _id

def NEW_CLASS_ID(class_level_id: ID):
    SCHOOL.settings.ID_index += 1
    _id = CLASS_ID(SCHOOL.settings.ID_index)
    
    _id.class_level_id = class_level_id
    
    return _id
