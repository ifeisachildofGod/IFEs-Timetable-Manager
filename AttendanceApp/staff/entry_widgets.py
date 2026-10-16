
from widgets.base import *
from widgets.user_interface import *

from ..base_widgets import *
from ..extra_widgets import *


class AttendancePrefectEntryWidget(BaseAttendanceEntryWidget[Prefect]):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Prefect", data)
        self.labeled_container.setProperty("class", "AttendancePrefectEntryWidget")
        
        info_sub_widget = BaseWidget()
        
        self.class_label = QLabel()
        self.post_label = QLabel()
        
        info_sub_widget.addWidget(LabeledField("Class", self.class_label, height_policy=QSizePolicy.Policy.Maximum))
        info_sub_widget.addWidget(LabeledField("Post Name", self.post_label, height_policy=QSizePolicy.Policy.Maximum))
        
        sub_main_info_widget = BaseWidget(QHBoxLayout)
        
        sub_main_info_widget.addWidget(info_sub_widget)
        if data.is_check_in:
            widget_1_3_1 = BaseScrollWidget()
            
            for index, duty in enumerate(self.staff.duties.get(self.data.period.day, [])):
                widget_1_3_1.addWidget(QLabel(f"<b>{index + 1}.</b> <span style='font-weight: bold'>{"<br>&nbsp;&nbsp;&nbsp;&nbsp;".join(wrapify_text(duty, 50))}</span>"))
            
            sub_main_info_widget.addWidget(LabeledField("Duties", widget_1_3_1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        self.main_info_widget.addWidget(sub_main_info_widget)
        
        self.update_class()
        self.update_post()
    
    def update_class(self):
        self.class_label.setText(
            f"<b>{self.staff.cls.level.name.full()} {self.staff.cls.name}</b"
            if self.staff.cls is not None else
            "<i><b style='font-size: larger;'>NONE</b></i>"
        )
    
    def update_post(self):
        self.post_label.setText(
            f"<span style='font-weight: bold'>{"<br>".join(wrapify_text(SCHOOL.posts[self.staff.post_id], 30))}</span>"
            if self.staff.post_id is not None else
            "<i><b style='font-size: larger;'>NONE</b></i>"
        )

class AttendanceTeacherEntryWidget(BaseAttendanceEntryWidget[Teacher]):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Teacher", data)
        self.labeled_container.setProperty("class", "AttendanceTeacherEntryWidget")
        
        if data.is_check_in:
            self.main_info_widget.addWidget(LabeledField("Subjects", (widget_2_2_2 := BaseScrollWidget()), QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            widget_2_2_2.setFixedHeight(180)
            
            periods_data: dict[tuple[str, str], dict[tuple[str, str], list[int]]] = {}
            
            for subject in self.staff.subjects.values():
                subject_periods = []
                
                for cls in subject.classes.values():
                    for day, periods in cls.timetable.table.items():
                        for i, s in enumerate(periods):
                            if isinstance(s, Subject):
                                if self.staff.id == s.teacher.id and day not in subject_periods:
                                    subject_periods.append((cls.id, day, i + 1))
                            elif isinstance(s, CombinedSubject):
                                if next((True for s_s in s.subjects if s_s.id == subject.id and s_s.teacher is not None and s_s.teacher.id == self.staff.id), False):
                                    subject_periods.append((cls.id, day, i + 1))
                
                for cls_id, day_name, period in subject_periods:
                    if self.data.period.day == day_name:
                        if periods_data.get(subject.id) is None:
                            periods_data[subject.id] = {}
                        if periods_data[subject.id].get(cls_id) is None:
                            periods_data[subject.id][cls_id] = []
                        periods_data[subject.id][cls_id].append(period)
        
            for subject_id, subject_data in periods_data.items():
                widget_2_2_2_1, layout_2_2_2_1 = create_widget(None, QGridLayout)
                
                for index, (cls_id, periods) in enumerate(subject_data.items()):
                    cls = SCHOOL.class_levels[cls_id.class_level_id].classes[cls_id]
                    
                    widget_2_2_2_1_1, layout_2_2_2_1_1 = create_widget(None, QVBoxLayout) ; layout_2_2_2_1_1.addStretch()
                    for i, period in enumerate(periods):
                        layout_2_2_2_1_1.insertWidget(i, QLabel(f"<b>{positionify(str(period))} period</b>"))
                    layout_2_2_2_1.addWidget(LabeledField(f"{cls.level.name.full()} {cls.name}", widget_2_2_2_1_1), int(index / 3), index % 3)
                widget_2_2_2.addWidget(LabeledField(SCHOOL.subjects[subject_id].name.full(), widget_2_2_2_1))


class StaffListPrefectEntryWidget(BaseStaffListEntryWidget[Prefect]):
    def __init__(self, parent_widget, staff, comm_system, card_scanner_widget, staff_data_widget):
        super().__init__(parent_widget, staff, comm_system, card_scanner_widget, staff_data_widget)
        
        self.container.setProperty("class", "StaffListPrefectEntryWidget")
        
        self._duty_text: dict[str, list[str]] = {}
        self._duty_day_widgets: dict[str, LabeledField] = {}
        
        self.cls_label = QLabel()
        self.post_label = QLabel()
        self.duties_widget = BaseScrollWidget() ; self.duties_widget.setMinimumHeight(110)
        
        self.sub_info_widget.addWidget(LabeledField("Class", self.cls_label, height_policy=QSizePolicy.Policy.Maximum), stretch=4)
        self.sub_info_widget.addWidget(LabeledField("Post", self.post_label, height_policy=QSizePolicy.Policy.Maximum), stretch=4)
        self.sub_info_widget.addWidget(LabeledField("Duties", self.duties_widget), stretch=9)
        
        self.update_class()
        self.update_post()
        
        for day, duties in self.staff.duties.items():
            for duty in duties:
                self.add_duty(day, duty)
    
    def update_class(self):
        self.cls_label.setText(
            f"<span style='font-weight: bold'>{self.staff.cls.level.name.full()} {self.staff.cls.name}</span>"
            if self.staff.cls is not None else
            "<i><b style='font-size: larger;'>NONE</b></i>"
        )
    
    def update_post(self):
        self.post_label.setText(
            f"<span style='font-weight: bold'>{"<br>".join(wrapify_text(SCHOOL.posts[self.staff.post_id], 30))}</span>"
            if self.staff.post_id is not None else
            "<i><b style='font-size: larger;'>NONE</b></i>"
        )
    
    def update_duty(self, day: str, index: int):
        duty = self.staff.duties[day][index]
        
        self._duty_text[day][index] = duty
        
        label: QLabel = self._duty_day_widgets[day].inner_widget.indexWidget(index)
        label.setText(f"<b>●</b> <span style='font-weight: bold'>{"<br>&nbsp;&nbsp;".join(wrapify_text(duty, 45))}</span>")
    
    def add_duty(self, day: str, duty: str):
        if day not in self._duty_day_widgets:
            self._duty_text[day] = []
            self._duty_day_widgets[day] = LabeledField(day, BaseWidget())
            
            self.duties_widget.addWidget(self._duty_day_widgets[day])
        
        self._duty_text[day].append(duty)
        self._duty_day_widgets[day].inner_widget.addWidget(QLabel())
        
        self.update_duty(day, len(self._duty_text[day]) - 1)
    
    def remove_duty(self, day: str, index: int):
        self._duty_text[day].pop(index)
        self._duty_day_widgets[day].inner_widget.popWidget(index)
        
        if not self._duty_text:
            day_widget = self._duty_day_widgets[day]
            
            self.duties_widget.removeWidget(day_widget)
            day_widget.deleteLater()
            
            self._duty_text.pop(day)
            self._duty_day_widgets.pop(day)

class StaffListTeacherEntryWidget(BaseStaffListEntryWidget[Teacher]):
    def __init__(self, parent_widget, staff, comm_system, card_scanner_widget, staff_data_widget):
        super().__init__(parent_widget, staff, comm_system, card_scanner_widget, staff_data_widget)
        
        self.subject_fields: dict[ID, LabeledField] = {}
        self.class_labels: dict[ID, list[tuple[ID, QLabel]]] = {}
        self.subject_cls_widgets: dict[ID, BaseWidget] = {}
        
        self.container.setProperty("class", "StaffListTeacherEntryWidget")
        
        self.subj_data_widget = BaseScrollWidget()
        self.subj_data_widget.setMinimumHeight(110)
        
        for subject in self.staff.subjects.values():
            self.add_subject(subject)
        
        self.sub_info_widget.addWidget(s_lf := LabeledField("Subjects", self.subj_data_widget), alignment=Qt.AlignmentFlag.AlignCenter)
        s_lf.setFixedWidth(440)
    
    def add_subject(self, subject: Subject):
        self.subject_cls_widgets[subject.id] = BaseWidget()
        
        self.subject_fields[subject.id] = LabeledField("", self.subject_cls_widgets[subject.id])
        self.update_subject_name(subject)
        
        self.subj_data_widget.addWidget(self.subject_fields[subject.id])
        
        for cls in subject.classes.values():
            if subject.id in cls.subjects:
                if cls.subjects[subject.id].teacher and cls.subjects[subject.id].teacher.id == self.staff.id:
                    self.add_class(subject.id, cls)
            else:
                for subj in SCHOOL.subjects.values():
                    if isinstance(subj, CombinedSubject) and next((subj.id in cls.subjects and cls.subjects[subj.id].subjects[i].teacher and cls.subjects[subj.id].subjects[i].teacher.id == self.staff.id for i, s in enumerate(subj.subjects) if s.id == subject.id), False):
                        self.add_class(subject.id, cls)
                        break
    
    def remove_subject(self, subject: Subject):
        field = self.subject_fields[subject.id]
        
        self.subj_data_widget.removeWidget(field)
        field.deleteLater()
        
        for cls in subject.classes.values():
            if cls.id in self.class_labels:
                for cls_data in self.class_labels[cls.id].copy():
                    s_id, _ = cls_data
                    
                    if s_id == subject.id:
                        self.class_labels[cls.id].remove(cls_data)
    
    def add_class(self, subject_id: ID, cls: Class):
        if cls.id not in self.class_labels:
            self.class_labels[cls.id] = []
        
        label = QLabel()
        self.subject_cls_widgets[subject_id].addWidget(label)
        
        self.class_labels[cls.id].append((subject_id, label))
        self.update_class_name(cls)
    
    def remove_class(self, subject_id: ID, cls_id: ID):
        for cls_label_data in self.class_labels[cls_id].copy():
            s_id, label = cls_label_data
            
            if s_id == subject_id:
                self.subject_cls_widgets[s_id].removeWidget(label)
                label.deleteLater()
                
                self.class_labels[cls_id].remove(cls_label_data)
    
    def update_subject_name(self, subject: Subject):
        self.subject_fields[subject.id].setTitle(f"<span style='font-weight: bold'>{subject.name.full()}</span>")
    
    def update_class_name(self, cls: Class):
        for _, label in self.class_labels[cls.id]:
            label.setText(f"<b>●</b> <span style='font-weight: bold'>{cls.level.name.full()} {cls.name}</span>")


