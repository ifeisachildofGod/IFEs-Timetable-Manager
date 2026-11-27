import random
from itertools import product

from communication import BaseCommSystem
from widgets.user_interface import *

from .base_widgets import *
from .data_display_widgets import *


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


class AttendanceWidget(BaseScrollListWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, parent_widget: TabViewWidget, attendance_chart_widget: "AttendanceBarWidget", punctuality_graph_widget: "PunctualityGraphWidget", comm_system: BaseCommSystem):
        super().__init__()
        
        self.__init = True
        
        self.kb_dbg_action_mapping = {}
        self.cs_dbg_action_mapping = {}
        
        try:
            action_mappings = {
                "kb": self.kb_dbg_action_mapping,
                "cs": self.cs_dbg_action_mapping,
            }
            
            with open("AttendanceApp/src/dbg.txt") as dbg_file:
                mapping_data = dbg_file.read().strip().splitlines()
                
                for text in mapping_data:
                    text = text.strip()
                    
                    key = None
                    for key in action_mappings:
                        if text.startswith(key):
                            break
                    
                    if key is not None:
                        text = text.removeprefix(key).strip()
                        
                        k, v = text.split(",")
                        
                        action_mappings[key][k.strip()] = v.strip()
        except Exception as e:
            print(e)
        
        self.comm_system = comm_system
        self.parent_widget = parent_widget
        
        self.attendance_chart_widget = attendance_chart_widget
        self.punctuality_graph_widget = punctuality_graph_widget
        
        self.attendance_dict = {}
        
        self.stack = QStackedWidget()
        
        cperiod = Period.str_to_period(time.ctime())
        self.other_years = sorted(set([str(att.period.year) for att in SCHOOL.attendance.attendance_data if att.period.year not in (cperiod.year, cperiod.year - 1)]))
        
        self.filter_views = {}
        self.scr_bar_values = []
        
        self.filter_data = [
            ["All (Staff)", "Prefects", "Teachers"],
            ["All (Timelines)", "Today", "This week", "This month", "This year", "Last year", "Last 5 years", "Last decade"] + self.other_years,
            ["Default (Display Format)", "Daily", "Weekly", "Monthly", "Yearly", "Dates (Categorised)", "Daily (Categorised)", "Monthly (Categorised)", "Yearly (Categorised)"]
        ]
        
        self.filter_combinations = [tuple(reversed(p)) for p in product(*reversed([range(len(l)) for l in self.filter_data]))]
        
        for comb in self.filter_combinations:
            widget = self._determine_filter_widget_type(comb)
            
            self.stack.addWidget(widget)
            
            self.filter_views[comb] = [widget, len(SCHOOL.attendance.attendance_data)]
            self.scr_bar_values.append(0)
        
        self.addWidget(self.stack)
        
        self.comm_signal.connect(self.add_new_attendance_log)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.time_label = QLabel()
        self.filter_widget = BaseWidget(QHBoxLayout)
        
        self.filter_widget.addStretch()
        self.filter_widget.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.filter_widget.addStretch()
        
        self.filter_comboboxes = []
        
        for index, f_data in enumerate(self.filter_data):
            filter = QComboBox()
            
            filter.addItems(f_data)
            filter.currentIndexChanged.connect(self._make_c_change_func(index))
            
            self.filter_widget.addWidget(filter, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.filter_comboboxes.append(filter)
        
        self.filter_comboboxes[0].setCurrentIndex(0)
        
        for i, attendance in enumerate(SCHOOL.attendance.attendance_data):
            self._add_attendance_log(attendance, i)
        
        self._layout.insertWidget(0, self.filter_widget)
        
        time_timer = QTimer(self.filter_widget)
        time_timer.timeout.connect(self._set_current_time)
        time_timer.start(1000)
        
        self.__init = False
    
    def _set_current_time(self):
        hr, min, sec = time.ctime().split()[3].split(":")
        
        self.time_label.setText(f"<span style='font-weight: bold; font-family: consolas; font-size: 25px'>{hr} : {min} : {sec}</span>")
    
    def _reveal_widget(self, dropdowns: list[DropdownLabeledField], target_widget: QWidget):
        if not dropdowns:
            self.scroll_to(target_widget)
            return

        dd = dropdowns[0]
        dd.setExpanded(True)
        
        QTimer.singleShot(
            0,
            lambda: self._reveal_widget(dropdowns[1:], target_widget)
        )
    
    def _determine_filter_widget_type(self, comb: tuple[int, ...]):
        return BaseListWidget(self.scroll_widget) if comb[1] in (0, 1) and comb[2] in (0, ) else BaseFilterCategoriesWidget(self.scroll_widget)
    
    def _add_attendance_entry(self, comb: tuple[int, ...], t_widget_entry: AttendanceEntry):
        if isinstance(t_widget_entry.staff, Teacher):
            t_widget = AttendanceTeacherEntryWidget(t_widget_entry)
        elif isinstance(t_widget_entry.staff, Prefect):
            t_widget = AttendancePrefectEntryWidget(t_widget_entry)
        else:
            raise TypeError(f"Type: {type(t_widget_entry.staff)} is not supported")
        
        parent_widg, _ = self.filter_views[comb]
        
        accepted, cls = self.filter(t_widget, comb)
        
        if accepted:
            parent_widg.addWidget(t_widget, cls)
        
        return t_widget
    
    def _make_c_change_func(self, index: int):
        def func(i):
            comb = tuple((c.currentIndex() if c_i != index else i) for c_i, c in enumerate(self.filter_comboboxes))
            widg, att_i = self.filter_views[comb]
            
            for att_entry in SCHOOL.attendance.attendance_data[att_i:]:
                self._add_attendance_entry(comb, att_entry)
            
            self.filter_views[comb][1] = len(SCHOOL.attendance.attendance_data)
            
            self.scr_bar_values[self.stack.currentIndex()] = self.scroll_widget.verticalScrollBar().value()
            
            self.stack.setCurrentWidget(widg)
            
            self.scroll_widget.verticalScrollBar().setValue(self.scr_bar_values[self.stack.currentIndex()])
        
        return func
    
    def _filter_category_fmt(self, entry_obj: BaseAttendanceEntryWidget, index: int, default: str | tuple[str, ...] | None):
        entry = entry_obj.data
        
        match index:
            case 0:
                return default
            case 1:
                return entry.period.day
            case 2:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                month_index = list(MONTHS_OF_THE_YEAR).index(entry.period.month)
                
                start_date = entry.period.date - day_index
                end_date = start_date + 6
                
                start_month = entry.period.month
                end_month = entry.period.month
                
                start_year = entry.period.year
                end_year = entry.period.year
                
                if start_date < 1:
                    if not month_index:
                        start_year -= 1
                    
                    start_month = list(MONTHS_OF_THE_YEAR)[month_index - 1]
                    start_date += MONTHS_OF_THE_YEAR[start_month]
                
                if end_date > MONTHS_OF_THE_YEAR[entry.period.month]:
                    if month_index == len(MONTHS_OF_THE_YEAR) - 1:
                        end_year += 1
                    
                    end_date = end_date % MONTHS_OF_THE_YEAR[entry.period.month]
                    end_month = list(MONTHS_OF_THE_YEAR)[(month_index + 1) % len(MONTHS_OF_THE_YEAR)]
                
                return f"{positionify(start_date)} {start_month} {start_year} - {positionify(end_date)} {end_month} {end_year}"
            case 3:
                return entry.period.month
            case 4:
                return entry.period.year
            case 5:
                return positionify(entry.period.date), entry.period.year, entry.period.month, entry.period.day
            case 6:
                return entry.period.day, entry.period.year, entry.period.month, positionify(entry.period.date)
            case 7:
                return entry.period.month, entry.period.year, entry.period.day, positionify(entry.period.date)
            case 8:
                return entry.period.year, entry.period.month, entry.period.day, positionify(entry.period.date)
        
        raise Exception()
    
    def _add_attendance_log(self, attendance_entry: AttendanceEntry, index=None):
        if isinstance(attendance_entry.staff, Teacher):
            self.attendance_chart_widget.teacher_data_changed()
            self.punctuality_graph_widget.teacher_data_changed()
        elif isinstance(attendance_entry.staff, Prefect):
            self.attendance_chart_widget.prefect_data_changed()
            self.punctuality_graph_widget.prefect_data_changed()
        else:
            raise TypeError(f"Type: {type(attendance_entry.staff)} is not supported")
        
        curr_widget = self.stack.currentWidget()
        
        if index is not None:
            widg_comb = None
            
            for comb, (widget, _) in self.filter_views.items():
                if widget == curr_widget:
                    widg_comb = comb
                    self.filter_views[comb][1] = len(SCHOOL.attendance.attendance_data)
                elif index < self.filter_views[comb][1]:
                    self.filter_views[comb][1] = index
            
            assert widg_comb
            
            widget = self._add_attendance_entry(widg_comb, attendance_entry)
            
            if not self.__init:
                self.scroll_to(widget, is_first=index==0)
        else:
            for comb, (widget, _) in self.filter_views.items():
                self._add_attendance_entry(comb, attendance_entry)
    
    def _random_period(self):
        period = Period.str_to_period(time.ctime())
        
        period.time.hour = random.randint(0, 24)
        period.time.minute = random.randint(0, 60)
        period.time.second = random.randint(0, 60)
        
        period.month = random.choice(list(MONTHS_OF_THE_YEAR))
        
        prev_date = period.date % MONTHS_OF_THE_YEAR[period.month]
        period.date = random.randint(1, MONTHS_OF_THE_YEAR[period.month])
        period.day = DAYS_OF_THE_WEEK[(DAYS_OF_THE_WEEK.index(period.day) + period.date - prev_date) % 7]
        
        period.year = random.randint(2000, 2030)
        
        return period
    
    def search_goto(self, sw: AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget | list[DropdownLabeledField | AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget]):
        if isinstance(sw, list):
            self._reveal_widget(sw[:-1], sw[-1])
        else:
            self.scroll_to(sw)
    
    def search_get_scope(self):
        parent_widget: BaseListWidget | BaseFilterCategoriesWidget = self.stack.currentWidget()
        
        if isinstance(parent_widget, BaseFilterCategoriesWidget):
            widgets: dict = parent_widget.getWidgets()
            
            return (
                sorted(
                    [
                        (
                            sw_list,
                            sw_list[-1].staff.name.full(),
                            (
                                sw_list[-1].staff.name.abbrev,
                                sw_list[-1].data.period.to_str(),
                                "Prefect" if isinstance(sw_list[-1].staff, Prefect) else "Teacher"
                                ),
                            [
                                sw_list[-1].staff.IUD,    
                                sw_list[-1].staff.name.third,
                                SCHOOL.posts[sw_list[-1].staff.post_id] if isinstance(sw_list[-1].staff, Prefect) else None,
                                f"{sw_list[-1].staff.cls.level.name.full()} {sw_list[-1].staff.cls.name}" if isinstance(sw_list[-1].staff, Prefect) else None
                                ] + (
                                    (list(set(flatten(sw_list[-1].staff.duties.values()))) + list(sw_list[-1].staff.duties))
                                    if isinstance(sw_list[-1].staff, Prefect) else
                                    ([s.name.full() for s in sw_list[-1].staff.subjects.values()] + [" ".join([f"{c.level.name.full()} {c.name}" for c in s.classes.values()]) for s in sw_list[-1].staff.subjects.values()] + list(flatten([[d for t, d, _ in s.get_periods() if t.id == sw_list[-1].staff.id] for s in sw_list[-1].staff.subjects.values()])))
                                    )
                        )
                        for sw_list in
                        widgets
                        ],
                    key=lambda params: params[1]
                    )
                )
        else:
            widgets: list[AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget] = parent_widget.getWidgets()
            
            return (
                sorted(
                    [
                        (
                            sw,
                            sw.staff.name.full(),
                            (
                                sw.staff.name.abbrev,
                                sw.data.period.to_str(),
                                "Prefect" if isinstance(sw.staff, Prefect) else "Teacher"
                                ),
                            [
                                sw.staff.IUD,    
                                sw.staff.name.third,
                                SCHOOL.posts[sw.staff.post_id] if isinstance(sw.staff, Prefect) else None,
                                f"{sw.staff.cls.level.name.full()} {sw.staff.cls.name}" if isinstance(sw.staff, Prefect) else None
                                ] + (
                                    (list(set(flatten(sw.staff.duties.values()))) + list(sw.staff.duties))
                                    if isinstance(sw.staff, Prefect) else
                                    ([s.name.full() for s in sw.staff.subjects.values()] + [" ".join([f"{c.level.name.full()} {c.name}" for c in s.classes.values()]) for s in sw.staff.subjects.values()] + list(flatten([[d for t, d, _ in s.get_periods() if t.id == sw.staff.id] for s in sw.staff.subjects.values()])))
                                    )
                        )
                        for sw in
                        widgets
                        ],
                    key=lambda params: params[1]
                    )
                )
    
    def filter(self, entry_obj: BaseAttendanceEntryWidget, comb: tuple[int, ...]):
        i1, i2, i3 = comb
        
        curr_period = Period.str_to_period(time.ctime())
        
        a_types = [(AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget), AttendancePrefectEntryWidget, AttendanceTeacherEntryWidget]
        
        if isinstance(entry_obj, a_types[i1]):
            entry = entry_obj.data
            
            if i2 == 0:
                return True, self._filter_category_fmt(entry_obj, i3, None)
            elif i2 == 1:
                return (
                    entry_obj.data.period.date == curr_period.date and entry_obj.data.period.month == curr_period.month and entry_obj.data.period.year == curr_period.year,
                    self._filter_category_fmt(entry_obj, i3, None)
                )
            elif i2 == 2:
                obj_day_index = DAYS_OF_THE_WEEK.index(entry_obj.data.period.day)
                cur_day_index = DAYS_OF_THE_WEEK.index(curr_period.day)
                
                return (
                    cur_day_index - obj_day_index == curr_period.date - entry_obj.data.period.date and abs(entry_obj.data.period.in_days() - curr_period.in_days()) < 7,
                    self._filter_category_fmt(entry_obj, i3, entry.period.day)
                )
            elif i2 == 3:
                return (
                    curr_period.month == entry_obj.data.period.month and entry_obj.data.period.year == curr_period.year,
                    self._filter_category_fmt(entry_obj, i3, f"{entry.period.day}, {positionify(entry.period.date)} {entry.period.month}")
                )
            elif i2 == 4:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 5:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 1 == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 6:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 5 <= entry_obj.data.period.year <= curr_period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            curr_period.year,
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            elif i2 == 7:
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    curr_period.year - 10 <= entry_obj.data.period.year <= curr_period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            curr_period.year,
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
            
            if 8 <= i2 <= 8 + len(self.other_years):
                day_index = DAYS_OF_THE_WEEK.index(entry.period.day)
                
                if entry.period.date - day_index < 1:
                    start_date = 1
                else:
                    start_date = entry.period.date - day_index
                
                if entry.period.date - day_index + 6 > MONTHS_OF_THE_YEAR[entry.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[entry.period.month]
                else:
                    end_date = entry.period.date - day_index + 6
                
                return (
                    int(self.other_years[i2 - 8]) == entry_obj.data.period.year,
                    self._filter_category_fmt(
                        entry_obj,
                        i3,
                        (
                            entry.period.month,
                            f"{positionify(start_date)} - {positionify(end_date)}" if start_date != end_date else positionify(start_date)
                        )
                    )
                )
        
        return False, None
    
    def add_new_attendance_log(self, IUD: str, period: Optional[Period] = None):
        if not GLOBAL_VARS.STAFF_IUD_REGISTRATION_ACTIVE:
            staff = next((staff for staff in list(SCHOOL.prefects.values()) + list(SCHOOL.teachers.values()) if staff.IUD == IUD), None)
            
            if staff is None:
                self.comm_system.send_message(f"UNREGISTERED")
                
                QMessageBox.warning(self.parent_widget, "CardScannerError", f"No staff is linked to this card (IUD: {IUD})")
                
                return
            else:
                if isinstance(staff, Prefect):
                    attendance_time_settings = SCHOOL.attendance.prefect_attendance_time_settings
                elif isinstance(staff, Teacher):
                    attendance_time_settings = SCHOOL.attendance.teacher_attendance_time_settings
            
            for k, v in self.cs_dbg_action_mapping.items():
                if k.lower() in ("period", IUD.lower()):
                    period = Period.str_to_period(v)
                
                if IUD.lower() == k.lower():
                    break
            else:
                period = period or Period.str_to_period(time.ctime())
            
            previous_check_in = next((entry.is_check_in for entry in staff.attendance if entry.period.date == period.date and entry.period.month == period.month and entry.period.year == period.year), None)
            cin, cout = attendance_time_settings.check_in_time, attendance_time_settings.check_out_time
            
            cin_interval = attendance_time_settings.check_in_border_interval_minutes
            cout_interval = attendance_time_settings.check_in_border_interval_minutes

            is_check_in, is_check_out = check_states(period.time, cin, cout, cin_interval, cout_interval)
            within_range = cin.in_minutes() - cin_interval <= period.time.in_minutes() <= cout.in_minutes() + cout_interval
            
            send_msg = ""
            
            if next((True for t_d in attendance_time_settings.timeline_dates if t_d[0].in_minutes() <= period.in_minutes() <= t_d[1].in_minutes()), False):
                if previous_check_in is not None:
                    if previous_check_in:
                        if is_check_in:
                            send_msg = "Check-In"
                            scan_failed_msg = "Cannot Check-In twice"
                        elif is_check_out:
                            scan_failed_msg = None
                        elif within_range:
                            send_msg = "Check-Out"
                            scan_failed_msg = "Cannot Check-Out during duty hours"
                        else:
                            send_msg = "Check-Out"
                            scan_failed_msg = "Check-Out time is too late"
                    else:
                        if is_check_in:
                            send_msg = "Check-In"
                            scan_failed_msg = "Cannot Check-In after Checking-Out"
                        elif is_check_out:
                            send_msg = "Check-Out"
                            scan_failed_msg = "Cannot Check-Out twice"
                        else:
                            send_msg = "Check-Out"
                            scan_failed_msg = "Check-Out time is too late"
                else:
                    if is_check_in:
                        scan_failed_msg = None
                    elif is_check_out:
                        send_msg = "Check-Out"
                        scan_failed_msg = "Cannot Check-Out without Checking-In"
                    elif within_range:
                        send_msg = "Check-Out"
                        scan_failed_msg = "Cannot Check-Out without Checking-In and the Check-Out time is also too early"
                    else:
                        send_msg = "Check-In"
                        scan_failed_msg = "Check-In time is too early"
            else:
                send_msg = "Attendance"
                scan_failed_msg = "Attendance is not within the valid attendance window"
            
            if scan_failed_msg:
                self.comm_system.send_message(f"UNSCANNED")
                
                QTimer.singleShot(
                    500,
                    lambda: self.comm_system.send_message(f"    Invalid     _    {send_msg}")
                )
                
                QMessageBox.warning(self.parent_widget, f"{send_msg.replace("-", "")}Error", scan_failed_msg)
                
                return
            
            entry = AttendanceEntry(period, staff, is_check_in)
            
            SCHOOL.attendance.attendance_data.append(entry)
            staff.attendance.append(entry)
            
            self._add_attendance_log(entry, len(SCHOOL.attendance.attendance_data) - 1)
            
            self.comm_system.send_message(f"SCANNED")
            QTimer.singleShot(
                500,
                lambda: self.comm_system.send_message(f"   Good{' morning' if is_check_in else "bye"}" + "_"+ (" " * int(8 - (len(entry.staff.name.short()) / 2))) + f"{entry.staff.name.short()}")
            )
            
            self.window().saved_state_changed.emit(True)
    
    def keyPressEvent(self, a0):
        period = Period.str_to_period(time.ctime())
        
        for k, v in self.kb_dbg_action_mapping.items():
            if k.lower() == "period":
                try:
                    period = Period.str_to_period(v)
                except Exception as e:
                    print(e)
            elif a0.text() == k:
                self.add_new_attendance_log(v, period)
        
        return super().keyPressEvent(a0)

class AttendanceBarWidget(BaseDataDisplayWidget):
    def __init__(self, parent_window: QMainWindow):
        super().__init__()
        
        self.parent_window = parent_window
    
    def _get_filter_widgets(self):
        self.prefect_info_widget = BarWidget("Cummulative School Prefect Attendance", "School Prefects", "Yearly Attendance (%)")
        self.prefect_info_widget.bar_canvas.axes.set_ylim(top=100)
        
        self.dtd_widget = BaseWidget()
        self.teacher_dep_widgets: dict[ID, BarWidget] = {}
        
        return {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Attendance", self.prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            "Teachers": LabeledField("Departmental Attendance", self.dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
    
    def add_subject(self, subjectID: ID):
        subject = SCHOOL.subjects[subjectID]
        
        bar_widget = self.teacher_dep_widgets[subjectID] = BarWidget(f"Cummulative {subject.name.full()} Department Attendance", f"{subject.name.full()} Department Teachers", "Yearly Attendance (%)")
        bar_widget.bar_canvas.axes.set_ylim(top=100)
        
        self.dtd_widget.addWidget(bar_widget)
    
    def delete_subject(self, subjectID: ID):
        if subjectID not in self.teacher_dep_widgets:
            return
        
        widget = self.teacher_dep_widgets.pop(subjectID)
        
        self.dtd_widget.removeWidget(widget)
        widget.deleteLater()
    
    def prefect_data_changed(self):
        self.prefect_info_widget.clear()
        
        prefect_data = {}
        
        for prefect in SCHOOL.prefects.values():
            p_attendance = self.get_percentage_attendance(prefect)
            
            if p_attendance is not None:
                prefect_data[prefect.id] = prefect.name.short(), p_attendance
        
        for index, (name, data) in enumerate(prefect_data.values()):
            self.prefect_info_widget.add_data(name, list(get_named_colors_mapping().values())[index], ([name], [data]))
    
    def teacher_data_changed(self):
        teacher_data: dict[ID, list[tuple[list[str], list[int]]]] = {}
        
        for teacher in SCHOOL.teachers.values():
            for subject in teacher.subjects.values():
                att_data = self.get_percentage_attendance(teacher)
                
                if att_data:
                    t_data = [teacher.name.full()], [att_data]
                
                    if subject.id not in teacher_data:
                        teacher_data[subject.id] = [t_data]
                    
                    teacher_data[subject.id].append(t_data)
                    
                    if subject.id not in self.teacher_dep_widgets:
                        self.add_subject(subject.id)
        
        if teacher_data:
            index = 0
            
            for subj_id, total_teacher_data in teacher_data.items():
                widget = self.teacher_dep_widgets[subj_id]
                widget.clear()
                
                for t_data in total_teacher_data:
                    index += 1
                    widget.add_data(SCHOOL.subjects[subj_id].name.full(), list(get_named_colors_mapping().values())[index], t_data, False)
    
    def get_percentage_attendance(self, staff: Staff):
        _, plot_data = self.parent_window.staff_widget.widgets[staff.id].get_staff_attendance_data()
        
        if plot_data:
            return sum(plot_data.values()) / len(plot_data)

class PunctualityGraphWidget(BaseDataDisplayWidget):
    def _get_filter_widgets(self):
        self.prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
        self.dtd_widget = BaseWidget()
        
        self.teacher_info_widgets: dict[ID, GraphWidget] = {}
        
        return {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Punctuality", self.prefect_info_widget),
            "Teachers": LabeledField("Departmental Punctuality", self.dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
    
    def add_subject(self, subjectID: ID):
        subject = SCHOOL.subjects[subjectID]
        
        graph_widget = self.teacher_info_widgets[subjectID] = GraphWidget(f"{subject.name.full()} Teachers Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
        self.dtd_widget.addWidget(graph_widget)
    
    def delete_subject(self, subjectID: ID):
        if subjectID not in self.teacher_info_widgets:
            return
        
        widget = self.teacher_info_widgets.pop(subjectID)
        
        self.dtd_widget.removeWidget(widget)
        widget.deleteLater()
    
    def prefect_data_changed(self):
        prefects_data = []
        self.prefect_info_widget.clear()
        
        for prefect in SCHOOL.prefects.values():
            data = self.get_punctuality_data(prefect)
            
            if data is not None:
                prefects_data.append(data)
        
        if prefects_data:
            for index, (name, prefect_data) in enumerate(prefects_data):
                self.prefect_info_widget.plot(None, prefect_data, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def teacher_data_changed(self):
        teacher_data = {}
        
        for teacher in SCHOOL.teachers.values():
            for subject in teacher.subjects.values():
                data = self.get_punctuality_data(teacher)
                
                if data is not None:
                    teacher_data[subject.id] = data
                
                if subject.id not in self.teacher_info_widgets:
                    self.add_subject(subject.id)
                
                self.teacher_info_widgets[subject.id].clear()
        
        if teacher_data:
            for index, (dep_id, (name, info)) in enumerate(teacher_data.items()):
                self.teacher_info_widgets[dep_id].plot(None, info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def get_punctuality_data(self, staff: Staff):
        if isinstance(staff, Teacher):
            attendance_time_settings = SCHOOL.attendance.teacher_attendance_time_settings
            working_days = list(set(flatten([[d for t, d, _ in s.get_periods() if t.id == staff.id] for s in staff.subjects.values()])))
        elif isinstance(staff, Prefect):
            attendance_time_settings = SCHOOL.attendance.prefect_attendance_time_settings
            working_days = list(staff.duties)
        else:
            raise Exception()
        
        y_plot_points = [attendance_time_settings.check_in_time.in_minutes() - attendance.period.time.in_minutes() for attendance in staff.attendance if BaseDataDisplayWidget.is_entry_countable(attendance, working_days, attendance_time_settings.timeline_dates) is not None]
        
        if y_plot_points:
            return staff.name.short(), y_plot_points

