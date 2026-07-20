
from ..base_widgets import *
from ..extra_widgets import *
from ..core_data_objects import *


class _CharacterNameWidget(QWidget):
    def __init__(self, name: StaffName):
        super().__init__()
        self.name = name
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        widget_2_1 = QWidget()
        layout_2_1 = QVBoxLayout()
        widget_2_1.setLayout(layout_2_1)
        
        widget_2_1_1 = QWidget()
        layout_2_1_1 = QHBoxLayout()
        widget_2_1_1.setLayout(layout_2_1_1)
        layout_2_1.addWidget(widget_2_1_1)
        
        name_1 = LabeledField("Surname", QLabel(self.name.start))
        name_2 = LabeledField("First name", QLabel(self.name.first))
        
        layout_2_1_1.addWidget(name_1)
        layout_2_1_1.addWidget(name_2)
        
        widget_2_1_2 = QWidget()
        layout_2_1_2 = QHBoxLayout()
        widget_2_1_2.setLayout(layout_2_1_2)
        layout_2_1.addWidget(widget_2_1_2)
        
        name_4 = LabeledField("Other name", QLabel(self.name.other if self.name.other else "No other name"))
        name_5 = LabeledField("Abbreviation", QLabel(self.name.abbrev if self.name.abbrev else "No abbreviatory name"))
        
        layout_2_1_2.addWidget(name_4)
        layout_2_1_2.addWidget(name_5, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.main_layout.addWidget(LabeledField("Names", widget_2_1, height_policy=QSizePolicy.Policy.Maximum))

    

class AttendanceTeacherEntryWidget(BaseAttendanceEntryWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Teacher", data)
        
        self.labeled_container.setProperty("class", "AttendanceTeacherEntryWidget")
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.minute < 10 else "") + str(self.data.period.time.minute))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.second < 10 else "") + str(self.data.period.time.second))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = _CharacterNameWidget(self.staff.name)
        layout_2.addWidget(name_widget)
        
        if data.is_check_in:
            _, layout_2_2 = create_widget(layout_2, QVBoxLayout)
            
            widget_2_2_2, layout_2_2_2 = create_scrollable_widget(None, QVBoxLayout)
            
            layout_2_2.addWidget(LabeledField("Subjects", widget_2_2_2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            
            periods_data: dict[tuple[str, str], dict[tuple[str, str], list[int]]] = {}
            
            for subject in self.staff.subjects.values():
                # clses: dict[CLASS_ID, Class] = {}
                # subject.classes = clses
                s_periods = []
                
                for cls in subject.classes.values():
                    if cls.timetable.table_remains.count(subject) < cls.level.subjects_occurence[subject.id].week_max:
                        for day, w_periods in cls.timetable.table.items():
                            if subject in w_periods:
                                for i, s in enumerate(w_periods):
                                    if subject.id == s.id:
                                        s_periods.append((day, i + 1))
                
                for day_name, period in subject.get_periods():
                    if self.data.period.day == day_name:
                        key = subject.id
                        sub_key = subject.cls.id
                        
                        if periods_data.get(key) is None:
                            periods_data[key] = {}
                        if periods_data[key].get(sub_key) is None:
                            periods_data[key][sub_key] = []
                        periods_data[key][sub_key].append(period)
            
            for (_, subject_name), subject_data in periods_data.items():
                widget_2_2_2_1, layout_2_2_2_1 = create_widget(None, QGridLayout)
                
                for index, ((_, cls_name), periods) in enumerate(subject_data.items()):
                    widget_2_2_2_1_1, layout_2_2_2_1_1 = create_widget(None, QVBoxLayout)
                    for period in periods:
                        layout_2_2_2_1_1.addWidget(QLabel(f"{positionify(str(period))} period"), alignment=Qt.AlignmentFlag.AlignTop)
                    layout_2_2_2_1.addWidget(LabeledField(cls_name, widget_2_2_2_1_1), int(index / 3), index % 3)
                layout_2_2_2.addWidget(LabeledField(subject_name, widget_2_2_2_1))

class AttendancePrefectEntryWidget(BaseAttendanceEntryWidget):
    def __init__(self, data: AttendanceEntry):
        super().__init__("Prefect", data)
        
        self.labeled_container.setProperty("class", "AttendancePrefectEntryWidget")
        
        _, layout_1 = create_widget(self.main_layout, QVBoxLayout)
        
        image = Image(self.staff.img_path, parent=self.container, height=300)
        
        layout_1.addWidget(image, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout_1.addStretch()
        
        widget_1_2, layout_1_2 = create_widget(None, QHBoxLayout)
        
        layout_1.addWidget(widget_1_2)
        
        widget_1_2_1, layout_1_2_1 = create_widget(None, QHBoxLayout)
        
        layout_1_2_1.addWidget(LabeledField("Day", QLabel(self.data.period.day)))
        layout_1_2_1.addWidget(LabeledField("Date", QLabel(f"{positionify(str(self.data.period.date))} of {self.data.period.month}, {self.data.period.year}")))
        
        layout_1_2.addWidget(LabeledField("Date Info", widget_1_2_1, height_policy=QSizePolicy.Policy.Maximum))
        
        widget_1_2_2, layout_1_2_2 = create_widget(None, QHBoxLayout)
        
        layout_1_2_2.addWidget(LabeledField("Hr", QLabel(("0" if self.data.period.time.hour < 10 else "") + str(self.data.period.time.hour))))
        layout_1_2_2.addWidget(LabeledField("Min", QLabel(("0" if self.data.period.time.minute < 10 else "") + str(self.data.period.time.minute))))
        layout_1_2_2.addWidget(LabeledField("Sec", QLabel(("0" if self.data.period.time.second < 10 else "") + str(self.data.period.time.second))))
        
        layout_1_2.addWidget(LabeledField("Time", widget_1_2_2, height_policy=QSizePolicy.Policy.Maximum))
        
        _, layout_2 = create_widget(self.main_layout, QVBoxLayout)
        
        name_widget = _CharacterNameWidget(self.staff.name)
        layout_2.addWidget(name_widget)
        
        widget_2_2, layout_2_2 = create_widget(None, QHBoxLayout)
        
        layout_2_2.addWidget(LabeledField("Class", QLabel(f"{self.staff.cls.level.name.full()} {self.staff.cls.name}"), height_policy=QSizePolicy.Policy.Maximum))
        
        if data.is_check_in:
            widget_1_3_1, layout_1_3_1 = create_scrollable_widget(None, QVBoxLayout)
            
            for index, duty in enumerate(self.staff.duties.get(self.data.period.day, [])):
                layout_1_3_1.addWidget(QLabel(f"{index + 1}. {duty}"))
            
            layout_2_2.addWidget(LabeledField("Duties", widget_1_3_1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        
        layout_2.addWidget(widget_2_2)



class StaffListPrefectEntryWidget(BaseStaffListEntryWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, prefect: Prefect, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, prefect, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListPrefectEntryWidget")
        
        self.sub_info_layout.addWidget(LabeledField("Post", QLabel(self.staff.post_name)))
        self.sub_info_layout.addWidget(LabeledField("Class", QLabel(f"{self.staff.cls.level.name.full()} {self.staff.cls.name}")))

class StaffListTeacherEntryWidget(BaseStaffListEntryWidget):
    def __init__(self, parent_widget: TabViewWidget, data: AppData, teacher: Teacher, comm_device: BaseCommSystem, card_scanner_index: int, staff_data_index: int):
        super().__init__(parent_widget, data, teacher, comm_device, card_scanner_index, staff_data_index)
        self.container.setProperty("class", "StaffListTeacherEntryWidget")
        
        subj_data_widget, subj_data_layout = create_scrollable_widget(None, QVBoxLayout)
        subj_data_widget.setMinimumHeight(110)
        
        for subject in self.staff.subjects.values():
            cls_d_widg, cls_d_lyt = create_widget(None, QVBoxLayout)
            
            subj_data_layout.addWidget(LabeledField(subject.name.full(), cls_d_widg))
            
            for cls in subject.classes.values():
                if cls.subjects[subject.id].teacher and teacher.id == cls.subjects[subject.id].teacher.id:
                    cls_d_lyt.addWidget(QLabel(f"<b>●</b> {cls.level.name.full()} {cls.name}"))
        
        self.sub_info_layout.addWidget(LabeledField("Subjects", subj_data_widget), alignment=Qt.AlignmentFlag.AlignCenter)


