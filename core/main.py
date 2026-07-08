

import json
import math
import random
from dataclasses import dataclass
from matplotlib.cbook import flatten
from typing import Generator, Optional

from core.base import *
from core.settings import *
from core.timetable import *


class Global:
    def __init__(self, school: "SchoolFrameWork | None" = None):
        super().__init__()
        
        self.data = {}
        self.school = school
    
    def set_school(self, school: "SchoolFrameWork"):
        self.school = school
    
    def get(self):
        return self.data
    
    def add(self, entry):
        self.data[entry.id] = entry
    
    def remove(self, id: ID):
        self.data.pop(id)
    
    def set(self, value):
        self.data.clear()
        self.data.update(value.data)
    
    def __len__(self):
        return self.data.__len__()
    
    def __iter__(self):
        return self.data.items().__iter__()
    
    def __getitem__(self, key: ID):
        return self.data.__getitem__(key)


class GlobalSubjects(Global):
    def __iter__(self) -> Generator[tuple[ID, Subject | CombinedSubject], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> Subject | CombinedSubject:
        return super().__getitem__(key)
    
    def add(self, entry: Subject | CombinedSubject):
        return super().add(entry)

class GlobalTeachers(Global):
    def __iter__(self) -> Generator[tuple[ID, Teacher | CombinedTeacher], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> Teacher | CombinedTeacher:
        return super().__getitem__(key)
    
    def add(self, entry: Teacher | CombinedTeacher):
        return super().add(entry)

class GlobalClassLevels(Global):
    def __iter__(self) -> Generator[tuple[ID, ClassLevel], None, None]:
        return super().__iter__()
    
    def __getitem__(self, key) -> ClassLevel:
        return super().__getitem__(key)
    
    def add(self, entry: ClassLevel):
        self.school.settings.TEACHER_rsma_mapping[entry.id] = None
        self.school.settings.TIMETABLE_time_settings[entry.id] = {"Everyday": SCHOOL.settings.DEFAULT_timetable_time_setting.copy()}
        self.school.settings.EXPORT_selected_classes[entry.id] = []
        
        return super().add(entry)
    
    def add_class(self, id: ID, cls: Class):
        self.data[id].classes[cls.id] = cls
        
        self.school.fresh_timetable(cls)
    
    def remove_class(self, id: ID, cls_id: ID):
        if cls_id in SCHOOL.settings.EXPORT_selected_classes[id]:
            SCHOOL.settings.EXPORT_selected_classes[id].remove(cls_id)
        
        self.school.timetables_data.pop(cls_id)
        
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


@dataclass
class SchoolFrameWork:
    subjects: Optional[GlobalSubjects] = None
    teachers: Optional[GlobalTeachers] = None
    class_levels: Optional[GlobalClassLevels] = None
    
    settings: Optional[Settings] = None
    
    timetables_data: Optional[dict[ID, tuple[Optional[TimetableFW], list[Subject]]]] = None
    gen_data: Optional[GeneratingData] = None
    
    _log_data: Optional[dict[str, dict[str, list[str]]]] = None
    
    def _init(self):
        if self.subjects is None:
            self.subjects = GlobalSubjects(self)
        if self.teachers is None:
            self.teachers = GlobalTeachers(self)
        if self.class_levels is None:
            self.class_levels = GlobalClassLevels(self)
        if self.timetables_data is None:
            self.timetables_data = {}
        
        if self._log_data is None:
            self._log_data = {}
        if self.gen_data is None:
            self.gen_data = GeneratingData({}, {}, {}, {})
        if self.settings is None:
            self.settings = Settings(
                "dark-blue",
                10, 7, 3, (2, 3), TimetableTime(Time(8, 10), 35, 35),
                {},
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], {},
                TimetableExportTheme(
                    None, None, None,
                    "white", "white", "black", "black", "black",
                    1, 1,
                    0, "PNG"
                ), {}
            )
    
    def set(self, school: "SchoolFrameWork"):
        self.subjects.set(school.subjects)
        self.teachers.set(school.teachers)
        self.class_levels.set(school.class_levels)
        
        self.settings.__dict__ = school.settings.__dict__
        
        self.timetables_data.clear()
        self.timetables_data.update(school.timetables_data)
        
        self.gen_data.__dict__ = school.gen_data.__dict__
    
    def fresh_timetable(self, cls: Class):
        if cls.id not in self.timetables_data:
            self.timetables_data[cls.id] = (
                {d: [BreakPeriod() if i + 1 == cls.level.break_period else FreePeriod() for i in range(cls.level.period_amount)] for d in cls.level.weekdays},
                list(flatten([[s for _ in range(cls.level.subjects_occurence[s.id].week_max)] for s in cls.subjects.values() if s.teacher is not None]))
            )
        else:
            timetable, timetable_remains = self.timetables_data[cls.id]
            break_periods = {d: next(i for i, s in enumerate(periods) if s.id == BreakPeriod.id) for d, periods in timetable.items()}
            
            for d in cls.level.weekdays:
                cls.level.period_amount
                timetable[d].clear()
                timetable[d].extend([BreakPeriod() if i == break_periods[d] else FreePeriod() for i in range(cls.level.period_amount)])
            
            timetable_remains.clear()
            timetable_remains.extend(list(flatten([[s for _ in range(cls.level.subjects_occurence[s.id].week_max)] for s in cls.subjects.values() if s.teacher is not None])))
        
        for (day, period), s_id in cls.locked_subjects.items():
            subject = cls.subjects[s_id]
            timetable, timetable_remains = self.timetables_data[cls.id]
            
            timetable[day][period - 1] = subject
            timetable_remains.remove(subject)
    
    def generate_timetables(self, cls_ids: list[tuple[ID, ID]] | None = None):
        if not cls_ids:
            cls_ids = []
            
            for cl_id, cls in self.class_levels:
                for c_id in cls.classes:
                    cls_ids.append((cl_id, c_id))
        
        for cls_lvl_id, cls_id in cls_ids:
            cls_lvl = self.class_levels[cls_lvl_id]
            cls = cls_lvl.classes[cls_id]
            
            timetable, timetable_remains = self.timetables_data[cls.id]
            
            assert timetable is not None, "Timetable is None"
            assert timetable_remains is not None, "Timetable Remains is None"
            
            total_available_periods = sum(len(periods) for periods in timetable.values())
            total_subj_amt = sum(cls.level.subjects_occurence[s_id].week_max for s_id in cls.subjects)
            
            assert total_available_periods > total_subj_amt, "Period slots are not enough for the amount of subjects"
            
            if cls_id not in self.gen_data.randomize:
                self.gen_data.randomize[cls_id] = False
            
            if self.gen_data.randomize[cls_id]:
                random.shuffle(timetable_remains)
            
            for subject in timetable_remains.copy():
                scores = self._sps(subject.id, cls)
                
                selected_period = None
                
                max_score = -math.inf
                for day, score in scores.items():
                    if max(score) > max_score:
                        max_score = max(score)
                        
                        selected_period = day, score.index(max_score)
                
                if not selected_period:
                    # print(cls.subjects[subject.id].name)
                    # print(json.dumps(self._log_data[cls_id][subject.id], indent=2))
                    
                    raise TimetableGeneratorError(
                        f"Error Generating the {cls_lvl.name.full()} {cls.name} Timetable\n"
                        "\n"
                        "Try:\n"
                        "1) Changing some parameters or connections\n"
                        "2) Unlocking some subjects in this class or other classes\n"
                        "3) Generating more classes in the school simultanously\n"
                        "4) Removing some subjects currently in the timetable\n"
                        "5) Randomizing the generation of the timetable\n"
                        f"6) Performing a 'Generating New' action {"for this timetable" if len(cls_ids) == 1 else "for the timetables"}\n"
                        "\n"
                        "You could also do all or a combination of the above suggestions to clear this error"
                    )
                
                day, index = selected_period
                
                assert timetable[day][index].id == FreePeriod.id, f"Slot on {day} in Period {index + 1} is occupied"
                
                timetable[day][index] = cls.subjects[subject.id]
                timetable_remains.remove(subject)
    
    def detect_clashes(self):
        """
        Returns {
            ((Day, PeriodIndex), SubjectID + TeacherID): [Class, ...]
        }
        """
        
        clashes: dict[tuple[tuple[str, int], tuple[ID, ID]], list[Class]] = {}
        
        days_uid_tracker: dict[str, list[tuple[tuple[ID, ID], Class]]] = {}
        
        for c_id, (timetable, _) in self.timetables_data.items():
            for day, periods in timetable.items():
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
        
        for c_id, (timetable, _) in self.timetables_data.items():
            for day, periods in timetable.items():
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
    
    def _sps(self, s_id: str, cls: Class):
        period_scores: dict[str, list[int | float]] = {day: [] for day in cls.level.weekdays}
        
        timetable = self.timetables_data[cls.id][0]
        
        assert timetable
        
        for day, periods in timetable.items():
            for p_index, period in enumerate(periods):
                score = -math.inf
                if period.id == FreePeriod.id:
                    score = self._period_score(s_id, cls, day, period, p_index)
                
                period_scores[day].append(score)
        
        return period_scores
    
    def _period_score(
            self,
            s_id: str,
            cls: Class,
            day: str,
            period: Subject | CombinedSubject | FreePeriod | BreakPeriod,
            p_index: int,
            l_operate: int = False,
            r_operate: int = False,
            default_score = -50
        ):
        if cls.id not in self._log_data:
            self._log_data[cls.id] = {}
        if s_id not in self._log_data[cls.id]:
            self._log_data[cls.id][s_id] = []
        
        subject = cls.subjects[s_id]
        timetable, _ = self.timetables_data[cls.id]
        
        periods = timetable[day]
        
        if not (0 <= p_index <= len(periods) - 1):
            self._log_data[cls.id][s_id].append(((day, p_index + 1), "Period out of timetable range"))
            return -math.inf
        
        assert subject.teacher, f"{cls.level.name.full()} {cls.name} does not have a {subject.name.full()} teacher"
        
        if (
                period.id != FreePeriod.id or
                period.id == BreakPeriod.id or
                [p.id for p in periods].count(s_id) >= cls.level.subjects_occurence[subject.id].day_max or
                abs(p_index - next((p_i for p_i, p in enumerate(periods) if p.id == s_id), p_index + 1)) != 1
                ):
            if period.id == BreakPeriod.id:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), "Break period"))
            elif period.id != FreePeriod.id:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Period is occupied by {period.name}"))
            elif [p.id for p in periods].count(s_id) >= cls.level.subjects_occurence[subject.id].day_max:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Per day max reached: {[p.id for p in periods].count(s_id)}"))
            else:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), "Period island"))
            
            return -math.inf
        
        score = default_score
        
        for _, s_cls_lvl in self.class_levels:
            for s_cls in s_cls_lvl.classes.values():
                timetable, _ = self.timetables_data[s_cls.id]
                
                if timetable is not None:
                    s_subject = timetable[day][p_index]
                    
                    if s_cls.id != cls.id and s_subject.id not in (FreePeriod.id, BreakPeriod.id):
                        s_teacher = s_subject.teacher
                        
                        assert s_teacher
                        
                        combined = next(
                            (
                                True
                                for s_list, c_list in
                                self.gen_data.combined_subjects.items()
                                if (s_id in s_list and s_subject.id in s_list) and (cls.id in c_list and s_cls.id in c_list)
                            ),
                            False
                            )
                        
                        is_clashing = None
                        
                        if isinstance(s_teacher, Teacher):
                            if isinstance(subject.teacher, Teacher):
                                is_clashing = subject.teacher.id == s_teacher.id
                            elif isinstance(subject.teacher, CombinedTeacher):
                                is_clashing = s_teacher.id in [t_id for t_id, _ in subject.teacher.teachers]
                        elif isinstance(s_teacher, CombinedTeacher):
                            if isinstance(subject.teacher, Teacher):
                                is_clashing = subject.teacher.id in [t_id for t_id, _ in s_teacher.teachers]
                            elif isinstance(subject.teacher, CombinedTeacher):
                                is_clashing = next((True for t in s_teacher.teachers if t.id in [s_t.id for s_t in subject.teacher.teachers]), False)
                        
                        if is_clashing is None:
                            raise Exception()
                        
                        if is_clashing and not combined:
                            self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Alignment Error: subject is{"not " if isinstance(subject.teacher, Teacher) else ""} combined and{"" if isinstance(subject.teacher, Teacher) else "not "} clashing/aligned with {"another subject" if isinstance(s_teacher, Teacher) else "any subject"}"))
                            
                            return -math.inf
        else:
            clump_wieght = self.gen_data.subject_clumping_weights.get(cls.id, {}).get(s_id, {}).get(day, 1) or 0
            day_weight, period_proclivity = self.gen_data.subject_positioning_weights.get(cls.id, {}).get(s_id, {}).get(day, (None, None))
            
            if p_index or p_index != len(periods) - 1:
                orig = score
                
                if l_operate:
                    if p_index:
                        l_info = self._period_score(s_id, cls, day, period, p_index - 1, l_operate + 1, False)
                        
                        if l_info == -math.inf:
                            return l_operate
                        
                        return l_info
                    else:
                        return l_operate
                elif r_operate:
                    if p_index != len(periods) - 1:
                        r_info = self._period_score(s_id, cls, day, period, p_index + 1, False, r_operate + 1)
                        
                        if r_info == -math.inf:
                            return r_operate
                        
                        return r_info
                    else:
                        return r_operate
                else:
                    mul = cls.level.subjects_occurence[subject.id].day_max - [p.id for p in periods].count(s_id)
                    
                    l_depth = self._period_score(s_id, cls, day, period, p_index - 1, 1, False)
                    r_depth = self._period_score(s_id, cls, day, period, p_index + 1, False, 1)
                    
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
                    
                    score += (((l_depth + r_depth) / cls.level.subjects_occurence[subject.id].day_max) * 2 - 1) * clump_wieght * 15
                
                if score == orig:
                    score -= 20
                
                score += sum((p_index - s_p_index) - (cls.level.subjects_occurence[s_period.id].day_max - periods.count(s_period)) for s_p_index, s_period in enumerate(periods) if not s_period.id in (FreePeriod.id, BreakPeriod.id)) # type: ignore
            
            if l_operate or r_operate:
                return l_operate + r_operate
            
            period_amt = len(timetable[day])
            
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
            score += ((1 - (abs(period_proclivity - p_index) if period_proclivity else 0) / period_amt)) * 10
            
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
    
    @staticmethod
    def id_name_from_text(text: str):
        text = text.strip().removeprefix("(").removesuffix(")")
        
        sep_index = text.rfind("-")
        
        return text[:sep_index].strip(), text[sep_index + 1:].strip()
    
    @staticmethod
    def from_template(text: str):
        text = "\n".join(["".join(list(line)[:line.find("#")] if "#" in line else list(line)) for line in text.splitlines()])
        
        subjects = GlobalSubjects()
        teachers = GlobalTeachers()
        class_levels = GlobalClassLevels()
        
        school_framework = SchoolFrameWork(subjects, teachers, class_levels) ; school_framework._init()
        school_framework.subjects.set_school(school_framework) ; school_framework.teachers.set_school(school_framework) ; school_framework.class_levels.set_school(school_framework)
        
        subjects_string, teachers_string, classes_string, dotw_string = text.split("---") #, timetable_string = text.split("---")
        
        subjects_string = subjects_string.strip()
        teachers_string = teachers_string.strip()
        classes_string = classes_string.strip()
        # timetable_string = timetable_string.strip()
        dotw_string = dotw_string.strip()
        
        for s_index, s_info in enumerate(subjects_string.splitlines()):
            if s_info.strip():
                s_name, s_id = SchoolFrameWork.id_name_from_text(s_info)
                
                s_id = ID(s_id)
                if "/" in s_name:
                    if s_name.count("(") == 1 and s_name.count(")") == 1:
                        n, s_str = SchoolFrameWork.id_name_from_text(s_name)
                        
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
        
        l_subjects = [s for _, s in school_framework.subjects]
        
        teacher_subject_indices = {}
        for t_string in teachers_string.splitlines():
            t_string = t_string.strip()
            
            if t_string:
                if ":" in t_string:
                    t_info, value =  t_string.split(":")
                else:
                    t_info = t_string
                    value = None
                
                t_name, t_id = SchoolFrameWork.id_name_from_text(t_info)
                
                t_id = ID(t_id)
                t_name = t_name.strip()
                if "/" in t_name:
                    teacher = CombinedTeacher(t_id, [[t for _, t in school_framework.teachers][int(s.strip()) - 1] for s in t_name.split("/")])
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
                        school_framework.teachers[t_id].subjects[l_subjects[s_index].id] = l_subjects[s_index]
        
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
        l_teachers = [t for _, t in school_framework.teachers]
        if classes_string:
            for cls_lvl_index, cls_lvl_string in enumerate(classes_string.split("_")):
                cls_lvl_data = cls_lvl_string.splitlines()
                cls_lvl_info, cls_data = cls_lvl_data[0], cls_lvl_data[1:]
                
                if ":" in cls_lvl_info:
                    cls_lvl_id_data, subjects_occurence_string = cls_lvl_info.split(":")
                else:
                    cls_lvl_id_data = cls_lvl_info.strip()
                    subjects_occurence_string = None
                
                cls_lvl_name, lvl_id = SchoolFrameWork.id_name_from_text(cls_lvl_id_data)
                
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
                    
                    cls_name, cls_id = SchoolFrameWork.id_name_from_text(cls_info)
                    
                    subject_mapping = {}
                    
                    cls_id = ID(cls_id.strip())
                    cls = classes[cls_id] = Class(cls_id, cls_name, cls_lvl, subject_mapping, {}, school_framework)
                    all_classes.append(cls)
                    
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
                            if isinstance(o_subject, Subject):
                                o_subject.classes[cls_id] = classes[cls_id]
                            
                            subject = o_subject.passCopy()
                            subject.teacher = teacher
                            
                            subject_mapping[subject.id] = subject
                        
                    school_framework.class_levels.add_class(lvl_id, cls)
            
        # l_class_levels = [cl_id for cl_id, _ in school_framework.class_levels]
        # if timetable_string:
        #     for cls_i, ttbl_string in enumerate(timetable_string.split("_")):
        #         cls = all_classes[cls_i]
        #         l_weekdays = list(weekdays_data[l_class_levels.index(cls.level.id)])
                
        #         ttbl_string = ttbl_string.strip()
                
        #         if ttbl_string:
        #             timetable, _ = school_framework.timetables_data[cls.id] = {}, []
                    
        #             for s_ttbl_i, s_ttbl_string in enumerate(ttbl_string.strip().split(";")):
        #                 s_ttbl_string = s_ttbl_string.strip()
                        
        #                 if s_ttbl_string:
        #                     timetable[l_weekdays[s_ttbl_i]] = [
        #                         (
        #                             FreePeriod()
        #                             if int(s.strip()) == 0 else
        #                             (
        #                                 BreakPeriod()
        #                                 if int(s.strip()) == -1 else
        #                                 list(cls.subjects.values())[int(s.strip()) - 1]
        #                             )
        #                         )
        #                         for s in
        #                         s_ttbl_string.split()
        #                     ]
        
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


SCHOOL = SchoolFrameWork()
SCHOOL._init()


if __name__ == "__main__":
    def display_school(sch: SchoolFrameWork):
        for _, cls_lvl in sch.class_levels:
            for cls in cls_lvl.classes.values():
                timetable, timetable_remains = sch.timetables_data[cls.id]
                
                assert timetable
                
                print(cls_lvl.name.full(), cls.name)
                for day, periods in timetable.items():
                    print(day, end=": ")
                    print(*[(p.name.full() if not isinstance(p, CombinedSubject) else "/".join([s.name for s in p.subjects])) for p in periods], sep=", ")
                
                if timetable_remains:
                    print()
                    print("Remainders:", ", ".join([s.name.full() for s in timetable_remains]))
                    print()
                print()
    
    with open(r"test.save\test.frmwk") as file:
        data = file.read()
    
    sch = SchoolFrameWork.from_template(data)
    print(2)
    
    print("Started Generating")
    sch.generate_timetables()
    print("Started Clash detection")
    print(sch.detect_clashes())
    print("Ended")
    print()
    print(11)
    
    display_school(sch)




