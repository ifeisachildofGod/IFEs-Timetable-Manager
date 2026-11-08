import json
import math
import random
import importlib
from typing import Any, TypeVar
from dataclasses import dataclass
from matplotlib.cbook import flatten

from os import PathLike

from core.timing_and_timetable import *



class ID(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.parents: list[ID] = []
    
    def __add__(self, value):
        id = ID(value)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if self == other:
            id = self.parents[-1]
        else:
            self.parents.remove(other)
            
            for p in self.parents:
                if p.parents == self.parents:
                    id = p
                    break
            else:
                id = self
        
        return id
    
    def __rsub__(self, other):
        return self.__sub__(other)

class CLASS_ID(ID):
    def __init__(self, *args):
        super().__init__()
        
        self.class_level_id = None
    
    def __add__(self, value):
        if isinstance(value, CLASS_ID):
            assert self.class_level_id == value.class_level_id
        
        id = CLASS_ID(value, class_level_id=self.class_level_id)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id


@dataclass
class Name:
    first: str
    
    def full(self):
        return self.first
    
    def short(self):
        return self.full()
@dataclass
class Entry:
    id: ID
    
    name: Name
@dataclass
class AttendanceEntry[_T]:
    period: Period
    staff: _T
    is_check_in: bool = True


@dataclass
class SubjectOccurrance:
    day_max: int
    week_max: int
@dataclass
class SubjectName(Name):
    abbrev: str
    
    def short(self):
        return self.abbrev if self.abbrev else self.full()
@dataclass
class Subject(Entry):
    name: SubjectName
    
    teacher: Optional["Teacher"]
    classes: dict[ID, "Class"]
    
    def cls_name(self):
        return self.name.full() if len(self.name.full()) <= 15 else self.name.short()
    
    def get_periods(self, teacher: Optional[Teacher] = None):
        s_periods = []
        
        for cls in self.classes.values():
            if self.id in cls.subjects:
                for day, w_periods in cls.timetable.table.items():
                    for i, s in enumerate(w_periods):
                        if self.id != s.id:
                            continue
                        
                        if teacher is None or s.teacher.id == teacher.id:
                            s_periods.append((s.teacher, day, i + 1))
            elif (comb_subjects := [s for s in cls.subjects.values() if isinstance(s, CombinedSubject) and self.id in s.classes]):
                for comb_subj in comb_subjects:
                    for cls in comb_subj.classes[self.id].values():
                        for day, w_periods in cls.timetable.table.items():
                            for i, s in enumerate(w_periods):
                                if comb_subj.id != s.id:
                                    continue
                                s_teacher = next((s_s.teacher for s_s in s.subjects if self.id == s_s.id), None)
                                
                                if teacher is None or s_teacher is None or s_teacher.id == teacher.id:
                                    s_periods.append((s_teacher, day, i + 1))
        
        return s_periods
    
    def passCopy(self):
        return Subject(self.id, self.name, None, self.classes)
    
    def template(self, _):
        return f"{self.name.first}{f"■ {self.name.abbrev}" if self.name.abbrev else ""} - {self.id}"
    
    @staticmethod
    def from_template(template: str, school):
        names, id = template.split("-")
        
        if "â–" in names:
            first, abbrev = names.split("â–")
        else:
            first, abbrev = names, ""
        
        return Subject(ID(id.strip()), SubjectName(first.strip(), abbrev.strip()), None, {})
@dataclass
class CombinedSubjectName(SubjectName):
    first: Optional[str]
    abbrev: Optional[str]
    
    def full(self):
        return self.first or (self.abbrev or "")
    
    def short(self):
        return self.full()
@dataclass
class CombinedSubject(Entry):
    name: CombinedSubjectName
    
    subjects: list[Subject]
    classes: dict[ID, dict[CLASS_ID, Class]]
    default_occurance_data: tuple[int, int]
    
    def cls_name(self):
        long_name_list = [s.name.full() for s in self.subjects if s.teacher is not None]
        short_name_list = [s.name.short() for s in self.subjects if s.teacher is not None]
        
        long_no_name = "/".join(long_name_list) + ("/" if long_name_list == 1 else "")
        short_no_name = "/".join(short_name_list) + ("/" if short_name_list == 1 else "")
        
        return (self.name.full() if len(self.name.full()) <= 16 else self.name.short()) if self.name.first is not None or not short_name_list else (long_no_name if len(long_no_name) <= 16 else short_no_name)
    
    def remove_subject(self, subject: Subject):
        self.subjects.remove(subject)
        
        for cls_id, cls in self.classes[subject.id].items():
            if self.id in cls.subjects and next((False for s in self.subjects if cls_id in s.classes), True):
                cls.subjects.pop(self.id)
            
            if subject.id not in cls.subjects:
                cls.subjects[subject.id] = subject.passCopy()
            
            if subject.id not in cls.level.subjects_occurence:
                per_day, per_week = self.default_occurance_data
                cls.level.subjects_occurence[subject.id] = SubjectOccurrance(per_day, per_week)
            
            if self.id in cls.level.subjects_occurence and next((False for s_id, s_clses in self.classes.items() if s_id != subject.id and next((True for c in s_clses.values() if c.level.id == cls.level.id), False)), True):
                cls.level.subjects_occurence.pop(self.id)
        
        self.classes.pop(subject.id)
    
    def passCopy(self):
        return CombinedSubject(self.id, self.name, [s.passCopy() for s in self.subjects], self.classes, self.default_occurance_data)
    
    def template(self, school):
        subject_ids = list(school.subjects)
        
        return f"({self.name.first or ""} - {self.id}): {" ".join([str(subject_ids.index(s.id) + 1) for s in self.subjects])}"
    
    @staticmethod
    def from_template(template: str, school):
        subjects = list(school.subjects.values())
        
        name_and_id, sub_subject_templates = template.split(":")
        name, id = name_and_id.strip().removeprefix("(").removesuffix(")").split("-")
        
        sub_subjects = [subjects[int(s_index) - 1] for s_index in sub_subject_templates.split()]
        
        classes = {}
        for sub_subject in sub_subjects:
            classes[sub_subject.id] = {}
        
        if name.strip():
            first, abbrev = name.strip(), None
        else:
            first, abbrev = None, "/".join([s.cls_name() for s in sub_subjects])
        
        return CombinedSubject(ID(id.strip()), CombinedSubjectName(first, abbrev), sub_subjects, classes, (1, 1))
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


@dataclass
class StaffName(Name):
    second: Optional[str]
    third: Optional[str]
    abbrev: Optional[str]
    
    def full(self):
        return f"{self.first} {self.second} {self.third}" if None not in (self.second, self.third) else self.first
    
    def short(self):
        return self.abbrev if self.abbrev else self.first
@dataclass
class Staff(Entry):
    IUD: Optional[ID]
    
    name: StaffName
    img_path: Optional[PathLike]
    
    attendance: list[AttendanceEntry]
    
    def info_template(self):
        names = "■".join([self.name.first or "", self.name.second or "", self.name.third or "", self.name.abbrev or ""]) if self.name.second or self.name.third or self.name.abbrev else self.name.first or ""
        
        if self.IUD or self.img_path:
            return f"{names} - {self.id} - {self.IUD or ""} - {self.img_path or ""}"
        elif self.name.first or self.name.second or self.name.third or self.name.abbrev:
            return f"{names} - {self.id}"
        else:
            return str(self.id)
    
    @staticmethod
    def from_name_template(info_template: str):
        info_template_split = info_template.split("-")
        
        if len(info_template_split) == 4:
            names, id, iud, img_path = info_template_split
        elif len(info_template_split) == 2:
            names, id = info_template_split
            iud, img_path = "", ""
        elif len(info_template_split) == 1:
            id = info_template_split
            names, iud, img_path = "", "", ""
        
        iud = iud.strip()
        
        if "â–" in names:
            first, second, third, abbrev = names.split("â–")
            
            second = second.strip()
            third = third.strip()
            abbrev = abbrev.strip()
        else:
            first, second, third, abbrev = names, None, None, None
        
        return StaffName(first.strip(), second, third, abbrev), ID(id.strip()), ID(iud) if iud else None, img_path.strip() or None
    
    @staticmethod
    def info_template_from_template(template: str):
        name_ids_info, info_template = template.split(":")
        name, id, iud, img_path = Staff.from_name_template(name_ids_info.strip().removeprefix("(").removesuffix(")"))
        
        return name, id, iud, img_path, info_template
@dataclass
class Prefect(Staff):
    post_id: Optional[ID]
    cls: Optional["Class"]
    duties: dict[str, list[str]]
    
    def template(self, school):
        post_ids = list(school.posts)
        cls_lvl_ids = list(school.class_levels)
        
        return f"({self.info_template()}): {post_ids.index(self.post_id) + 1} {cls_lvl_ids.index(self.cls.level.id) + 1}/{list(self.cls.level.classes).index(self.cls.id) + 1} {self.duties}"
    
    @staticmethod
    def from_template(template: str, school):
        posts = list(school.posts)
        cls_levels = list(school.class_levels.values())
        
        name, id, iud, img_path, str_prefect_info = Staff.info_template_from_template(template)
        
        prefect_info = [""]
        in_brace = False
        
        for c in str_prefect_info:
            if c == "{":
                in_brace = True
            elif c == "}":
                in_brace = False
            
            if not in_brace and c == " ":
                if prefect_info[-1] != "":
                    prefect_info.append("")
                
                continue
            
            prefect_info[-1] += c
        
        post_index, cls_data, duties = prefect_info
        if cls_data:
            cls_level_index, cls_index = cls_data.split("/")
        else:
            cls_level_index, cls_index = None, None
        
        return Prefect(id, name, iud, img_path, [], posts[int(post_index) - 1] if post_index else None, list(cls_levels[int(cls_level_index) - 1].classes.values())[int(cls_index) - 1] if cls_level_index else None, json.loads(duties))
@dataclass
class Teacher(Staff):
    subjects: dict[ID, Subject]
    
    def template(self, school):
        subject_ids: list[ID] = list(school.subjects)
        
        return f"({self.info_template()}): {" ".join([str(subject_ids.index(s_id) + 1) for s_id in self.subjects])}"
    
    @staticmethod
    def from_template(template: str, school):
        subjects = list(school.subjects.values())
        
        name, id, iud, img_path, subjects_template = Staff.info_template_from_template(template)
        
        return Teacher(id, name, iud, img_path, [], {s.id: s for subject_index in subjects_template.split() if (s := subjects[int(subject_index) - 1])})

class Class:
    def __init__(
        self,
        id: CLASS_ID,
        name: str,
        level: "ClassLevel",
        subjects: dict[ID, "Subject | CombinedSubject"]
    ):
        self.SCHOOL = importlib.import_module("core").SCHOOL
        
        self.id = id
        self.name = name
        self.level = level
        self.subjects = subjects
        
        self.locked_subjects: dict[tuple[str, int], ID] = {}
        self.timetable = Timetable(self, self.SCHOOL.class_levels, self.SCHOOL.gen_data)
        
        for subject in self.subjects.values():
            subject.classes[self.id] = self
    
    def delete_subject(self, id: ID):
        self.subjects.pop(id)
        self.SCHOOL.subjects[id].classes.pop(self.id)
        
        for key, s_id in self.locked_subjects.copy().items():
            if s_id == id:
                self.locked_subjects.pop(key)
    
    def delete(self):
        self.level.classes.pop(self.id)
        
        for s_id, s in self.subjects.copy().items():
            classes = self.SCHOOL.subjects[s_id].classes
            if self.id in classes:
                classes.pop(self.id)
            
            self.subjects.pop(s_id)
    
    def template(self, school):
        subject_ids = list(school.subjects)
        teacher_ids = list(school.teachers)
        
        subj_str = ""
        
        for subject in self.subjects.values():
            if isinstance(subject, Subject):
                if subject.teacher:
                    _, subj_indexes = subject.teacher.template(school).split(":")
                    subj_indexes_split = subj_indexes.split()
                    
                    subject_index_template = f"{subject_ids.index(subject.id) + 1}"
                    
                    subj_str += f"{teacher_ids.index(subject.teacher.id) + 1}/{subj_indexes_split.index(subject_index_template) + 1} "
                else:
                    subj_str += f"{subject_ids.index(subject.id) + 1} "
            elif isinstance(subject, CombinedSubject):
                subj_str += f"({subject_ids.index(subject.id) + 1}"
                
                for i, sub_subj in enumerate(subject.subjects):
                    if self.id in subject.classes[sub_subj.id]:
                        subj_str += f"/{i + 1}"
                        
                        cls_sub_subj = next(s for s in self.subjects[subject.id].subjects if s.id == sub_subj.id)
                        
                        if cls_sub_subj.teacher is not None:
                            subj_str += f".{teacher_ids.index(cls_sub_subj.teacher.id) + 1}"
                
                subj_str += ") "
        
        return f"({self.name} - {self.id}): {subj_str.strip()}"
    
    @staticmethod
    def from_template(template: str, class_level: "ClassLevel", school):
        subjects = list(school.subjects.values())
        teachers = list(school.teachers.values())
        
        name_and_id, subjects_template = template.split(":")
        
        name, id = name_and_id.strip().removeprefix("(").removesuffix(")").split("-")
        
        id = CLASS_ID(id.strip())
        id.class_level_id = class_level.id
        
        cls = Class(id, name.strip(), class_level, {})
        
        for subject_template in subjects_template.split():
            if not (subject_template.startswith("(") and subject_template.endswith(")")) and "." not in subject_template and subject_template.count("/") <= 1:
                if subject_template.count("/") == 0:
                    subject = subjects[int(subject_template) - 1]
                    
                    subject.classes[cls.id] = cls
                    cls.subjects[subject.id] = subject.passCopy()
                elif subject_template.count("/") == 1:
                    str_teacher_index, teacher_subject_sub_index = subject_template.split("/")
                    
                    teacher = teachers[int(str_teacher_index) - 1]
                    subject = list(teacher.subjects.values())[int(teacher_subject_sub_index) - 1]
                    
                    subject.classes[cls.id] = cls
                    cls.subjects[subject.id] = subject.passCopy()
                    cls.subjects[subject.id].teacher = teacher
            else:
                c_subject_index, *sub_subjects_info = subject_template.removeprefix("(").removesuffix(")").split("/")
                
                c_subject = subjects[int(c_subject_index) - 1]
                
                for sub_subject_index_info in sub_subjects_info:
                    sub_subject_index_info = sub_subject_index_info.strip()
                    
                    if "." in sub_subject_index_info:
                        sub_subject_index, sub_subject_teacher_index = sub_subject_index_info.split(".")
                        
                        sub_subject = c_subject.subjects[int(sub_subject_index) - 1]
                        teacher = teachers[int(sub_subject_teacher_index) - 1]
                        
                        assert sub_subject.id in teacher.subjects
                        
                        c_subject.classes[sub_subject.id][cls.id] = cls
                        cls.subjects[c_subject.id] = c_subject.passCopy()
                        
                        cls_sub_subject = next(s for s in cls.subjects[c_subject.id].subjects if s.id == sub_subject.id)
                        cls_sub_subject.teacher= teacher
                    else:
                        sub_subject = c_subject.subjects[int(sub_subject_index_info) - 1]
                        
                        c_subject.classes[sub_subject.id][cls.id] = cls
                        cls.subjects[c_subject.id] = c_subject.passCopy()
        
        return cls
class ClassLevelName(str):
    def __init__(self, *args):
        super().__init__()
        
        self.first = self
    
    def full(self):
        return str(self)
    
    def short(self):
        return str(self)
@dataclass
class ClassLevel(Entry):
    name: ClassLevelName
    
    classes: dict[CLASS_ID, Class]
    subjects_occurence: dict[ID, SubjectOccurrance]
    
    weekdays: list[str]
    
    period_amount: int
    break_period: int
    
    def delete_subject(self, id: ID, teacher_id: Optional[ID] = None):
        for cls in self.classes.values():
            if id in cls.subjects:
                if cls.subjects[id].teacher is None or (cls.subjects[id].teacher.id == teacher_id if teacher_id is not None else True):
                    cls.delete_subject(id)
    
    def template(self, school):
        subject_ids = list(school.subjects)
        subject_occurence_str = " ".join([f"{subject_ids.index(s_id) + 1}/{occ.day_max}/{occ.week_max}" for s_id, occ in self.subjects_occurence.items()])
        
        return f"({self.name} - {self.id}): {self.period_amount} {self.break_period} | {" ".join(self.weekdays)} | {subject_occurence_str}\n{"\n".join([cls.template(school) for cls in self.classes.values()])}"
    
    @staticmethod
    def from_template(template: str, school):
        lvl_template, *classes_template = template.split("\n")
        
        subject_ids = list(school.subjects)
        
        name_and_id_template, info_template = lvl_template.split(":")
        name, id = name_and_id_template.strip().removeprefix("(").removesuffix(")").split("-")
        
        period_amt_and_break_period, day_of_the_weeks, subject_occurence_template = info_template.split("|")
        
        weekdays = [day.strip() for day in day_of_the_weeks.split()]
        period_amount, break_period = period_amt_and_break_period.split()
        subjects_occurence = {subject_ids[int(occ_split_template[0].strip()) - 1]: SubjectOccurrance(int(occ_split_template[1].strip()), int(occ_split_template[2].strip())) for occ_template in subject_occurence_template.split() if (occ_split_template := occ_template.split("/"))}
        
        cls_level = ClassLevel(ID(id.strip()), ClassLevelName(name.strip()), {}, subjects_occurence, weekdays, int(period_amount.strip()), int(break_period.strip()))
        
        for cls_template in classes_template:
            cls = Class.from_template(cls_template.strip(), cls_level, school)
            
            cls_level.classes[cls.id] = cls
        
        return cls_level
@dataclass
class GeneratingData:
    #            ClassID
    randomize: dict[ID, bool]
    #                              ClassID  SubjectID   Day    DayWeight  PeriodProclivity
    subject_positioning_weights: dict[ID, dict[ID, dict[str, tuple[float, int]]]]
    
    #                              ClassID    SubjectID    Day  Weight
    subject_clumping_weights: dict[CLASS_ID, dict[ID, dict[str, float]]]
    
    #                    LevelID             SubjectID    ClassIDs
    combined_subjects: dict[ID, list[tuple[list[ID], list[CLASS_ID]]]]


class Timetable:
    def __init__(self, cls: Class, class_levels: dict[ID, ClassLevel], gen_data: GeneratingData):
        self.cls = cls
        self.gen_data = gen_data
        self.class_levels = class_levels
        
        self.table: dict[str, list[Subject | CombinedSubject | BreakPeriod | FreePeriod]] = {d: [BreakPeriod() if i + 1 == cls.level.break_period else FreePeriod() for i in range(cls.level.period_amount)] for d in cls.level.weekdays}
        self.table_remains: list[Subject] = list(flatten([[s for _ in range(cls.level.subjects_occurence[s.id].week_max)] for s in cls.subjects.values() if s.id in cls.level.subjects_occurence and s.teacher is not None]))
        
        self._log_data: dict = {}
    
    def clear(self):
        for d, periods in self.table.items():
            for i, subject in enumerate(periods.copy()):
                if subject.id not in (FreePeriod.id, BreakPeriod.id, self.cls.locked_subjects.get((d, i + 1))):
                    periods[i] = FreePeriod()
                    
                    if subject in self.table_remains:
                        self.table_remains.insert(self.table_remains.index(subject), subject)
                    else:
                        n = subject.name.full()
                        index = sorted([s.name.full() for s in self.table_remains] + [n]).index(n)
                        
                        self.table_remains.insert(index, subject)
    
    def _sps(self, s_id: ID):
        period_scores: dict[str, list[int | float]] = {day: [] for day in self.cls.level.weekdays}
        
        for day, periods in self.table.items():
            for p_index, period in enumerate(periods):
                score = -math.inf
                if period.id == FreePeriod.id:
                    score = self._period_score(s_id, day, period, p_index)
                
                period_scores[day].append(score)
        
        return period_scores
    
    def _period_score(
            self,
            s_id: ID,
            day: str,
            period: Subject | CombinedSubject | FreePeriod | BreakPeriod,
            p_index: int,
            l_operate: int = False,
            r_operate: int = False,
            default_score = -50
        ):
        if s_id not in self._log_data:
            self._log_data[s_id] = []
        
        subject = self.cls.subjects[s_id]
        periods = self.table[day]
        
        if not (0 <= p_index <= len(periods) - 1):
            self._log_data[s_id].append(((day, p_index + 1), "Period out of table range"))
            return -math.inf
        
        assert subject.teacher if isinstance(subject, Subject) else next((True for s in subject.subjects if s.teacher is not None), False), f"{self.cls.level.name.full()} {self.cls.name} does not have a {subject.name.full()} teacher"
        
        if (
                period.id != FreePeriod.id or
                period.id == BreakPeriod.id or
                [p.id for p in periods].count(s_id) >= self.cls.level.subjects_occurence[subject.id].day_max or
                abs(p_index - next((p_i for p_i, p in enumerate(periods) if p.id == s_id), p_index + 1)) != 1
        ):
            if period.id == BreakPeriod.id:
                self._log_data[s_id].append(((day, p_index + 1), "Break period"))
            elif period.id != FreePeriod.id:
                self._log_data[s_id].append(((day, p_index + 1), f"Period is occupied by {period.name}"))
            elif [p.id for p in periods].count(s_id) >= self.cls.level.subjects_occurence[subject.id].day_max:
                self._log_data[s_id].append(((day, p_index + 1), f"Per day max reached: {[p.id for p in periods].count(s_id)}"))
            else:
                self._log_data[s_id].append(((day, p_index + 1), "Period island"))
            
            return -math.inf
        
        score = default_score
        
        for s_cls_lvl_id, s_cls_lvl in self.class_levels.items():
            for s_cls in s_cls_lvl.classes.values():
                s_subject = s_cls.timetable.table[day][p_index]
                
                if s_cls.id != self.cls.id and s_subject.id not in (FreePeriod.id, BreakPeriod.id):
                    s_teacher = s_subject.teacher if isinstance(s_subject, Subject) else [(s.teacher.id if s.teacher else None) for s in s_subject.subjects]
                    
                    assert s_teacher, f"{s_cls.level.name.full()} {s_cls.name} does not have a {s_subject.name.full()} teacher"
                    
                    is_combined = self.cls.level.id == s_cls_lvl_id and next(
                        (
                            True
                            for s_list, c_list in
                            self.gen_data.combined_subjects[self.cls.level.id]
                            if (s_id in s_list and s_subject.id in s_list) and (self.cls.id in c_list and s_cls.id in c_list)
                        ),
                        False
                    )
                    
                    is_clashing = None
                    
                    if isinstance(s_teacher, Teacher):
                        if isinstance(subject, Subject):
                            is_clashing = subject.teacher.id == s_teacher.id
                        elif isinstance(subject, CombinedSubject):
                            is_clashing = s_teacher.id in [s.teacher.id for s in subject.subjects if s.teacher is not None]
                    elif isinstance(s_teacher, list):
                        if isinstance(subject, Subject):
                            is_clashing = subject.teacher.id in s_teacher
                        elif isinstance(subject, CombinedSubject):
                            is_clashing = next((True for t_id in s_teacher if t_id in [s.teacher.id for s in subject.subjects if s.teacher is not None]), False)
                    
                    assert is_clashing is not None, "Internal Error: Clash check type mismatch"
                    
                    if is_clashing ^ is_combined:
                        self._log_data[s_id].append(((day, p_index + 1), f"Alignment Error: Subject is{"not " if isinstance(subject, Subject) else ""} combined and{"" if isinstance(subject, Subject) else "not "} clashing/aligned with {"another subject" if isinstance(s_teacher, Teacher) else "any subject"}"))
                        
                        return -math.inf
        else:
            clump_wieght = self.gen_data.subject_clumping_weights.get(self.cls.id, {}).get(s_id, {}).get(day, 1) or 0
            day_weight, period_proclivity = self.gen_data.subject_positioning_weights.get(self.cls.id, {}).get(s_id, {}).get(day, (None, None))
            
            if p_index or p_index != len(periods) - 1:
                orig = score
                
                if l_operate:
                    if p_index:
                        l_info = self._period_score(s_id, day, period, p_index - 1, l_operate + 1, False)
                        
                        if l_info == -math.inf:
                            return l_operate
                        
                        return l_info
                    else:
                        return l_operate
                elif r_operate:
                    if p_index != len(periods) - 1:
                        r_info = self._period_score(s_id, day, period, p_index + 1, False, r_operate + 1)
                        
                        if r_info == -math.inf:
                            return r_operate
                        
                        return r_info
                    else:
                        return r_operate
                else:
                    mul = self.cls.level.subjects_occurence[subject.id].day_max - [p.id for p in periods].count(s_id)
                    
                    l_depth = self._period_score(s_id, day, period, p_index - 1, 1, False)
                    r_depth = self._period_score(s_id, day, period, p_index + 1, False, 1)
                    
                    if l_depth == -math.inf:
                        l_depth = 0
                    if r_depth == -math.inf:
                        r_depth = 0
                    
                    if p_index:
                        is_prev_subj = periods[p_index - 1].id == s_id
                        
                        score += is_prev_subj * mul * 20
                        l_depth = l_depth or is_prev_subj * 20
                    if p_index != len(periods) - 1:
                        is_next_subj = periods[p_index + 1].id == s_id
                        
                        score += is_next_subj * mul * 20
                        r_depth = r_depth or is_next_subj * 20
                    
                    score += (((l_depth + r_depth) / self.cls.level.subjects_occurence[subject.id].day_max) * 2 - 1) * clump_wieght * 15
                
                if score == orig:
                    score -= 20
                
                score += sum((p_index - s_p_index) - (self.cls.level.subjects_occurence[s_period.id].day_max - periods.count(s_period)) for s_p_index, s_period in enumerate(periods) if not s_period.id in (FreePeriod.id, BreakPeriod.id)) # type: ignore
            
            if l_operate or r_operate:
                return l_operate + r_operate
            
            period_amt = len(self.table[day])
            
            # l_p = [p.id for p_i, p in enumerate(periods) if p.id not in (FreePeriod.id, BreakPeriod.id) and (p_i < break_period - 1 if p_index < break_period else p_i > break_period - 1)]
            
            # space_left = len(set(l_p)) - (
            #     (break_period - 1) // avg_day_freq + (((break_period - 1) % avg_day_freq) != 0)
            #     if p_index < break_period else
            #     (period_amt - break_period) // avg_day_freq + (((period_amt - break_period) % avg_day_freq) != 0)
            #     )
            
            # is_in_l_p = s_id in l_p
            
            # if is_in_l_p:
            #     score += clump_wieght * 10
            # else:
            #     score += space_left * 10
            
            score += (day_weight or 0) * 10
            score += ((1 - (abs(period_proclivity - (p_index + 1)) if period_proclivity else 0) / period_amt)) * 10
            
            score += (1 - (p_index / period_amt)) * 20
            
            consecs = []
            max_consec = 0
            match_indices = [pi for pi, p in enumerate(periods) if p.id == s_id]
            for j, i in enumerate(match_indices):
                if j:
                    if i == match_indices[j - 1] - 1:
                        consecs.append(i)
                        continue
                    
                    if len(consecs) <= max_consec:
                        consecs = []
                    else:
                        max_consec = len(consecs)
                else:
                    consecs.append(i)
            
            if consecs:
                score += (1 - (abs(consecs[0] - p_index) / period_amt)) * 2
                score += (1 - (abs(consecs[-1] - p_index) / period_amt)) * 20
        
        return score
    
    def generate(self):
        total_available_periods = sum(len(periods) for periods in self.table.values())
        total_subj_amt = sum(self.cls.level.subjects_occurence[s_id].week_max for s_id in self.cls.subjects if s_id in self.cls.level.subjects_occurence)
        
        assert total_available_periods > total_subj_amt, "Period slots are not enough for the amount of subjects"
        
        if self.cls.id not in self.gen_data.randomize:
            self.gen_data.randomize[self.cls.id] = False
        
        if self.gen_data.randomize[self.cls.id]:
            random.shuffle(self.table_remains)
        else:
            self.table_remains.sort(
                key=lambda s: self.cls.level.subjects_occurence[s.id].week_max * self.cls.level.subjects_occurence[s.id].day_max + (self.cls.id in self.gen_data.subject_positioning_weights and s.id in self.gen_data.subject_positioning_weights[self.cls.id]) * 3,
                reverse=True
            )
        
        for subject in self.table_remains.copy():
            scores = self._sps(subject.id)
            
            selected_period = None
            
            max_score = -math.inf
            for day, score in scores.items():
                if max(score) > max_score:
                    max_score = max(score)
                    
                    selected_period = day, score.index(max_score)
            
            if selected_period is None:
                raise TimetableGeneratorError(
                    f"Error Generating the {self.cls.level.name.full()} {self.cls.name} Timetable\n"
                    "\n"
                    "Try:\n"
                    "1) Changing some parameters or connections\n"
                    "2) Unlocking some subjects in this class or other classes\n"
                    "3) Generating more classes in the school simultanously\n"
                    "4) Removing some subjects currently in the timetable\n"
                    "5) Randomizing the generation of the timetable\n"
                    f"6) Performing a 'Generating New' action timetable\n"
                    "\n"
                    "You could also do all or a combination of the above suggestions to clear this error"
                )
            
            day, index = selected_period
            
            assert self.table[day][index].id == FreePeriod.id, f"Slot on {day} in Period {index + 1} is occupied"
            
            self.table[day][index] = self.cls.subjects[subject.id]
            self.table_remains.remove(subject)

    def scramble(self):
        timetable_points_days = list(flatten([[day for s in periods if s.id != BreakPeriod.id] for day, periods in self.table.items()]))
        timetable_points_indexes = list(flatten([[i for i, s in enumerate(periods) if s.id != BreakPeriod.id] for periods in self.table.values()]))
        
        timetable_points = list(zip(timetable_points_days, timetable_points_indexes))
        
        random.shuffle(self.table_remains)
        random.shuffle(timetable_points)
        
        for day, i in timetable_points:
            if not self.table_remains:
                break
            
            subj = self.table_remains.pop(0)
            self.table[day][i] = self.cls.subjects[subj.id]


