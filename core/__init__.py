
"""Core framework backbone"""

from dataclasses import dataclass
from typing import Optional, TypeVar

from core.base import *
from core.settings import *
from core.timetable import *


_T = TypeVar("_T")

class Global(dict[ID, _T]):
    def __init__(self, school: "School | None" = None):
        super().__init__()
        
        self.school = school
    
    def set_school(self, school: "School"):
        self.school = school
    
    def add(self, entry: _T):
        self[entry.id] = entry
    
    def remove(self, id: ID):
        self.pop(id)
    
    def set(self, value):
        self.clear()
        self.update(value)


class GlobalSubjects(Global[Subject | CombinedSubject]):
    pass

class GlobalTeachers(Global[Teacher| CombinedTeacher]):
    pass

class GlobalClassLevels(Global[ClassLevel]):
    def add(self, entry: ClassLevel):
        self.school.settings.TEACHER_rsma_mapping[entry.id] = None
        self.school.settings.TIMETABLE_time_settings[entry.id] = {"Everyday": SCHOOL.settings.DEFAULT_timetable_time_setting.copy()}
        self.school.settings.EXPORT_selected_classes[entry.id] = []
        
        return super().add(entry)
    
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
    EXPORT_selected_classes: dict[ID, list[ID]]
    
    def set(self, value):
        self.__dict__ = value.__dict__


class School:
    def __init__(self):
        self.subjects = GlobalSubjects(self)
        self.teachers = GlobalTeachers(self)
        self.class_levels = GlobalClassLevels(self)
        
        self.gen_data = GeneratingData({}, {}, {}, {})
        self.settings = Settings(
            "dark-blue",
            10, 7, 3, (2, 4), TimetableTime(Time(8, 10), 35, 35),
            {},
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], {},
            TimetableExportTheme(
                None, None, None,
                "white", "white", "black", "black", "black",
                1, 1,
                0, "PNG"
            ), {}
        )
        
        self._log_data = {}
    
    def set(self, school: "School"):
        self.subjects.set(school.subjects)
        self.teachers.set(school.teachers)
        self.class_levels.set(school.class_levels)
        
        self.settings.__dict__ = school.settings.__dict__
        self.gen_data.__dict__ = school.gen_data.__dict__
    
    def detect_clashes(self):
        """
        Returns {
            ((Day, PeriodIndex), SubjectID + TeacherID): [Class, ...]
        }
        """
        
        clashes: dict[tuple[tuple[str, int], tuple[ID, ID]], list[Class]] = {}
        
        days_uid_tracker: dict[str, list[tuple[tuple[ID, ID], Class]]] = {}
        
        for class_level in self.class_levels.values():
            for c_id, cls in class_level.classes.items():
                for day, periods in cls.timetable.table.items():
                    if day not in days_uid_tracker:
                        days_uid_tracker[day] = [[((s.id, s.teacher.id), s.classes[c_id]) if s.id not in (FreePeriod.id, BreakPeriod.id) else (None, None)] for s in periods]
                        continue
                    
                    for i, subj in enumerate(periods):
                        if subj.id not in (FreePeriod.id, BreakPeriod.id):
                            s_uid = subj.id, subj.teacher.id
                            
                            key = (day, i), s_uid
                            cls = subj.classes[c_id]
                            
                            if i < len(days_uid_tracker[day]):
                                clash_subject_index = next((j for j, (uid, c) in enumerate(days_uid_tracker[day][i]) if s_uid == uid and c.id != cls.id), None)
                                
                                if clash_subject_index is not None:
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
                        
                        s_name = SubjectName(n.strip(), n.strip())
                        subjs = [[cs_id for cs_id, _ in school_framework.subjects][int(s.strip()) - 1] for s in s_str.strip().split("/")]
                    else:
                        subjs = [[cs_id for cs_id, _ in school_framework.subjects][int(s.strip()) - 1] for s in s_name.strip().split("/")]
                        s_name = None
                    
                    subject = CombinedSubject(s_id, s_name, subjs, None, {})
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
                if "/" in t_name:
                    teacher = CombinedTeacher(t_id, [list(school_framework.teachers.values())[int(s.strip()) - 1] for s in t_name.split("/")])
                else:
                    if "■" in t_name:
                        names = [n.strip() if n.strip() else None for n in t_name.split("■")]
                    else:
                        names = [t_name, None, None, ""]
                    
                    teacher = Teacher(t_id, TeacherName(*names), {})
                
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
                
                subject_occurence = {}
                
                if subjects_occurence_string is not None:
                    for occ_string in subjects_occurence_string.strip().split():
                        occ_string = occ_string.strip()
                        
                        if occ_string:
                            gs_index, day_max, week_max = occ_string.split("/")
                            
                            subject_occurence[l_subjects[int(gs_index.strip()) - 1].id] = SubjectOccurrance(int(day_max.strip()), int(week_max.strip()))
                    
                lvl_id = ID(lvl_id) ; classes = {} ; (p_amt, b_p), weekdays = weekdays_data[cls_lvl_index]
                cls_lvl = ClassLevel(lvl_id, ClassLevelName(cls_lvl_name), classes, subject_occurence, weekdays, p_amt, b_p)
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
                    
                    cls_id = ID(cls_id.strip())
                    cls = classes[cls_id] = Class(cls_id, cls_name, cls_lvl, subject_mapping, school_framework)
                    all_classes.append(cls)
                    
                    school_framework.class_levels.add_class(lvl_id, cls)
        
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
        for _, cls_lvl in sch.class_levels:
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
    print(2)
    
    print("Started Generating")
    sch.generate()
    print("Started Clash detection")
    print(sch.detect_clashes())
    print("Ended")
    print()
    print(11)
    
    display_school(sch)




