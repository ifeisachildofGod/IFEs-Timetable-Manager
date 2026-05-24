
import json
import math
import random
from core import ID
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


# Subject Periods
@dataclass
class SubjectPeriodFW:
    id: str
    
    name: str
    
    teacher: "TeacherFW | None" = None
    #                Day  Week
    freq_info: tuple[int, int] | None = None

@dataclass
class CombinedSubjectPeriodFW:
    id: str
    
    subjects: list[SubjectPeriodFW]
    
    teacher: "CombinedTeacherFW | None" = None
    
    #                Day  Week
    freq_info: tuple[int, int] | None = None

@dataclass
class FreePeriodFW:
    id: str = "FreePeriodID"
    
    name: str = "Free"
    teacher: "TeacherFW | None" = None

@dataclass
class BreakPeriodFW:
    id: str = "BreakPeriodID"
    
    name: str = "Break"
    teacher: "TeacherFW | None" = None


# Objects
TimetableFW = dict[str, list[SubjectPeriodFW | CombinedSubjectPeriodFW | BreakPeriodFW | FreePeriodFW]]

@dataclass
class TeacherFW:
    id: str
    
    name: str

@dataclass
class CombinedTeacherFW:
    id: str
    
    teachers: list[TeacherFW]

@dataclass
class ClassFW:
    section_id: ID
    specifier_id: ID
    
    section_name: str
    specifier_name: str
    
    #                    Period Amount  Break Period
    weekdays_data: dict[str, tuple[int, int]]
    
    #           SubjectID
    subjects: dict[str, SubjectPeriodFW | CombinedSubjectPeriodFW]
    
    timetable: TimetableFW | None = None
    timetable_remains: list[SubjectPeriodFW] | None = None
    
    def init(self):
        if self.timetable is None:
            self.timetable = {d: [FreePeriodFW() if i + 1 != b else BreakPeriodFW() for i in range(p)] for d, (p, b) in self.weekdays_data.items()}
        
        if self.timetable_remains is None:
            self.timetable_remains = flatten([[s for _ in range(s.freq_info[1])] for s in self.subjects])
    
    def name(self):
        return f"{self.section_name} {self.specifier_name}"
    
    def id(self):
        return self.specifier_id + self.section_id

@dataclass
class SchoolFrameWork:
    subjects: dict[str, SubjectPeriodFW | CombinedSubjectPeriodFW]
    teachers: dict[str, TeacherFW]
    classes: dict[str, ClassFW]
    
    #         Teacher ID  Classes
    teachers_c: dict[str, list[ClassFW]]
    gen_data: GeneratingData
    _log_data: dict[str, dict[str, list[str]]] | None = None
    
    def generate_timetable(self, cls_ids: list[str] | None = None):
        if not self._log_data:
            self._log_data = {}
        
        cls_ids = cls_ids or list(self.classes)
        
        for cls_id in cls_ids:
            cls = self.classes[cls_id]
            
            if cls.timetable is None:
                cls.timetable = {d: [FreePeriodFW() if i + 1 != b else BreakPeriodFW() for i in range(p)] for d, (p, b) in cls.weekdays_data.items()}
            
            week_amt_data = {s_id: s.freq_info[1] for s_id, s in cls.subjects.items()} # type: ignore
            
            total_available_periods = sum(amt for amt, _ in cls.weekdays_data.values())
            total_subj_amt = sum(list(week_amt_data.values()))
            
            assert total_available_periods > total_subj_amt, "Period slots are not enough for the amount of subjects"
            
            for s_list in cls.timetable.values():
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
                    freq_info = cls.subjects[s_id].freq_info
                    
                    assert freq_info
                    
                    for _ in range(freq_info[0]):
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
                        
                        assert cls.timetable[day][index].id == FreePeriodFW.id
                        
                        cls.timetable[day][index] = cls.subjects[s_id]
                        week_amt_data[s_id] -= 1
                        
                        if week_amt_data[s_id] <= 0:
                            completed_ones.append(s_id)
            
            cls.timetable_remains = list(flatten([[self.subjects[s_id] for _ in range(amt)] for s_id, amt in week_amt_data.items()]))
    
    def detect_clashes(self):
        clashes = {}
        
        for teacher_id, classes in self.teachers_c.items():
            teacher = self.teachers[teacher_id]
            
            day_markers = []
            day_marker_mapping = {}
            
            for cls in classes:
                assert cls.timetable
                
                for day, periods in cls.timetable.items():
                    for p_index, subject_period in enumerate(periods):
                        if subject_period.id not in (FreePeriodFW.id, BreakPeriodFW.id):
                            assert subject_period.teacher
                            
                            if teacher.id == subject_period.teacher.id:
                                marker = day, p_index
                                
                                day_markers.append(marker)
                                
                                if marker not in day_marker_mapping:
                                    day_marker_mapping[marker] = []
                                
                                day_marker_mapping[marker].append((cls, subject_period.id))
            
            t_clashes = {}
            
            l_dmm = list(day_marker_mapping.values())
            
            for marker, classes in day_marker_mapping.items():
                if len(classes) > 1:
                    for cls, sp_id in classes:
                        combined = next(
                            (
                                True 
                                for s_cls, s_sp_id in
                                l_dmm
                                if next(
                                    (
                                        True
                                        for s_list, c_list in
                                        self.gen_data.combined_subjects.items()
                                        if (sp_id in s_list and s_sp_id in s_list) and (cls.id in c_list and s_cls.id in c_list)
                                        ),
                                    False
                                    )
                                ),
                            False
                            )
                        
                        if not combined:
                            t_clashes[marker] = cls.id
            
            if t_clashes:
                clashes[teacher.id] = t_clashes
        
        return clashes
    
    def _sps(self, s_id: str, cls: ClassFW):
        period_scores: dict[str, list[int | float]] = {day: [] for day in cls.weekdays_data}
        
        assert cls.timetable
        
        for day, periods in cls.timetable.items():
            for p_index, period in enumerate(periods):
                period_scores[day].append(self._period_score(s_id, cls, day, period, p_index))
        
        return period_scores
    
    def _period_score(
            self,
            s_id: str,
            cls: ClassFW,
            day: str,
            period: SubjectPeriodFW | CombinedSubjectPeriodFW | FreePeriodFW | BreakPeriodFW,
            p_index: int,
            l_operate: int = False,
            r_operate: int = False,
            default_score = -50
        ):
        if cls.id() not in self._log_data:
            self._log_data[cls.id()] = {}
        if s_id not in self._log_data[cls.id()]:
            self._log_data[cls.id()][s_id] = []
        
        subject = cls.subjects[s_id]
        
        assert cls.timetable
        
        periods = cls.timetable[day]
        
        if not (0 <= p_index <= len(periods) - 1):
            self._log_data[cls.id()][s_id].append(((day, p_index + 1), "Period out of timetable range"))
            return -math.inf
        
        assert subject.teacher
        assert subject.freq_info
        
        _l_d_freq = [s.freq_info[0] for s in cls.subjects.values()] # type: ignore
        avg_day_freq = sum(_l_d_freq) // len(_l_d_freq)
        
        assert isinstance(avg_day_freq, int)
        
        if (
                period.id != FreePeriodFW.id or
                period.id == BreakPeriodFW.id or
                [p.id for p in periods].count(s_id) >= subject.freq_info[0] or
                abs(p_index - next((p_i for p_i, p in enumerate(periods) if p.id == s_id), p_index + 1)) != 1
                ):
            if period.id == BreakPeriodFW.id:
                self._log_data[cls.id()][s_id].append(((day, p_index + 1), "Break period"))
            elif period.id != FreePeriodFW.id:
                self._log_data[cls.id()][s_id].append(((day, p_index + 1), f"Period is occupied by {period.name}"))
            elif [p.id for p in periods].count(s_id) >= subject.freq_info[0]:
                self._log_data[cls.id()][s_id].append(((day, p_index + 1), f"Per day max reached: {[p.id for p in periods].count(s_id)}"))
            else:
                self._log_data[cls.id()][s_id].append(((day, p_index + 1), "Period island"))
            
            return -math.inf
        
        score = default_score
        
        for s_cls in self.classes.values():
            if s_cls.timetable is not None:
                s_subject = s_cls.timetable[day][p_index]
                
                if s_cls.id() != cls.id() and s_subject.id not in (FreePeriodFW.id, BreakPeriodFW.id):
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
                    
                    if isinstance(s_teacher, TeacherFW):
                        if isinstance(subject.teacher, TeacherFW):
                            is_clashing = subject.teacher.id == s_teacher.id
                        elif isinstance(subject.teacher, CombinedTeacherFW):
                            is_clashing = s_teacher.id in [t.id for t in subject.teacher.teachers]
                    elif isinstance(s_teacher, CombinedTeacherFW):
                        if isinstance(subject.teacher, TeacherFW):
                            is_clashing = subject.teacher.id in [t.id for t in s_teacher.teachers]
                        elif isinstance(subject.teacher, CombinedTeacherFW):
                            is_clashing = next((True for t in s_teacher.teachers if t.id in [s_t.id for s_t in subject.teacher.teachers]), False)
                    
                    if is_clashing is None:
                        raise Exception()
                    
                    if is_clashing and not combined:
                        self._log_data[cls.id()][s_id].append(((day, p_index + 1), f"Alignment Error: subject is{"not " if isinstance(subject.teacher, TeacherFW) else ""} combined and{"" if isinstance(subject.teacher, TeacherFW) else "not "} clashing/aligned with {"another subject" if isinstance(s_teacher, TeacherFW) else "any subject"}"))
                        
                        return -math.inf
        else:
            clump_wieght = (self.gen_data.subject_clumping_weights[cls.id()][s_id][day] or 0) if cls.id in self.gen_data.subject_clumping_weights else 1
            day_weight, period_proclivity = (self.gen_data.subject_positioning_weights[cls.id()][s_id][day] if cls.id() in self.gen_data.subject_positioning_weights else (None, None))
            
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
                    mul = subject.freq_info[0] - [p.id for p in periods].count(s_id)
                    
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
                    
                    score += (((l_depth + r_depth) / subject.freq_info[0]) * 2 - 1) * clump_wieght * 15
                
                if score == orig:
                    score -= 20
                
                score += sum((p_index - s_p_index) - (s_period.freq_info[0] - periods.count(s_period)) for s_p_index, s_period in enumerate(periods) if not s_period.id in (FreePeriodFW.id, BreakPeriodFW.id)) # type: ignore
            
            if l_operate or r_operate:
                return l_operate + r_operate
            
            period_amt, break_period = cls.weekdays_data[day]
            
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
    def school_from_text(text: str, id_mappings: dict[str, list[str]] | None = None):
        id_mappings = id_mappings or {"subjects": None, "teachers": None, "classes": None}
        
        text = "\n".join(["".join(list(line)[:line.find("#")] if "#" in line else list(line)) for line in text.splitlines()])
            
        subjects_string, teachers_string, classes_string, timetable_string, dotw_string = text.split("---")

        subjects_string = subjects_string.strip()
        teachers_string = teachers_string.strip()
        classes_string = classes_string.strip()
        timetable_string = timetable_string.strip()
        dotw_string = dotw_string.strip()

        subjects = []
        for s_index, s_string in enumerate(subjects_string.splitlines()):
            s_string = s_string.strip()
            
            if s_string:
                s_id = id_mappings["subjects"][len(subjects)] if id_mappings["subjects"] else str(len(subjects))
                
                subjects.append(
                    CombinedSubjectPeriodFW(s_id, [subjects[int(s.strip()) - 1] for s in s_string.strip().split("/")])
                    if "/" in s_string else
                    SubjectPeriodFW(s_id, s_string)
                )
        
        teachers = {}
        for t_string in teachers_string.splitlines():
            t_string = t_string.strip()
            
            if t_string:
                name, value =  t_string.split(":")
                
                t_id = id_mappings["teachers"][len(teachers)] if id_mappings["teachers"] else str(len(teachers))
                
                teachers[t_id] = (
                        CombinedTeacherFW(t_id, [list([t for t, _ in teachers.values()])[int(s.strip()) - 1] for s in name.strip().split("/")])
                        if "/" in name else
                        TeacherFW(t_id, name.strip())
                    ), tuple(int(v) - 1 for v in value.strip().split())
        
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
        
        _cls_id_trackers = {}
        sc_classes = {}
        sc_teachers_c = {}
        for c_index, c_string in enumerate(classes_string.splitlines()):
            c_string = c_string.strip()
            
            name, value =  c_string.split(":")
            se_name, sp_name = name.strip().split()
            
            subject_mapping = {}
            
            for v in value.strip().split():
                s_list = v.split("/")
                
                if len(s_list) == 3:
                    t_index, per_day, per_week = s_list
                    s_index = "1"
                elif len(s_list) == 4:
                    t_index, s_index, per_day, per_week = s_list
                else:
                    raise Exception()
                
                l_teachers = list(teachers.values())
                
                t_index = int(t_index.strip()) - 1
                s_index = int(s_index.strip()) - 1
                per_day = int(per_day)
                per_week = int(per_week)
                
                if not (0 <= t_index <= len(l_teachers) - 1):
                    raise IndexError(f"Invalid teacher index: {t_index + 1}")
                
                teacher, subject_indices = l_teachers[t_index]
                
                if not (0 <= s_index <= len(subject_indices) - 1):
                    raise IndexError(f"Invalid teacher-subject index: {s_index + 1}")
                
                if not (0 <= subject_indices[s_index] <= len(subjects) - 1):
                    raise IndexError(f"Invalid subject index: {subject_indices[s_index] + 1}")
                
                r_subject = subjects[subject_indices[s_index]]
                
                if isinstance(r_subject, SubjectPeriodFW) and isinstance(teacher, TeacherFW):
                    subject = SubjectPeriodFW(r_subject.id, r_subject.name, teacher, (per_day, per_week))
                elif isinstance(r_subject, CombinedSubjectPeriodFW) and isinstance(teacher, CombinedTeacherFW):
                    subject = CombinedSubjectPeriodFW(r_subject.id, r_subject.subjects, teacher, (per_day, per_week))
                else:
                    raise Exception()
                
                subject_mapping[subject.id] = subject
            
            se_key = se_name
            sp_key = (sp_name, )
            
            if se_key not in _cls_id_trackers:
                _cls_id_trackers[se_key] = id_mappings["classes"][c_index][0] if id_mappings["classes"] else id(se_name)
            if sp_key not in _cls_id_trackers:
                _cls_id_trackers[sp_key] = id_mappings["classes"][c_index][1] if id_mappings["classes"] else id(sp_name)
            
            cls = ClassFW(_cls_id_trackers[se_key], _cls_id_trackers[sp_key], se_name, sp_name, weekdays_data[c_index], subject_mapping)
            sc_classes[cls.id()] = cls
            
            for subj in subject_mapping.values():
                if subj.teacher.id not in sc_teachers_c:
                    sc_teachers_c[subj.teacher.id] = []
                
                if cls in sc_teachers_c[subj.teacher.id]:
                    continue
                
                sc_teachers_c[subj.teacher.id].append(cls)
        
        if timetable_string:
            for cls_i, ttbl_string in enumerate(timetable_string.split("_")):
                cls = list(sc_classes.values())[cls_i]
                
                ttbl_string = ttbl_string.strip()
                
                if ttbl_string:
                    sc_classes[cls.id].timetable = {}
                    
                    for s_ttbl_i, s_ttbl_string in enumerate(ttbl_string.strip().split(";")):
                        s_ttbl_string = s_ttbl_string.strip()
                        
                        if s_ttbl_string:
                            sc_classes[cls.id].timetable[list(weekdays_data[cls_i])[s_ttbl_i]] = [
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
                else:
                    sc_classes[cls.id].timetable = None
        
        return SchoolFrameWork({s.id: s for s in subjects}, {k: v for k, (v, _) in teachers.items()}, sc_classes, sc_teachers_c, GeneratingData(False, {}, {}, {}))



def _display_school(sch: SchoolFrameWork):
    for cls in sch.classes.values():
        assert cls.timetable
        
        print(cls.name())
        for day, periods in cls.timetable.items():
            print(day, end=": ")
            print(*[(p.name if not isinstance(p, CombinedSubjectPeriodFW) else "/".join([s.name for s in p.subjects])) for p in periods], sep=", ")
        
        if cls.timetable_remains:
            print()
            print("Remainders:", ", ".join([s.name for s in cls.timetable_remains]))
            print()
        print()


if __name__ == "__main__":
    with open(Path(__file__).parent.joinpath(Path("test-frmwk.txt"))) as file:
        data = file.read()
    
    sch = SchoolFrameWork.school_from_text(data)
    
    print("Started Generating")
    sch.generate_timetable()
    print("Started Clash detection")
    print(sch.detect_clashes())
    print("Ended")
    print()
    
    _display_school(sch)

