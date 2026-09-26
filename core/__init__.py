
"""Core framework backbone"""

import json
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

class GlobalClassLevels(Global[ClassLevel]):
    def add(self, entry: ClassLevel, index):
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
        self.prefects = {}
        self.class_levels = GlobalClassLevels(self)
        
        self.gen_data = GeneratingData({}, {}, {}, [])
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
        self.class_levels.update(school.class_levels)
        
        self.settings.__dict__.update(school.settings.__dict__)
        self.gen_data.__dict__.update(school.gen_data.__dict__)
        self.attendance.__dict__.update(school.attendance.__dict__)
    
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
                                if subj.teacher is not None:
                                    continue
                                
                                subjs = [subj]
                            
                            if i not in days_uid_tracker:
                                days_uid_tracker[day][i] = []
                            
                            for s in subjs:
                                days_uid_tracker[day][i].append(((s.id, s.teacher.id, i), s.classes[c_id]))
                        
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
                                    clash_subject_index, (o_s_id, _, _), o_cls = clash_data
                                    
                                    is_combined = next(
                                        (
                                            True
                                            for s_list, c_list in
                                            cls.timetable.gen_data.combined_subjects.items()
                                            if (subj.id in s_list and o_s_id in s_list) and (cls.id in c_list and o_cls.id in c_list)
                                        ),
                                        False
                                    )
                                    
                                    if not is_combined:
                                        if key not in clashes:
                                            clashes[key] = []
                                        
                                        clash_cls = days_uid_tracker[day][i][clash_subject_index][1]
                                        
                                        if clash_cls not in clashes[key]:
                                            clashes[key].append(clash_cls)
                                        
                                        clashes[key].append(cls)
                                else:
                                    days_uid_tracker[day][i].append((s_uid, cls))
        print(days_uid_tracker)
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
                                islands[c_id] = subject.classes[c_id].level, []
                            
                            islands[c_id][1].append(((subj_id, day, subject_index)))
                            if seen_subjects.count(subj_id) == 1:
                                islands[c_id][1].append(((subj_id, day, periods.index(subject))))
                        
                        seen_subjects.append(subj_id)
            
        return islands
    
    @staticmethod
    def id_name_from_text(text: str):
        text = text.strip().removeprefix("(").removesuffix(")")
        
        sep_index = text.rfind("-")
        
        return text[:sep_index].strip(), text[sep_index + 1:].strip()
    
    @staticmethod
    def from_template(text: str):
        text = "\n".join(["".join(list(line)[:line.find("#")] if "#" in line else list(line)) for line in text.splitlines()])

        school_framework = School()
        
        subjects_string, teachers_string, classes_string, dotw_string = text.split("---") #, timetable_string = text.split("---")
        
        subjects_string = subjects_string.strip()
        teachers_string = teachers_string.strip()
        classes_string = classes_string.strip()
        # timetable_string = timetable_string.strip()
        dotw_string = dotw_string.strip()
        
        for s_index, s_info in enumerate(subjects_string.splitlines()):
            if s_info.strip():
                s_name, s_id = School.id_name_from_text(s_info)
                
                s_id = ID(s_id)
                if "/" in s_name:
                    if s_name.count("(") == 1 and s_name.count(")") == 1:
                        n, s_str = School.id_name_from_text(s_name)
                        
                        cs_d_s = s_str
                        s_name = SubjectName(n.strip(), n.strip())
                    else:
                        cs_d_s = s_name
                        s_name = SubjectName(None, None)
                    
                    subjs = [next(cs for i, cs in enumerate(school_framework.subjects.values()) if i == int(s.strip()) - 1) for s in cs_d_s.strip().split("/")]
                    subject = CombinedSubject(s_id, s_name, subjs)
                else:
                    if "â–" in s_name:
                        names = [n.strip() for n in s_name.split("â–")]
                    else:
                        names = [s_name, s_name]
                    
                    subject = Subject(s_id, SubjectName(*names), None, {})
                
                school_framework.subjects.add(subject)
        
        teacher_subject_indices = {}
        for t_string in teachers_string.splitlines():
            t_string = t_string.strip()
            
            if t_string:
                if ":" in t_string:
                    t_info, value =  t_string.split(":")
                else:
                    t_info = t_string
                    value = None
                
                t_name, t_id = School.id_name_from_text(t_info)
                
                t_id = ID(t_id)
                t_name = t_name.strip()
                
                if "■" in t_name:
                    names = [n.strip() if n.strip() else None for n in t_name.split("■")]
                else:
                    names = [t_name, None, None, ""]
                
                teacher = Teacher(t_id, None, StaffName(*names), "AttendanceApp/src/profile-images/t_id1.png", [], {})
                
                school_framework.teachers.add(teacher)
                
                if value is not None:
                    teacher_subject_indices[t_id] = tuple(int(v) - 1 for v in value.strip().split())
                    
                    for s_index in teacher_subject_indices[t_id]:
                        subj = list(school_framework.subjects.values())[s_index]
                        school_framework.teachers[t_id].subjects[subj.id] = subj
        
        weekdays_data = []
        if dotw_string:
            for dw_string in dotw_string.split("_"):
                cl_dw_info = dw_string.splitlines()
                (p_amt, b_p), dw_info = cl_dw_info[0].split(), cl_dw_info[1:]
                
                weekdays_data.append(([int(p_amt), int(b_p)], dw_info))
        else:
            weekdays_data = [
                (
                    (
                        school_framework.settings.DEFAULT_period_amount,
                        school_framework.settings.DEFAULT_break_period
                    ),
                    school_framework.settings.TIMETABLE_weekdays.copy()
                )
                for _ in
                classes_string.split("_")
            ]
        
        all_classes = []
        l_subjects = list(school_framework.subjects.values())
        l_teachers = list(school_framework.teachers.values())
        if classes_string:
            for cls_lvl_index, cls_lvl_string in enumerate(classes_string.split("_")):
                cls_lvl_data = cls_lvl_string.splitlines()
                cls_lvl_info, cls_data = cls_lvl_data[0], cls_lvl_data[1:]
                
                if ":" in cls_lvl_info:
                    cls_lvl_id_data, subjects_occurence_string = cls_lvl_info.split(":")
                else:
                    cls_lvl_id_data = cls_lvl_info.strip()
                    subjects_occurence_string = None
                
                cls_lvl_name, lvl_id = School.id_name_from_text(cls_lvl_id_data)
                
                subjects_occurence = {}
                
                if subjects_occurence_string is not None:
                    for occ_string in subjects_occurence_string.strip().split():
                        occ_string = occ_string.strip()
                        
                        if occ_string:
                            gs_index, day_max, week_max = occ_string.split("/")
                            
                            subjects_occurence[l_subjects[int(gs_index.strip()) - 1].id] = SubjectOccurrance(int(day_max.strip()), int(week_max.strip()))
                    
                lvl_id = ID(lvl_id) ; classes = {} ; (p_amt, b_p), weekdays = weekdays_data[cls_lvl_index]
                cls_lvl = ClassLevel(lvl_id, ClassLevelName(cls_lvl_name), classes, subjects_occurence, weekdays, p_amt, b_p)
                school_framework.class_levels.add(cls_lvl)
                
                for c_string in cls_data:
                    c_string = c_string.strip()
                    
                    if ":" in c_string:
                        cls_info, value =  c_string.split(":")
                    else:
                        cls_info = c_string.strip()
                        value = None
                    
                    cls_name, cls_id = School.id_name_from_text(cls_info)
                    
                    subject_mapping = {}
                    
                    # Volatile
                    if value is not None:
                        for v in value.strip().split():
                            s_list = v.split("/")
                            
                            if len(s_list) == 1:
                                t_index = s_list
                                s_index = "1"
                            elif len(s_list) == 2:
                                t_index, s_index = s_list
                            else:
                                raise Exception()
                            
                            t_index = int(t_index.strip()) - 1
                            s_index = int(s_index.strip()) - 1
                            
                            if not (0 <= t_index <= len(l_teachers) - 1):
                                raise IndexError(f"Invalid teacher index: {t_index + 1}")
                            
                            teacher = l_teachers[t_index]
                            subject_indices = teacher_subject_indices[teacher.id]
                            
                            if not (0 <= s_index <= len(subject_indices) - 1):
                                raise IndexError(f"Invalid teacher-subject index: {s_index + 1}")
                            
                            if not (0 <= subject_indices[s_index] <= len(l_subjects) - 1):
                                raise IndexError(f"Invalid subject index: {subject_indices[s_index] + 1}")
                            
                            o_subject = l_subjects[subject_indices[s_index]]
                            
                            # if isinstance(o_subject, Subject):
                            #     o_subject.classes[cls_id] = classes[cls_id]
                            
                            subject = o_subject.passCopy()
                            subject.teacher = teacher
                            
                            subject_mapping[subject.id] = subject
                    # Volatile
                    
                    cls_id = ID(cls_id.strip())
                    cls = classes[cls_id] = Class(cls_id, cls_name, cls_lvl, subject_mapping, school_framework)
                    all_classes.append(cls)
                    
                    school_framework.class_levels.add_class(lvl_id, cls)
        
        school_framework.prefects = {
            "p_id1": Prefect(
                id = "p_id1",
                IUD = "6999BDB2",
                name = StaffName(start="Eze", first="Emmmanuel", other="Udochukwu", abbrev="Emma"),
                post_name = "Parade Commander",
                cls = random.choice(all_classes),
                img_path = "AttendanceApp/src/profile-images/p_id1.png",
                duties = {"Wednesday": ["Morning", "Assembly parade", "Cadet training"]},
                attendance = []
            ),
            "p_id2": Prefect(
                id = "p_id2",
                IUD = "637B910C",
                name = StaffName(start="Eshiokwu", first="Johnpaul", other="Bassey", abbrev="J.P"),
                post_name = "Band Prefect",
                cls = random.choice(all_classes),
                img_path = "AttendanceApp/src/profile-images/p_id1.png",
                duties = {"Monday": ["Morning", "Band"], "Thursday": ["Afternoon", "Band practice"], "Friday": ["Morning", "Band"]},
                attendance = []
            ),
            "p_id3": Prefect(
                id = "p_id3",
                IUD = "A3DEB30C",
                name = StaffName(start="Igboke", first="Chisom", other="Joseph", abbrev="Chisom"),
                post_name = "Ast. Games",
                cls = random.choice(all_classes),
                img_path = "AttendanceApp/src/profile-images/p_id1.png",
                duties = {"Monday": ["Afternoon", "Boys Footbal"], "Tuesday": ["Afternoon", "Boys Footbal"], "Wednesday": ["Afternoon", "Boys Footbal"], "Thursday": ["Afternoon", "Boys Footbal"], "Friday": ["Afternoon", "Boys Footbal"]},
                attendance = []
            ),
            "p_id4": Prefect(
                id = "p_id4",
                IUD = "B3A6DE0C",
                name = StaffName(start="Anyanwu", first="Divine", other="Godswill", abbrev="Onuwa"),
                post_name = "Chapel Prefect",
                cls = random.choice(all_classes),
                img_path = "AttendanceApp/src/profile-images/p_id1.png",
                duties = {"Monday": ["Morning Prayers"]},
                attendance = []
            ),
            "p_id5": Prefect(
                id = "p_id5",
                IUD = "89A2A1B2",
                name = StaffName(start="Eze", first="Ifebuche", other="Esther", abbrev="Esther"),
                post_name = "Games Prefect (Girl)",
                cls = random.choice(all_classes),
                img_path = "AttendanceApp/src/profile-images/p_id1.png",
                duties = {"Wednesday": ["Afternoon", "Girls Football" ]},
                attendance = []
            )
        }
        
        return school_framework
    
    def framework(self):
        text = ""
        
        l_subjects = list(s_id for s_id, _ in self.subjects)
        for s_id, s in self.subjects:
            if isinstance(s, Subject):
                name = s.name.full() if s.name.full() == s.name.short() else f"{s.name.full()} ■ {s.name.short()}"
            else:
                name = "/".join([l_subjects.index(s.id) + 1 for s in s.subjects.values()])
                
                if s.name is not None:
                    name = f"({s.name.full()} - {name})"
            
            text += f"({name} - {s_id})" + "\n"
        
        text += "---\n"
        
        s_t_index_mapping = {}
        l_teachers = list(t_id for t_id, _ in self.teachers)
        for t_id, t in self.teachers:
            s_t_index_mapping[t_id] = [l_subjects.index(t_s_id) + 1 for t_s_id in t.subjects]
            
            name = t.name.full() if t.name.full() == t.name.short() else f"{t.name.start} ■ {t.name.first if t.name.first else ""} ■ {t.name.other if t.name.other else ""} ■ {t.name.abbrev}"
            subject_indexes = " ".join([str(i) for i in s_t_index_mapping[t_id]])
            
            text += f"({name} - {t_id}): {subject_indexes}\n"
        
        text += "---\n"
        
        weekdays = ""
        for ci, (cl_id, cl) in enumerate(self.class_levels):
            weekdays += f"{cl.period_amount} {cl.break_period}\n" + "\n".join(cl.weekdays)
            
            subjects_occurence = " ".join([f"{l_subjects.index(cl_s_id) + 1}/{cl_so.day_max}/{cl_so.week_max}" for cl_s_id, cl_so in cl.subjects_occurence.items()])
            
            text += f"({cl.name.full()} - {cl_id}): {subjects_occurence}\n"
            
            for c_id, c in cl.classes.items():
                t_s_mapping = " ".join([f"{l_teachers.index(c_s.teacher.id) + 1}/{s_t_index_mapping[c_s.teacher.id].index(l_subjects.index(c_s_id) + 1) + 1}" for c_s_id, c_s in c.subjects.items()])
                
                text += f"({c.name} - {c_id}): {t_s_mapping}\n"
            
            if ci < len(self.class_levels) - 1:
                text += "_"
                weekdays += "_"
        
        text += "---\n"
        
        text += weekdays
        
        return text


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
