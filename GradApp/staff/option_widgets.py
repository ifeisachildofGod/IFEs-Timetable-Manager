
from ..base_widgets import *
from ..data_display_widgets import *


class StaffDataWidget(BaseOptionsWidget):
    def __init__(self, data: AppData, parent_widget: TabViewWidget):
        super().__init__(parent_widget, "scrollable")
        
        self.data = data
        
        self.staff_working_days = {}
        
        for prefect in self.data.prefects.values():
            self.staff_working_days[prefect.id] = list(prefect.duties)
        
        for teacher in self.data.teachers.values():
            self.staff_working_days[teacher.id] = list(set(flatten([[d for d, _ in s.get_periods()] for s in teacher.subjects])))
        
        self.attendance_amt_widget = QLabel()
        
        staff_data_widget, self.staff_data_layout = create_widget(None, QVBoxLayout)
        
        self.punctuality_widget: GraphWidget | None = None
        
        self.attendance_widget = BarWidget("", "Time (Weeks)", "Attendance (%)")
        self.attendance_widget.bar_canvas.axes.set_ylim(0, 110)
        
        self.punctuality_widget = GraphWidget("", "Scan Interval", "Punctuality (Minutes)")
        
        stats_widget, stats_layout = create_scrollable_widget(None, QHBoxLayout) ; stats_layout.setContentsMargins(50, 20, 50, 20)
        chart_widget, chart_layout = create_widget(None, QVBoxLayout) ; chart_layout.setContentsMargins(10, 0, 10, 0)
        
        stats_widget.setMinimumHeight(200)
        stats_layout.setSpacing(150)
        
        stats_layout.addWidget(staff_data_widget, alignment=Qt.AlignmentFlag.AlignTop, stretch=5)
        stats_layout.addWidget(self.attendance_amt_widget, alignment=Qt.AlignmentFlag.AlignTop, stretch=5)
        
        chart_layout.addWidget(self.attendance_widget)
        chart_layout.addWidget(self.punctuality_widget)
        
        self.main_layout.addWidget(LabeledField("General Information", stats_widget))
        self.main_layout.addWidget(LabeledField("Graphs and Charts", chart_widget))
    
    def get_staff_attendance_data(self, staff: Staff):
        if isinstance(staff, Teacher):
            timeline_dates = self.data.teacher_timeline_dates
        elif isinstance(staff, Prefect):
            timeline_dates = self.data.prefect_timeline_dates
        else:
            raise Exception()
        
        weeks_data = {}
        
        for attendance in staff.attendance:
            if BaseDataDisplayWidget.is_entry_countable(attendance, self.staff_working_days[staff.id], timeline_dates) is not None:
                curr_index = DAYS_OF_THE_WEEK.index(attendance.period.day)
                
                days = self.staff_working_days[staff.id]
                
                if attendance.period.date - curr_index < 1:
                    start_date = 1
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) < abs(attendance.period.date - curr_index) + 1)]
                else:
                    start_date = attendance.period.date - curr_index
                
                if attendance.period.date - curr_index + 6 > MONTHS_OF_THE_YEAR[attendance.period.month]:
                    end_date = MONTHS_OF_THE_YEAR[attendance.period.month]
                    days = [day for day in days if not (DAYS_OF_THE_WEEK.index(day) > MONTHS_OF_THE_YEAR[attendance.period.month] - (attendance.period.date - curr_index))]
                else:
                    end_date = attendance.period.date - curr_index + 6
                
                if start_date != end_date:
                    name_key = f"{attendance.period.month} {attendance.period.year}\n{positionify(start_date)} to {positionify(end_date)}"
                else:
                    name_key = f"{attendance.period.year}\n{positionify(start_date)} {attendance.period.month}"
                
                if days:
                    if name_key not in weeks_data:
                        weeks_data[name_key] = [0, len(days)]
                    
                    weeks_data[name_key][0] += 1
        
        return weeks_data, {key: amt_attended / total * 100 for key, (amt_attended, total) in weeks_data.items()}
    
    def get_staff_punctuality_data(self, staff: Staff):
        if isinstance(staff, Teacher):
            timeline_dates = self.data.teacher_timeline_dates
            cit = self.data.teacher_cit
            working_days = list(set(flatten([[d for d, _ in s.get_periods()] for s in staff.subjects.values()])))
        elif isinstance(staff, Prefect):
            timeline_dates = self.data.prefect_timeline_dates
            cit = self.data.prefect_cit
            working_days = list(staff.duties)
        else:
            raise Exception()
        
        full_y_plot_points = []
        for index, day in enumerate(working_days):
            y_plot_points = [cit.in_minutes() - attendance.period.time.in_minutes() for attendance in staff.attendance if BaseDataDisplayWidget.is_entry_countable(attendance, [day], timeline_dates) is not None]
            
            if y_plot_points:
                full_y_plot_points.append([index, day, y_plot_points])
        
        return full_y_plot_points
    
    def set_self(self, staff):
        super().set_self(staff)
        
        clear_layout(self.staff_data_layout)
        
        if isinstance(staff, Teacher):
            bar_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s Monthly Cummulative Punctuality Graph"
            staff_list = list(self.data.teachers)
            staff_position_data = None
            cls = None
        elif isinstance(staff, Prefect):
            bar_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Cummulative Attendance Chart"
            graph_title = f"{staff.name.sur} {staff.name.first}'s ({staff.post_name}) Monthly Average Punctuality Graph"
            staff_list = list(self.data.prefects)
            staff_position_data = "Post", staff.post_name
            cls = staff.cls.name
        else:
            raise Exception()
        
        self.attendance_widget.clear()
        self.punctuality_widget.clear()
        
        self.attendance_widget.set_title(bar_title)
        self.punctuality_widget.set_title(graph_title)
        
        color = list(get_named_colors_mapping().values())[staff_list.index(staff.id) % len(list(get_named_colors_mapping().values()))]
        
        weeks_data, plot_data = self.get_staff_attendance_data(staff)
        
        self.attendance_widget.add_data(f"{staff.name.full()} Attendance Data", color, plot_data)
        
        full_y_plot_points = self.get_staff_punctuality_data(staff)
        
        for index, day, y_plot_points in full_y_plot_points:
            self.punctuality_widget.plot(None, y_plot_points, label=day, marker='o', color=list(get_named_colors_mapping().values())[index + 200])
        
        full_y_plot_points = list(flatten([p for _, _, p in full_y_plot_points]))
        
        if full_y_plot_points:
            score_list = [1 + int(p) / 60 for p in full_y_plot_points]
            
            p_score_factor = sum(score_list) / len(score_list)
            
            r = max(min((1 - (p_score_factor)) * 255, 255), 0)
            g = max(min(p_score_factor * 255, 255), 0)
            b = 10
        else:
            r = g = b = 255
        
        cins = [att.period.time.in_seconds() for att in staff.attendance if att.is_check_in]
        avg_cit = Time(0, 0, sum(cins) / len(cins) if cins else 0)
        avg_cit.normalize()
        avg_cit.second = int(avg_cit.second)
        
        couts = [att.period.time.in_seconds() for att in staff.attendance if not att.is_check_in]
        avg_cot = Time(0, 0, sum(couts) / len(couts) if couts else 0)
        avg_cot.normalize()
        avg_cot.second = int(avg_cot.second)
        
        disabled_color = THEME_MANAGER.pallete_get("disabled")
        
        self.attendance_amt_widget.setText(
            f"""
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Total Attended:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(sum(amt_attended for amt_attended, _ in weeks_data.values())) if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Attendance:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {str(int(sum(list(plot_data.values())) / len(plot_data))) + "%" if plot_data else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Punctuality Score:  </span>
                <span style='font-size: 15px; font-weight: 900; color: rgb({r}, {g}, {b});'>
                    {round(p_score_factor, 2) if full_y_plot_points else "No Data"}
                </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-in Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cit.to_str() if cins else "No Data"}
                    </span>
            </span>
            <br>
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Avg Check-out Time:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>
                        {avg_cot.to_str() if couts else "No Data"}
                    </span>
            </span>
            <br>
            """)
        
        staff_data_base_content = f"""
            <span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Name:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>{staff.name.full()}</span>
            </span>
            <br>
            
            {"""<span>
                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>{staff_position_data[0]}:  </span>
                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>{staff_position_data[1]}</span>
            </span>""" if staff_position_data is not None else ""}
        """
        if cls:
            staff_data_base_content += f"""
                <br>
                <span>
                    <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>Class:  </span>
                    <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>{cls}</span>
                </span>
            """
        
        self.staff_data_layout.addWidget(QLabel(staff_data_base_content))
        
        duties_widget, duties_layout = create_widget(None, QVBoxLayout)
        
        if isinstance(staff, Teacher):
            duty_days_map: dict[str, QLabel] = {}
            
            for subject in staff.subjects.values():
                for day, _ in subject.get_periods():
                    if day not in duty_days_map:
                        duty_days_map[day] = QLabel()
                        duties_layout.addWidget(LabeledField(day, duty_days_map[day]))
                    
                    duty_days_map[day].setText(
                        duty_days_map[day].text() + f"""
                            <span>
                                <span style='font-size: 20px; font-weight: 500; color: {disabled_color};'>{subject.cls.name}:  </span>
                                <span style='font-size: 15px; font-weight: 900; color: #ffffff;'>{subject.name}</span>
                            </span>
                            <br>
                        """
                    )
            
            self.staff_data_layout.addWidget(LabeledField("Classes", duties_widget))
        elif isinstance(staff, Prefect):
            for day, duties in staff.duties.items():
                duties_content = ""
                
                for duty in duties:
                    duties_content += f"<span><span style='font-weight: bold; font-size: 15px;'>•</span>  {duty}</span><br>"
                
                duties_layout.addWidget(LabeledField(day, QLabel(duties_content)))
            
            self.staff_data_layout.addWidget(LabeledField("Duties", duties_widget))

class CardScanScreenWidget(BaseOptionsWidget):
    comm_signal = pySignal(str)
    
    def __init__(self, data: AppData, comm_system: BaseCommSystem, parent_widget: TabViewWidget, saved_state_changed: pyBoundSignal):
        super().__init__(parent_widget, "static")
        self.data = data
        self.comm_system = comm_system
        self.saved_state_changed = saved_state_changed
        
        self.just_scanned = False
        
        self.setStyleSheet("""
            QLabel {
                font-size: 30px;
                font-weight: bold;
            }
        """)
        
        scan_img = Image("src/images/scan.png", height=330)
        scan_img.setStyleSheet("margin-bottom: 20px;")
        self.main_layout.addWidget(scan_img, alignment=Qt.AlignmentFlag.AlignCenter)
        
        info = QLabel("Scan RFID card")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.info_label, Qt.AlignmentFlag.AlignCenter)
        
        self.comm_signal.connect(self.scanned)
        self.comm_system.set_data_point("IUD", self.comm_signal)
        
        self.iud_label = None
        
        self.comm_system.connection_changed_signal.connect(self.connection_changed)
        self.iud_changed = False
    
    def _deactivate_just_scanned(self):
        self.just_scanned = False
    
    def set_self(self, staff: Staff, iud_label: QLabel):
        super().set_self(staff)
        
        self.iud_label = iud_label
        self.info_label.setText(f"<span style='font-size: 20px; font-weight: 500; text-align: left;'><span style='font-weight: bold; color: {THEME_MANAGER.pallete_get('fg2')};'>ID:</span>  {self.staff.id}<br>\n<span style='font-weight: bold; color: {THEME_MANAGER.pallete_get('fg2')};'>Name:</span>  {self.staff.name.full()}</span>")
    
    def finished(self):
        self.iud_label = None
        if self.iud_changed:
            self.comm_system.send_message("REGISTERED")
            
            # QTimer.singleShot(
            #     500,
            #     lambda: QMessageBox.information(self.parent_widget, "IUD Set", f"{self.staff.name.full()}'s IUD has been set to {self.staff.IUD}")
            # )
            
            self.just_scanned = True
            QTimer.singleShot(500, self._deactivate_just_scanned)
        return super().finished()
    
    def connection_changed(self, state: bool):
        if not state and self.parent_widget.stack.indexOf(self) == self.parent_widget.stack.currentIndex():
            self.finished()
    
    def scanned(self, data: str):
        if self.parent_widget.stack.currentIndex() == self.parent_widget.stack.indexOf(self):
            for prefect in self.data.prefects.values():
                if prefect.IUD == data:
                    self.comm_system.send_message("UNREGISTERED")
                    self.just_scanned = True
                    
                    QTimer.singleShot(1000, lambda: self.comm_system.send_message("Card has already_ been assigned "))
                    
                    QMessageBox.warning(self.parent_widget, "KeyError", f"Card of IUD {data} has already been assigned to the prefect {prefect.name.full()}")
                    
                    QTimer.singleShot(500, self._deactivate_just_scanned)
                    self.iud_changed = False
                    self.finished()
                    return
            else:
                for teacher in self.data.teachers.values():
                    if teacher.IUD == data:
                        self.comm_system.send_message("UNREGISTERED")
                        self.just_scanned = True
                        
                        QTimer.singleShot(1000, lambda: self.comm_system.send_message("Card has already_ been assigned "))
                        
                        QMessageBox.warning(self.parent_widget, "KeyError", f"Card of IUD {data} has already been assigned to the teacher {teacher.name.full()}")
                        
                        QTimer.singleShot(500, self._deactivate_just_scanned)
                        self.iud_changed = False
                        self.finished()
                        return
            
            self.staff.IUD = data
            self.iud_label.setText(self.staff.IUD)
            
            self.saved_state_changed.emit(False)
            
            self.iud_changed = True
            self.finished()
            self.iud_changed = False

