import random
from itertools import product

from ..base_widgets import *
from ..data_display_widgets import *

from .entry_widgets import *
from .option_widgets import *


class AttendanceWidget(BaseScrollListWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, parent_widget: TabViewWidget, attendance_chart_widget: "AttendanceBarWidget", punctuality_graph_widget: "PunctualityGraphWidget", comm_system: BaseCommSystem, saved_state_changed: pyBoundSignal, card_scanner_widget: CardScanScreenWidget):
        super().__init__()
        
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
        self.saved_state_changed = saved_state_changed
        self.card_scanner_widget = card_scanner_widget
        
        self.attendance_chart_widget = attendance_chart_widget
        self.punctuality_graph_widget = punctuality_graph_widget
        
        self.attendance_dict = {}
        
        self.create_time_labels()
        
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
        
        self.main_layout.addWidget(self.stack)
        
        self.main_layout.addStretch()
        
        self.comm_signal.connect(self.add_new_attendance_log)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.time_label = QLabel()
        self.filter_widget, filter_layout = create_widget(None, QHBoxLayout)
        
        filter_layout.addStretch()
        filter_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignCenter)
        filter_layout.addStretch()
        
        
        self.filter_comboboxes = []
        
        for index, f_data in enumerate(self.filter_data):
            filter = QComboBox()
            
            filter.addItems(f_data)
            filter.currentIndexChanged.connect(self._make_c_change_func(index))
            
            filter_layout.addWidget(filter, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.filter_comboboxes.append(filter)
        
        self.filter_comboboxes[0].setCurrentIndex(0)
        
        for i, attendance in enumerate(SCHOOL.attendance.attendance_data):
            self._add_attendance_log(attendance, i)
        
        self._layout.insertWidget(0, self.filter_widget)
        
        time_timer = QTimer(self.filter_widget)
        time_timer.timeout.connect(self._set_current_time)
        time_timer.start(1000)
    
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
        
        self.saved_state_changed.emit(False)
        
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
            widgets: dict = parent_widget.get_widgets()
            
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
                                sw_list[-1].staff.name.other,
                                sw_list[-1].staff.post_name if isinstance(sw_list[-1].staff, Prefect) else None,
                                f"{sw_list[-1].staff.cls.level.name.full()} {sw_list[-1].staff.cls.name}" if isinstance(sw_list[-1].staff, Prefect) else None
                                ] + (
                                    (list(set(flatten(sw_list[-1].staff.duties.values()))) + list(sw_list[-1].staff.duties))
                                    if isinstance(sw_list[-1].staff, Prefect) else
                                    ([s.name.full() for s in sw_list[-1].staff.subjects.values()] + [" ".join([f"{c.level.name.full()} {c.name}" for c in s.classes.values()]) for s in sw_list[-1].staff.subjects.values()] + list(flatten([[d for d, _ in s.get_periods()] for s in sw_list[-1].staff.subjects.values()])))
                                    )
                        )
                        for sw_list in
                        widgets
                        ],
                    key=lambda params: params[1]
                    )
                )
        else:
            widgets: list[AttendancePrefectEntryWidget | AttendanceTeacherEntryWidget] = parent_widget.get_widgets()
            
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
                                sw.staff.name.other,
                                sw.staff.post_name if isinstance(sw.staff, Prefect) else None,
                                f"{sw.staff.cls.level.name.full()} {sw.staff.cls.name}" if isinstance(sw.staff, Prefect) else None
                                ] + (
                                    (list(set(flatten(sw.staff.duties.values()))) + list(sw.staff.duties))
                                    if isinstance(sw.staff, Prefect) else
                                    ([s.name.full() for s in sw.staff.subjects.values()] + [" ".join([f"{c.level.name.full()} {c.name}" for c in s.classes.values()]) for s in sw.staff.subjects.values()] + list(flatten([[d for d, _ in s.get_periods()] for s in sw.staff.subjects.values()])))
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
    
    def create_time_labels(self):
        time_widget, time_layout = create_widget(None, QHBoxLayout)
        
        teacher_widget, teacher_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cit_teacher_widget, cit_teacher_layout = create_widget(None, QHBoxLayout)
        cot_teacher_widget, cot_teacher_layout = create_widget(None, QHBoxLayout)
        
        it_time_label = QLabel(SCHOOL.attendance.teacher_cit.to_str().replace(":", " : "))
        it_time_label.setProperty("class", "labeled-widget")
        
        ot_time_label = QLabel(SCHOOL.attendance.teacher_cot.to_str().replace(":", " : "))
        ot_time_label.setProperty("class", "labeled-widget")
        
        cit_teacher_layout.addWidget(QLabel(f'Teacher CIT'))
        cit_teacher_layout.addWidget(it_time_label)
        
        cot_teacher_layout.addWidget(QLabel(f'Teacher COT'))
        cot_teacher_layout.addWidget(ot_time_label)
        
        teacher_layout.addWidget(cit_teacher_widget)
        teacher_layout.addWidget(cot_teacher_widget)
        
        
        base_widget, base_layout = create_widget(None, QHBoxLayout)
        
        prefect_widget, prefect_layout = create_widget(self.main_layout, QHBoxLayout)
        
        cit_prefect_widget, cit_prefect_layout = create_widget(None, QHBoxLayout)
        cot_prefect_widget, cot_prefect_layout = create_widget(None, QHBoxLayout)        
             
        it_time_label = QLabel(SCHOOL.attendance.prefect_cit.to_str().replace(":", " : "))
        it_time_label.setProperty("class", "labeled-widget")
        
        ot_time_label = QLabel(SCHOOL.attendance.prefect_cot.to_str().replace(":", " : "))
        ot_time_label.setProperty("class", "labeled-widget")
        
        cit_prefect_layout.addWidget(it_time_label)
        cit_prefect_layout.addWidget(QLabel(f'Prefect CIT'))
        
        cot_prefect_layout.addWidget(ot_time_label)
        cot_prefect_layout.addWidget(QLabel(f'Prefect COT'))
        
        prefect_layout.addWidget(cit_prefect_widget)
        prefect_layout.addWidget(cot_prefect_widget)
        
        
        time_layout.addWidget(teacher_widget, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        time_layout.addWidget(base_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        time_layout.addWidget(prefect_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        self.main_layout.insertWidget(0, time_widget)
    
    def add_new_attendance_log(self, IUD: str, period: Period | None = None):
        if not self.card_scanner_widget.just_scanned:
            staff = next((prefect for _, prefect in SCHOOL.prefects.items() if prefect.IUD == IUD), None)
            
            if staff is None:
                staff = next((teacher for _, teacher in SCHOOL.teachers.items() if teacher.IUD == IUD), None)
                
                if staff is None:
                    self.comm_system.send_message(f"UNREGISTERED")
                    
                    QMessageBox.warning(self.parent_widget, "CardScannerError", f"No staff is linked to this card (IUD: {IUD})")
                    
                    return
            
            for k, v in self.cs_dbg_action_mapping.items():
                if k.lower() in ("period", IUD.lower()):
                    period = Period.str_to_period(v)
                
                if IUD.lower() == k.lower():
                    break
            else:
                period = period or Period.str_to_period(time.ctime())
            
            previous_check_in = next((entry.is_check_in for entry in staff.attendance if entry.period.date == period.date and entry.period.month == period.month and entry.period.year == period.year), None)
            cin, cout = (SCHOOL.attendance.prefect_cit, SCHOOL.attendance.prefect_cot) if isinstance(staff, Prefect) else (SCHOOL.attendance.teacher_cit, SCHOOL.attendance.teacher_cot)
            
            cin_interval = SCHOOL.attendance.prefect_cin_border_interval_minutes if isinstance(staff, Prefect) else SCHOOL.attendance.teacher_cin_border_interval_minutes
            cout_interval = SCHOOL.attendance.prefect_cout_border_interval_minutes if isinstance(staff, Prefect) else SCHOOL.attendance.teacher_cout_border_interval_minutes

            is_check_in, is_check_out = check_states(period.time, cin, cout, cin_interval, cout_interval)
            within_range = cin.in_minutes() - cin_interval <= period.time.in_minutes() <= cout.in_minutes() + cout_interval
            
            send_msg = ""
            
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
            
            if scan_failed_msg:
                self.comm_system.send_message(f"UNSCANNED")
                
                QTimer.singleShot(
                    500,
                    lambda: self.comm_system.send_message(f"    Invalid     _    {send_msg}")
                )
                
                QMessageBox.warning(self.parent_widget, f"{send_msg.replace("-", "")}Error", scan_failed_msg)
                
                return
            
            self.window().saved_state_changed.emit(True)
            
            entry = AttendanceEntry(period, staff, is_check_in)
            
            SCHOOL.attendance.attendance_data.append(entry)
            staff.attendance.append(entry)
            
            self._add_attendance_log(entry, len(SCHOOL.attendance.attendance_data) - 1)
            
            self.comm_system.send_message(f"SCANNED")
            QTimer.singleShot(
                500,
                lambda: self.comm_system.send_message(f"   Good{' morning' if is_check_in else "bye"}" + "_"+ (" " * int(8 - (len(entry.staff.name.abbrev) / 2))) + f"{entry.staff.name.abbrev}")
            )
    
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

class StaffListWidget(BaseScrollListWidget):
    def __init__(self, parent_widget: TabViewWidget, comm_system: BaseCommSystem, card_scanner_widget: CardScanScreenWidget, staff_data_widget: StaffDataWidget):
        super().__init__()
        
        self.parent_widget = parent_widget
        self.comm_system = comm_system
        self.card_scanner_widget = card_scanner_widget
        self.staff_data_widget = staff_data_widget
        
        self.curr_filter = None
        
        prefects = lambda: sorted([(k, v) for k, v in SCHOOL.prefects.items()], key=lambda params: params[1].name.full())
        teachers = lambda: sorted([(k, v) for k, v in SCHOOL.teachers.items()], key=lambda params: params[1].name.full())
        boths = lambda: sorted(prefects() + teachers(), key=lambda params: params[1].name.full())
        prefects_first = lambda: prefects() + teachers()
        teachers_first = lambda: teachers() + prefects()
        
        self._filter_funcs: dict[str, Callable] = {}
        self._filter_layouts: dict[str, QVBoxLayout] = {}
        self.all_staff_widgets: dict[str, dict[str, StaffListPrefectEntryWidget | StaffListTeacherEntryWidget]] = {}
        
        both_func = lambda staff: StaffListTeacherEntryWidget if isinstance(staff, Teacher) else StaffListPrefectEntryWidget
        
        self.widgets = {}
        
        self.get_filtered_widgets("Default", boths, both_func)
        self.get_filtered_widgets("Prefects Only", prefects, lambda staff: StaffListPrefectEntryWidget if isinstance(staff, Prefect) else None)
        self.get_filtered_widgets("Teachers Only", teachers, lambda staff: StaffListTeacherEntryWidget if isinstance(staff, Teacher) else None)
        self.get_filtered_widgets("Prefects First", prefects_first, both_func)
        self.get_filtered_widgets("Teachers First", teachers_first, both_func)
        
        for i, staff_widget in enumerate(self.widgets.copy().values()):
            staff_widget.setVisible(i == 0)
            self.main_layout.addWidget(staff_widget)
        
        self.filter_widget, filter_layout = create_widget(None, QHBoxLayout)
        
        self.filter_cb = QComboBox()
        self.filter_cb.addItems(list(self.widgets))
        self.filter_cb.currentIndexChanged.connect(self.filter)
        
        filter_layout.addWidget(self.filter_cb, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._layout.insertWidget(0, self.filter_widget)
        
        self.filter(0)
    
    def get_filtered_widgets(
        self,
        filter_key: str,
        
        staff_list_callback: Callable[[], list[tuple[str, Prefect | Teacher]]],
        entry_type_callback: Callable[[Prefect | Teacher], type[StaffListTeacherEntryWidget] | type[StaffListTeacherEntryWidget]],
    ):
        widget = QWidget()
        layout = QVBoxLayout()
        
        widget.setLayout(layout)
        
        self._filter_funcs[filter_key] = staff_list_callback, entry_type_callback
        self._filter_layouts[filter_key] = layout
        
        if filter_key not in self.all_staff_widgets:
            self.all_staff_widgets[filter_key] = {}
        
        self.widgets[filter_key] = widget
    
    def search_goto(self, sw: StaffListPrefectEntryWidget | StaffListTeacherEntryWidget):
        self.scroll_to(sw)
    
    def search_get_scope(self):
        return (
            sorted(
                [
                    (
                        sw,
                        sw.staff.name.full(),
                        (
                            sw.staff.name.abbrev,
                            sw.staff.IUD,
                            "Prefect" if isinstance(sw.staff, Prefect) else "Teacher"
                            ),
                        [
                            sw.staff.name.other,
                            sw.staff.post_name if isinstance(sw.staff, Prefect) else None,
                            f"{sw.staff.cls.level.name.full()} {sw.staff.cls.name}" if isinstance(sw.staff, Prefect) else None
                            ] + (
                                (list(set(flatten(sw.staff.duties.values()))) + list(sw.staff.duties))
                                if isinstance(sw.staff, Prefect) else
                                ([s.name.full() for s in sw.staff.subjects.values()] + [" ".join([f"{c.level.name.full()} {c.name}" for c in s.classes.values()]) for s in sw.staff.subjects.values()] + list(flatten([[d for d, _ in s.get_periods()] for s in sw.staff.subjects.values()])))
                                )
                        )
                    for sw in
                    self.all_staff_widgets[self.curr_filter].values()
                    if (
                        self.filter_cb.currentIndex() == 0 or
                        (isinstance(sw.staff, Prefect) and self.filter_cb.currentIndex() == 1) or
                        (sw.staff.id in SCHOOL.teachers and self.filter_cb.currentIndex() == 2)
                        )
                    ],
                key=lambda params: params[1]
                )
            )
    
    def filter(self, index: int):
        for i, (f_type, staff_widget) in enumerate(self.widgets.items()):
            staff_widget.setVisible(index == i)
            
            if index == i:
                self.curr_filter = f_type
    
    def add_staff(self, staff: Prefect | Teacher):
        for f_key, staff_maps in self.all_staff_widgets.items():
            layout = self._filter_layouts[f_key]
            staff_list_callback, entry_type_callback = self._filter_funcs[f_key]
            
            entry_type = entry_type_callback(staff)
            
            if entry_type is not None:
                staff_widget = entry_type(
                    self.parent_widget,
                    staff,
                    self.comm_system,
                    self.card_scanner_widget,
                    self.staff_data_widget
                )
                
                index = next(i for i, (k, _) in enumerate(staff_list_callback()) if k == staff.id)
                
                layout.insertWidget(index, staff_widget)
                
                _temp_maps = list(staff_maps.items())
                _temp_maps.insert(index, (staff.id, staff_widget))
                
                staff_maps.clear()
                staff_maps.update(dict(_temp_maps))
    
    def delete_staff(self, staff: Prefect | Teacher):
        for f_key, staff_maps in self.all_staff_widgets.items():
            if staff.id in staff_maps:
                widget = staff_maps.pop(staff.id)
                self._filter_layouts[f_key].removeWidget(widget)

class AttendanceBarWidget(BaseDataDisplayWidget):
    def __init__(self, staff_data_widget: StaffDataWidget):
        super().__init__()
        
        self.staff_data_widget = staff_data_widget
    
    def _get_filter_widgets(self):
        self.prefect_info_widget = BarWidget("Cummulative School Prefect Attendance", "School Prefects", "Yearly Attendance (%)")
        self.prefect_info_widget.bar_canvas.axes.set_ylim(top=100)
        
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        self.teacher_dep_widgets = {}
        
        for teacher in SCHOOL.teachers.values():
            for subject in teacher.subjects.values():
                if subject.id not in self.teacher_dep_widgets:
                    self.teacher_dep_widgets[subject.id] = BarWidget(f"Cummulative {subject.name.full()} Department Attendance", f"{subject.name.full()} Department Teachers", "Yearly Attendance (%)")
                    self.teacher_dep_widgets[subject.id].bar_canvas.axes.set_ylim(top=100)
                    
                    dtd_layout.addWidget(self.teacher_dep_widgets[subject.id])
        
        return {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Attendance", self.prefect_info_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum),
            "Teachers": LabeledField("Departmental Attendance", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
    
    def prefect_data_changed(self):
        self.prefect_info_widget.clear()
        
        prefect_data = {}
        
        for prefect in SCHOOL.prefects.values():
            p_attendance = self.get_percentage_attendance(prefect)
            
            if p_attendance is not None:
                prefect_data[prefect.id] = prefect.name.abbrev, p_attendance
        
        for index, (name, data) in enumerate(prefect_data.values()):
            self.prefect_info_widget.add_data(name, list(get_named_colors_mapping().values())[index], ([name], [data]))
    
    def teacher_data_changed(self):
        teacher_data: dict[tuple[str, str], list[tuple[list[str], list[int]]]] = {}
        
        for teacher in SCHOOL.teachers.values():
            for subject in teacher.subjects.values():
                att_data = self.get_percentage_attendance(teacher)
                
                if att_data:
                    t_data = [teacher.name.full()], [att_data]
                
                    if subject.id not in teacher_data:
                        teacher_data[subject.id] = [t_data]
                    
                    teacher_data[subject.id].append(t_data)
        
        if teacher_data:
            index = 0
            
            for (dep_id, dep_name), total_teacher_data in teacher_data.items():
                widget = self.teacher_dep_widgets[dep_id]
                widget.clear()
                
                for t_data in total_teacher_data:
                    index += 1
                    widget.add_data(dep_name, list(get_named_colors_mapping().values())[index], t_data, False)
    
    def get_percentage_attendance(self, staff: Staff):
        _, plot_data = self.staff_data_widget.get_staff_attendance_data(staff)
        
        if plot_data:
            return sum(plot_data.values()) / len(plot_data)

class PunctualityGraphWidget(BaseDataDisplayWidget):
    def __init__(self, staff_data_widget: StaffDataWidget):
        super().__init__()
        
        self.staff_data_widget = staff_data_widget
    
    def _get_filter_widgets(self):
        self.prefect_info_widget = GraphWidget("Prefects Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
        dtd_widget, dtd_layout = create_widget(None, QVBoxLayout)
        
        self.teacher_info_widgets = {}
        for teacher in SCHOOL.teachers.values():
            for subject in teacher.subjects.values():
                if subject.id not in self.teacher_info_widgets:
                    self.teacher_info_widgets[subject.id] = GraphWidget(f"{subject.name.full()} Teachers Punctuality Graph", "Time Interval (Weeks)", "Punctuality (Hours)")
                    
                    dtd_layout.addWidget(self.teacher_info_widgets[subject.id])
        
        return {
            "All": ("Prefects", "Teachers"),
            "Prefects": LabeledField("Prefect Punctuality", self.prefect_info_widget),
            "Teachers": LabeledField("Departmental Punctuality", dtd_widget, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        }
    
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
                
                self.teacher_info_widgets[subject.id].clear()
        
        if teacher_data:
            for index, (dep_id, (name, info)) in enumerate(teacher_data.items()):
                self.teacher_info_widgets[dep_id].plot(None, info, label=name, marker='o', color=list(get_named_colors_mapping().values())[index])
    
    def get_punctuality_data(self, staff: Staff):
        if isinstance(staff, Teacher):
            timeline_dates = SCHOOL.attendance.teacher_timeline_dates
            cit = SCHOOL.attendance.teacher_cit
            working_days = list(set(flatten([[d for d, _ in s.get_periods()] for s in staff.subjects.values()])))
        elif isinstance(staff, Prefect):
            timeline_dates = SCHOOL.attendance.prefect_timeline_dates
            cit = SCHOOL.attendance.prefect_cit
            working_days = list(staff.duties)
        else:
            raise Exception()
        
        y_plot_points = [cit.in_minutes() - attendance.period.time.in_minutes() for attendance in staff.attendance if BaseDataDisplayWidget.is_entry_countable(attendance, working_days, timeline_dates) is not None]
        
        if y_plot_points:
            return staff.name.abbrev, y_plot_points


