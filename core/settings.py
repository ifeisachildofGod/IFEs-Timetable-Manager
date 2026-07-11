import math
import random
from typing import Any
from core.timetable import *
from core.base import *
from dataclasses import dataclass
from matplotlib.cbook import flatten


@dataclass
class Entry:
    id: ID


@dataclass
class SubjectOccurrance:
    day_max: int
    week_max: int
@dataclass
class SubjectName:
    full_name: str
    abbrev: str
    
    def full(self):
        return self.full_name
    
    def short(self):
        return self.abbrev if self.abbrev else self.full_name
@dataclass
class Subject(Entry):
    name: SubjectName
    
    teacher: Optional["Teacher"]
    classes: dict[ID, "Class"]
    
    def passCopy(self):
        return Subject(self.id, self.name, None, self.classes)
@dataclass
class CombinedSubject(Entry):
    name: Optional[SubjectName]
    
    subjects: list[Subject]
    teacher: Optional["CombinedTeacher"]
    
    def passCopy(self):
        return CombinedSubject(self.id, self.subjects, None)
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
class TeacherName:
    start: str
    first: Optional[str]
    other: Optional[str]
    abbrev: str
    
    def full(self):
        return f"{self.start} {self.first} {self.other}" if None not in (self.first, self.other) else self.start
    
    def short(self):
        return self.abbrev if self.abbrev else self.start
@dataclass
class Teacher(Entry):
    name: TeacherName
    
    subjects: dict[ID, Subject]
@dataclass
class CombinedTeacher(Entry):
    teachers: list[Teacher]



class Class:
    def __init__(
        self,
        id: CLASS_ID,
        name: str,
        level: "ClassLevel",
        subjects: dict[ID, "Subject | CombinedSubject"],
        school: Any
    ):
        self.id = id
        self.name = name
        self.level = level
        self.subjects = subjects
        self.school = school
        
        self.locked_subjects = {}
        self.timetable = Timetable(self, self.school.class_levels, self.school.gen_data)
        
        for subject in self.subjects.values():
            subject.classes[self.id] = self
    
    def delete_subject(self, id: ID):
        self.subjects.pop(id)
        self.school.subjects[id].classes.pop(self.id)
        
        for v, s_id in self.locked_subjects.copy().items():
            if s_id == id:
                self.locked_subjects.pop(v)
    
    def delete(self):
        self.level.classes.pop(self.id)
        
        for s_id in self.subjects.copy():
            self.school.subjects[s_id].classes.pop(self.id)
            self.subjects.pop(s_id)
class ClassLevelName(str):
    def __init__(self, *args):
        super().__init__()
    
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

@dataclass
class GeneratingData:
    #            ClassID
    randomize: dict[ID, bool]
    #                              ClassID  SubjectID   Day    DayWeight  PeriodProclivity
    subject_positioning_weights: dict[ID, dict[ID, dict[str, tuple[float, int]]]]
    
    #                          ClassID  SubjectID    Day  Weight
    subject_clumping_weights: dict[ID, dict[ID, dict[str, float]]]
    
    #                       SubjectID  ClassIDs
    combined_subjects: dict[list[ID], list[ID]]


TimetableTableType = dict[str, list[Subject | CombinedSubject | BreakPeriod | FreePeriod]]
class Timetable:
    def __init__(self, cls: Class, class_levels: dict[ID, ClassLevel], gen_data: GeneratingData):
        self.cls = cls
        self.gen_data = gen_data
        self.class_levels = class_levels
        
        self.table: TimetableTableType = {d: [BreakPeriod() if i + 1 == cls.level.break_period else FreePeriod() for i in range(cls.level.period_amount)] for d in cls.level.weekdays}
        self.table_remains: list[Subject] = list(flatten([[s for _ in range(cls.level.subjects_occurence[s.id].week_max)] for s in cls.subjects.values() if s.teacher is not None]))
        
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
    
    def _sps(self, s_id: str):
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
            s_id: str,
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
        
        assert subject.teacher, f"{self.cls.level.name.full()} {self.cls.name} does not have a {subject.name.full()} teacher"
        
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
        
        for s_cls_lvl in self.class_levels.values():
            for s_cls in s_cls_lvl.classes.values():
                s_subject = s_cls.timetable.table[day][p_index]
                
                if s_cls.id != self.cls.id and s_subject.id not in (FreePeriod.id, BreakPeriod.id):
                    s_teacher = s_subject.teacher
                    
                    assert s_teacher
                    
                    combined = next(
                        (
                            True
                            for s_list, c_list in
                            self.gen_data.combined_subjects.items()
                            if (s_id in s_list and s_subject.id in s_list) and (self.cls.id in c_list and s_cls.id in c_list)
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
                        self._log_data[s_id].append(((day, p_index + 1), f"Alignment Error: subject is{"not " if isinstance(subject.teacher, Teacher) else ""} combined and{"" if isinstance(subject.teacher, Teacher) else "not "} clashing/aligned with {"another subject" if isinstance(s_teacher, Teacher) else "any subject"}"))
                        
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
    
    def generate(self):
        total_available_periods = sum(len(periods) for periods in self.table.values())
        total_subj_amt = sum(self.cls.level.subjects_occurence[s_id].week_max for s_id in self.cls.subjects)
        
        assert total_available_periods > total_subj_amt, "Period slots are not enough for the amount of subjects"
        
        if self.cls.id not in self.gen_data.randomize:
            self.gen_data.randomize[self.cls.id] = False
        
        if self.gen_data.randomize[self.cls.id]:
            random.shuffle(self.table_remains)
        
        for subject in self.table_remains.copy():
            scores = self._sps(subject.id)
            
            selected_period = None
            
            max_score = -math.inf
            for day, score in scores.items():
                if max(score) > max_score:
                    max_score = max(score)
                    
                    selected_period = day, score.index(max_score)
            
            if not selected_period:
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


