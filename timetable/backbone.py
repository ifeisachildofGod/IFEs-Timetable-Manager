
import json
import math
import random
# from temp_core import *
from core import *
from pathlib import Path
from dataclasses import dataclass
from matplotlib.cbook import flatten

class BGTimetableError(Exception):
    pass


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
class FreePeriodFW:
    id: str = "FreePeriodID"
    
    name: SubjectName = "Free"
    teacher: "Teacher | None" = None
    
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        
        self.name = SubjectName("Free", "Free")

@dataclass
class BreakPeriodFW:
    id: str = "BreakPeriodID"
    
    name: str = "Break"
    teacher: "Teacher | None" = None
    
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        
        self.name = SubjectName("Break", "Break")


# Objects
TimetableFW = dict[str, list[Subject | CombinedSubject | BreakPeriodFW | FreePeriodFW]]

@dataclass
class SchoolFrameWork:
    subjects: dict[ID, Subject | CombinedSubject]
    teachers: dict[ID, Teacher | CombinedTeacher]
    class_lvls: dict[ID, ClassLevel]
    timetables_data: dict[ID, tuple[Optional[TimetableFW], list[Subject]]]
    
    gen_data: GeneratingData
    _log_data: dict[str, dict[str, list[str]]] | None = None
    
    def generate_timetable(self, cls_ids: list[tuple[ID, ID]] | None = None):
        if not self._log_data:
            self._log_data = {}
        
        if not cls_ids:
            cls_ids = []
            
            for cl_id, cls in self.class_lvls.items():
                for c_id in cls.classes:
                    cls_ids.append((cl_id, c_id))
        
        for cls_lvl_id, cls_id in cls_ids:
            cls = self.class_lvls[cls_lvl_id].classes[cls_id]
            
            if self.timetables_data[cls.id][0] is None:
                self.timetables_data[cls.id][0] = {d: [FreePeriodFW() if i + 1 != b else BreakPeriodFW() for i in range(p)] for d, (p, b) in cls.level.weekdays.items()}
            
            timetable, timetable_remains = self.timetables_data[cls.id]
            
            week_amt_data = {s_id: cls.level.subjects_occurence[s_id].week_max for s_id in cls.subjects}
            
            total_available_periods = sum(amt for amt, _ in cls.level.weekdays.values())
            total_subj_amt = sum(list(week_amt_data.values()))
            
            assert total_available_periods > total_subj_amt, "Period slots are not enough for the amount of subjects"
            
            for s_list in timetable.values():
                for s in s_list:
                    if s.id not in (FreePeriodFW.id, BreakPeriodFW.id):
                        week_amt_data[s.id] -= 1
            
            completed_ones = []
            
            while True:
                if len(completed_ones) == len(cls.subjects):
                    break
                
                cls_subject_ids = list(cls.subjects)
                
                if self.gen_data.randomize:
                    random.shuffle(cls_subject_ids) # type: ignore
                
                for s_id in cls_subject_ids:
                    for _ in range(cls.level.subjects_occurence[s_id].day_max):
                        if s_id in completed_ones:
                            continue
                        
                        scores = self._sps(s_id, cls)
                        
                        selected_period = None
                        
                        max_score = -math.inf
                        for day, score in scores.items():
                            if max(score) > max_score:
                                max_score = max(score)
                                
                                selected_period = day, score.index(max_score)
                        if not selected_period:
                            print(cls.subjects[s_id].name)
                            print(json.dumps(self._log_data[cls_id][s_id], indent=2))
                            
                            raise BGTimetableError("No valid periods available")
                        
                        day, index = selected_period
                        
                        assert timetable[day][index].id == FreePeriodFW.id
                        
                        timetable[day][index] = cls.subjects[s_id]
                        week_amt_data[s_id] -= 1
                        
                        if week_amt_data[s_id] <= 0:
                            completed_ones.append(s_id)
            
            timetable_remains.clear()
            timetable_remains.extend(list(flatten([[self.subjects[s_id] for _ in range(amt)] for s_id, amt in week_amt_data.items()])))
    
    def detect_clashes(self):
        clashes = {}
        
        return clashes
    
    def _sps(self, s_id: str, cls: Class):
        period_scores: dict[str, list[int | float]] = {day: [] for day in cls.level.weekdays}
        
        timetable = self.timetables_data[cls.id][0]
        
        assert timetable
        
        for day, periods in timetable.items():
            for p_index, period in enumerate(periods):
                period_scores[day].append(self._period_score(s_id, cls, day, period, p_index))
        
        return period_scores
    
    def _period_score(
            self,
            s_id: str,
            cls: Class,
            day: str,
            period: Subject | CombinedSubject | FreePeriodFW | BreakPeriodFW,
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
        timetable = self.timetables_data[cls.id][0]
        
        assert timetable
        
        periods = timetable[day]
        
        if not (0 <= p_index <= len(periods) - 1):
            self._log_data[cls.id][s_id].append(((day, p_index + 1), "Period out of timetable range"))
            return -math.inf
        
        assert subject.teacher
        
        _l_d_freq = [cls.level.subjects_occurence[s.id].day_max for s in cls.subjects.values()] # type: ignore
        avg_day_freq = sum(_l_d_freq) // len(_l_d_freq)
        
        assert isinstance(avg_day_freq, int)
        
        if (
                period.id != FreePeriodFW.id or
                period.id == BreakPeriodFW.id or
                [p.id for p in periods].count(s_id) >= cls.level.subjects_occurence[subject.id].day_max or
                abs(p_index - next((p_i for p_i, p in enumerate(periods) if p.id == s_id), p_index + 1)) != 1
                ):
            if period.id == BreakPeriodFW.id:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), "Break period"))
            elif period.id != FreePeriodFW.id:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Period is occupied by {period.name}"))
            elif [p.id for p in periods].count(s_id) >= cls.level.subjects_occurence[subject.id].day_max:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Per day max reached: {[p.id for p in periods].count(s_id)}"))
            else:
                self._log_data[cls.id][s_id].append(((day, p_index + 1), "Period island"))
            
            return -math.inf
        
        score = default_score
        
        for s_cls_lvl in self.class_lvls.values():
            for s_cls in s_cls_lvl.classes.values():
                timetable, _ = self.timetables_data[s_cls.id]
                
                if timetable is not None:
                    s_subject = timetable[day][p_index]
                    
                    if s_cls.id != cls.id and s_subject.id not in (FreePeriodFW.id, BreakPeriodFW.id):
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
                                is_clashing = s_teacher.id in [t.id for t in subject.teacher.teachers]
                        elif isinstance(s_teacher, CombinedTeacher):
                            if isinstance(subject.teacher, Teacher):
                                is_clashing = subject.teacher.id in [t.id for t in s_teacher.teachers]
                            elif isinstance(subject.teacher, CombinedTeacher):
                                is_clashing = next((True for t in s_teacher.teachers if t.id in [s_t.id for s_t in subject.teacher.teachers]), False)
                        
                        if is_clashing is None:
                            raise Exception()
                        
                        if is_clashing and not combined:
                            self._log_data[cls.id][s_id].append(((day, p_index + 1), f"Alignment Error: subject is{"not " if isinstance(subject.teacher, Teacher) else ""} combined and{"" if isinstance(subject.teacher, Teacher) else "not "} clashing/aligned with {"another subject" if isinstance(s_teacher, Teacher) else "any subject"}"))
                            
                            return -math.inf
        else:
            clump_wieght = (self.gen_data.subject_clumping_weights[cls.id][s_id][day] or 0) if cls.id in self.gen_data.subject_clumping_weights else 1
            day_weight, period_proclivity = (self.gen_data.subject_positioning_weights[cls.id][s_id][day] if cls.id in self.gen_data.subject_positioning_weights else (None, None))
            
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
                
                score += sum((p_index - s_p_index) - (cls.level.subjects_occurence[s_period.id].day_max - periods.count(s_period)) for s_p_index, s_period in enumerate(periods) if not s_period.id in (FreePeriodFW.id, BreakPeriodFW.id)) # type: ignore
            
            if l_operate or r_operate:
                return l_operate + r_operate
            
            period_amt, break_period = cls.level.weekdays[day]
            
            # l_p = [p.id for p_i, p in enumerate(periods) if p.id not in (FreePeriodFW.id, BreakPeriodFW.id) and (p_i < break_period - 1 if p_index < break_period else p_i > break_period - 1)]
            
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
        
        return text[:sep_index], text[sep_index + 1:]
    
    @staticmethod
    def school_from_text(text: str, id_mappings: dict[str, list[str]] | None = None):
        id_mappings = id_mappings or {"subjects": None, "teachers": None, "classes": None}
        
        text = "\n".join(["".join(list(line)[:line.find("#")] if "#" in line else list(line)) for line in text.splitlines()])
            
        subjects_string, teachers_string, classes_string, timetable_string, dotw_string = text.split("---")
        
        subjects_string = subjects_string.strip()
        teachers_string = teachers_string.strip()
        classes_string = classes_string.strip()
        timetable_string = timetable_string.strip()
        dotw_string = dotw_string.strip()

        subjects = {}
        for s_index, s_info in enumerate(subjects_string.splitlines()):
            if s_info.strip():
                s_name, s_id = SchoolFrameWork.id_name_from_text(s_info)
                
                s_id = ID(s_id)
                subjects[s_id] = (
                    CombinedSubject(s_id, [subjects[int(s.strip()) - 1] for s in s_name.strip().split("/")], None, {})
                    if "/" in s_name else
                    Subject(s_id, SubjectName(s_name.strip(), s_name.strip()), None, {})
                )
        
        l_subjects = list(subjects.values())
        
        teachers = {}
        teacher_subject_indices = {}
        for t_string in teachers_string.splitlines():
            t_string = t_string.strip()
            
            if t_string:
                t_info, value =  t_string.split(":")
                t_name, t_id = SchoolFrameWork.id_name_from_text(t_info)
                
                t_id = ID(t_id)
                teachers[t_id] = (
                        CombinedTeacher(t_id, [list([t for t, _ in teachers.values()])[int(s.strip()) - 1] for s in t_name.strip().split("/")])
                        if "/" in t_name else
                        Teacher(t_id, TeacherName(t_name.strip(), None, None, t_name.strip()), {})
                    )
                teacher_subject_indices[t_id] = tuple(int(v) - 1 for v in value.strip().split())
                
                for s_index in teacher_subject_indices[t_id]:
                    teachers[t_id].subjects[l_subjects[s_index].id] = l_subjects[s_index]
        
        weekdays_data = []
        for dw_string in dotw_string.split("_"):
            s_dotw_data = {}
            
            for s_dw_string in dw_string.splitlines():
                s_dw_string = s_dw_string.strip()
                
                if s_dw_string:
                    day, values = s_dw_string.split(":")
                    day, values = day.strip(), values.strip()
                    
                    p_amt, b_p = values.split()
                    
                    s_dotw_data[day] = int(p_amt), int(b_p)
            
            weekdays_data.append(s_dotw_data)
        
        timetables_data = {}
        
        all_classes = []
        class_levels = {}
        l_teachers = list(teachers.values())
        for cls_lvl_index, cls_lvl_string in enumerate(classes_string.split("_")):
            cls_lvl_data = cls_lvl_string.splitlines()
            cls_lvl_info, cls_data = cls_lvl_data[0], cls_lvl_data[1:]
            
            cls_lvl_id_data, subjects_occurence_string = cls_lvl_info.split(";")
            cls_lvl_name, lvl_id = SchoolFrameWork.id_name_from_text(cls_lvl_id_data)
            
            subject_occurence = {}
            
            for occ_string in subjects_occurence_string.strip().split():
                occ_string = occ_string.strip()
                
                if occ_string:
                    gs_index, day_max, week_max = occ_string.split("/")
                    
                    subject_occurence[l_subjects[int(gs_index.strip()) - 1].id] = SubjectOccurrance(int(day_max.strip()), int(week_max.strip()))
            
            classes = {}
            
            lvl_id = ID(lvl_id)
            cls_lvl = class_levels[lvl_id] = ClassLevel(lvl_id, ClassLevelName(cls_lvl_name), classes, subject_occurence, weekdays_data[cls_lvl_index])
            
            for c_string in cls_data:
                c_string = c_string.strip()
                
                cls_info, value =  c_string.split(":")
                cls_name, cls_id = SchoolFrameWork.id_name_from_text(cls_info)
                
                subject_mapping = {}
                
                cls_id = ID(cls_id)
                cls = classes[cls_id] = Class(cls_id, cls_name, cls_lvl, subject_mapping)
                all_classes.append(cls)
                
                timetables_data[cls_id] = (
                    {d: [FreePeriodFW() if i + 1 != b else BreakPeriodFW() for i in range(p)] for d, (p, b) in cls.level.weekdays.items()},
                    list(flatten([[s for _ in range(cls.level.subjects_occurence[s.id].week_max)] for s in cls.subjects]))
                )
                
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
        
        l_class_levels = list(class_levels)
        if timetable_string:
            for cls_i, ttbl_string in enumerate(timetable_string.split("_")):
                cls = all_classes[cls_i]
                l_weekdays = list(weekdays_data[l_class_levels.index(cls.level.id)])
                
                ttbl_string = ttbl_string.strip()
                
                if ttbl_string:
                    timetable, _ = timetables_data[cls.id] = {}, []
                    
                    for s_ttbl_i, s_ttbl_string in enumerate(ttbl_string.strip().split(";")):
                        s_ttbl_string = s_ttbl_string.strip()
                        
                        if s_ttbl_string:
                            timetable[l_weekdays[s_ttbl_i]] = [
                                (
                                    FreePeriodFW()
                                    if int(s.strip()) == 0 else
                                    (
                                        BreakPeriodFW()
                                        if int(s.strip()) == -1 else
                                        list(cls.subjects.values())[int(s.strip()) - 1]
                                    )
                                )
                                for s in
                                s_ttbl_string.split()
                            ]
        
        return SchoolFrameWork(subjects, teachers, class_levels, timetables_data, GeneratingData(False, {}, {}, {}))



def _display_school(sch: SchoolFrameWork):
    for cls_lvl in sch.class_lvls.values():
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


if __name__ == "__main__":
    with open(r"C:\Users\User\Documents\GitHub\IFEs Timetable Manager\timetable\test\test-frmwk.txt") as file:
        data = file.read()
    
    sch = SchoolFrameWork.school_from_text(data)
    
    print("Started Generating")
    sch.generate_timetable()
    print("Started Clash detection")
    print(sch.detect_clashes())
    print("Ended")
    print()
    
    _display_school(sch)

