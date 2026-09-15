
from imports import *

from .base import *
from .timetable import *
from .user_interface import *

from AttendanceApp import AttendanceManager


class BaseSelectionList(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, selected_items: list[tuple[ID, Subject | Teacher]], content_scope: Global, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.setFixedSize(400, 300)
        
        self.widgets: dict[ID, SelectWidget] = {}
        
        selected_ids = []
        
        # Add selected items
        for item_id, item in selected_items:
            selected_ids.append(item_id)
            widget = _SL_SelectedWidget(self, item_id, item.name.full(), self.getLayout(), self.item_removed, self.item_selected, self._parent.window())
            
            self.addWidget(widget)
        
        # Add unselected items
        for item_id, item in content_scope.items():
            if item_id not in selected_ids:
                widget = _SL_UnSelectedWidget(self, item_id, item.name.full(), self.getLayout(), self.item_selected, self.item_removed, self._parent.window())
                
                self.addWidget(widget)
        
        self.addStretch()
    
    def addWidget(self, widget, stretch = None, alignment = None):
        self.widgets[widget.id] = widget
        
        return super().addWidget(widget, stretch, alignment)
    
    def insertWidget(self, index, widget, stretch = None, alignment = None):
        self.widgets[widget.id] = widget
        
        return super().insertWidget(index, widget, stretch, alignment)
    
    def removeWidget(self, widget):
        self.widgets.pop(widget.id)
        
        r = super().removeWidget(widget)
        widget.deleteLater()
        
        return r
    
    def item_removed(self, id: ID):
        raise NotImplementedError()
    
    def item_selected(self, id: ID):
        raise NotImplementedError()
    
    def go_to(self, widget: "_SL_SelectedWidget"):
        def func():
            self.getScrollWidget().verticalScrollBar().setValue(widget.y())
            
            widget.setFocus()
        
        QTimer.singleShot(200, func)


class SubjectSelectionList(BaseSelectionList):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        self.subject = SCHOOL.subjects[id]
        
        selected_iter = {t_id: teacher for t_id, teacher in SCHOOL.teachers.items() if id in teacher.subjects}
        
        scope = SCHOOL.teachers
        if next((False for cls in self.subject.classes.values() if cls.subjects[id].teacher is None), True):
            scope = selected_iter.copy()
        
        super().__init__(parent, id, title, iter(selected_iter.items()), scope, attendance_manager)
    
    def item_selected(self, id: ID):
        SCHOOL.teachers[id].subjects[self.id] = self.subject
        
        for staff_widget_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
            if id in staff_widget_dict:
                staff_widget_dict[id].add_subject(self.subject)
    
    def item_removed(self, id: ID):
        SCHOOL.teachers[id].subjects.pop(self.id)
        
        for cls in self.subject.classes.values():
            if cls.subjects[self.id].teacher is not None and cls.subjects[self.id].teacher.id == id:
                cls.subjects[self.id].teacher = None
        
        for staff_widget_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
            if id in staff_widget_dict:
                staff_widget_dict[id].remove_subject(self.subject)

class CombinedSubjectSelectionList(BaseSelectionList):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        self.c_subject: CombinedSubject = SCHOOL.subjects[id]
        
        self.selected_items = {s.id: s for s in self.c_subject.subjects}
        self.full_scope = {s_id: s for s_id, s in SCHOOL.subjects.items() if self._scope_check(s)}
        
        super().__init__(parent, id, title, iter(self.selected_items.items()), self.full_scope, attendance_manager)
    
    def _scope_check(self, subject: Subject | CombinedSubject):
        return isinstance(subject, Subject) and subject.classes
    
    def item_selected(self, id: ID):
        subject = SCHOOL.subjects[id]
        
        self.c_subject.classes[id] = {}
        self.c_subject.subjects.append(subject)
        
        self.selected_items[subject.id] = subject
        
        for s_id, s in SCHOOL.subjects.items():
            if not self._scope_check(s) and s_id in self.full_scope:
                self.full_scope.pop(s_id)
                self.removeWidget(self.widgets[s_id])
        
        if not self._parent.simple_line_edit.text():
            self._parent.simple_name_changed(self._parent.simple_line_edit.text(), None)
    
    def item_removed(self, id):
        subject = SCHOOL.subjects[id]
        
        self.c_subject.remove_subject(subject)
        
        self.selected_items.pop(subject.id)
        
        for s_id, s in SCHOOL.subjects.items():
            if self._scope_check(s) and s_id not in self.full_scope and s_id not in self.selected_items:
                self.full_scope[s_id] = s
                self.insertWidget(len(self.full_scope) - 1, _SL_UnSelectedWidget(self, s_id, s.name.full(), self.getLayout(), self.item_selected, self.item_removed, self._parent.window()))
        
        if not self._parent.simple_line_edit.text():
            self._parent.simple_name_changed(self._parent.simple_line_edit.text(), None)
    
class TeacherSelectionList(BaseSelectionList):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        self.teacher = SCHOOL.teachers[id]
        
        self.combined_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject)]
        scope = {s.id: s for s in SCHOOL.subjects.values() if self._scope_check(id, s)}
        
        super().__init__(parent, id, title, iter(self.teacher.subjects.items()), scope, attendance_manager)
    
    def _scope_check(self, teacher_id: ID, subject: Subject | CombinedSubject):
        if not isinstance(subject, Subject):
            return False
        
        for cls in subject.classes.values():
            if subject.id in cls.subjects and (cls.subjects[subject.id].teacher is None or cls.subjects[subject.id].teacher.id == teacher_id):
                break
        else:
            for c_subject in self.combined_subjects:
                if subject.id in c_subject.classes:
                    for cls in c_subject.classes[subject.id].values():
                        if next((s.teacher is None or s.teacher.id == teacher_id for s in cls.subjects[c_subject.id].subjects if s.id == subject.id), False):
                            break
                    else:
                        continue
                    
                    break
            else:
                return False
        
        return True
    
    def item_selected(self, id: ID):
        subject = SCHOOL.teachers[self.id].subjects[id] = SCHOOL.subjects[id]
        
        for staff_widget_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
            if self.id in staff_widget_dict:
                staff_widget_dict[self.id].add_subject(subject)
    
    def item_removed(self, id: ID):
        subject = self.teacher.subjects.pop(id)
        
        for cls in subject.classes.values():
            if id in cls.subjects:
                if cls.subjects[id].teacher is not None and cls.subjects[id].teacher.id == self.id:
                    cls.subjects[id].teacher = None
            else:
                for subj in SCHOOL.subjects.values():
                    if (
                            isinstance(subj, CombinedSubject) and
                            (u_subj := next((cls.subjects[subj.id].subjects[i] for i, s in enumerate(subj.subjects) if s.id == subject.id), False)) and
                            u_subj.teacher is not None and
                            u_subj.teacher.id == self.id
                        ):
                        u_subj.teacher = None
                        break
        
        for staff_widget_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
            if self.id in staff_widget_dict:
                staff_widget_dict[self.id].remove_subject(subject)

class SubjectDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.__init = True
        
        self.id = id
        self._parent = parent
        self.subject = SCHOOL.subjects[self.id]
        
        self.attendance_manager = attendance_manager
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and next((True for s_s in s.subjects if self.id == s_s.id), False)]
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.class_check_box_tracker = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "widget": {}, "min_rem": {}}
        
        for widget in self.make_school_widget_dropdowns():
            self.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
        
        self.__init = False
    
    def go_to(self, lvl_id: ID, cls_id: Optional[CLASS_ID] = None):
        if cls_id is None:
            if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
            
            def func():
                self.getScrollWidget().verticalScrollBar().setValue(self.class_check_box_tracker["widget"][lvl_id].y())
                
                self.class_check_box_tracker["widget"][lvl_id].setFocus()
            
            QTimer.singleShot(200, func)
        else:
            if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
            
            self.getScrollWidget().verticalScrollBar().setValue(self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].y())
            
            self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].setFocus()
    
    def make_school_widget_dropdowns(self):
        widgets: list[QWidget] = []
        all_clicked_checkboxes: list[QCheckBox] = []
        
        for lvl_id, cls_lvl in SCHOOL.class_levels.items():
            week_total = (cls_lvl.period_amount - 1) * len(cls_lvl.weekdays)
            min_rem = min(week_total - sum(cls_lvl.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls_lvl.subjects_occurence) for cls in cls_lvl.classes.values())
            
            check_box = QCheckBox()
            check_box.clicked.connect(self.make_main_checkbox_func(lvl_id))
            
            self.class_check_box_tracker["sub_cbs"][lvl_id] = {}
            self.class_check_box_tracker["main_cb"][lvl_id] = check_box
            self.class_check_box_tracker["min_rem"][lvl_id] = min_rem
            self.class_check_box_tracker["widget"][lvl_id], to_be_clicked = self.make_level_dp_widget(lvl_id, cls_lvl)
            
            main_widget = WidgetDropdown(cls_lvl.name.full(), self.class_check_box_tracker["widget"][lvl_id])
            main_widget.header.addWidget(check_box)
            main_widget.setOpen(False)
            main_widget.setDisabled(self.id not in cls_lvl.subjects_occurence and min_rem <= 0)
            
            self.class_check_box_tracker["icon"][lvl_id] = main_widget.toogle_icon
            
            all_clicked_checkboxes.extend(to_be_clicked)
            
            widgets.append(main_widget)
        
        for cb in all_clicked_checkboxes:
            cb.click()
        
        return widgets
    
    def make_level_dp_widget(self, lvl_id: ID, cls_lvl: ClassLevel):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in cls_lvl.classes.items():
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            
            dp_checkbox = QCheckBox()
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(lvl_id, cls_id))
            
            self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id] = dp_checkbox
            
            if cls.id in self.subject.classes and not dp_checkbox.isChecked():
                clicked_cbs.append(dp_checkbox)
            
            option_widget.addSpacing(50)
            option_widget.addWidget(dp_title)
            option_widget.addStretch()
            option_widget.addWidget(dp_checkbox)
            
            dp_widget.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def make_main_checkbox_func(self, lvl_id: ID):
        def checkbox_func(is_on):
            if not self.mini_guy_is_clicked:
                if not self.__init:
                    self._parent.window().saved_state_changed.emit(True)
                
                self.main_guy_is_clicked = True
                
                for c_box in self.class_check_box_tracker["sub_cbs"][lvl_id].values():
                    if is_on != c_box.isChecked():
                        c_box.click()
                
                self.main_guy_is_clicked = False
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, lvl_id: ID, cls_id: CLASS_ID):
        def checkbox_func(on):
            if not self.__init:
                self.sub_checkbox_func(on, lvl_id, cls_id)
                self._parent.window().saved_state_changed.emit(True)
            
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if on:
                    lvl_set = set(SCHOOL.class_levels[lvl_id].classes)
                    intersect_set = set(self.subject.classes).intersection(lvl_set)
                    
                    if len(lvl_set) == len(intersect_set) and not self.class_check_box_tracker["main_cb"][lvl_id].isChecked():
                        self.class_check_box_tracker["main_cb"][lvl_id].click()
                else:
                    if self.class_check_box_tracker["main_cb"][lvl_id].isChecked():
                        self.class_check_box_tracker["main_cb"][lvl_id].click()
                
                self.mini_guy_is_clicked = False
        
        return checkbox_func
    
    def sub_checkbox_func(self, on: bool, lvl_id: ID, cls_id: CLASS_ID):
        lvl = SCHOOL.class_levels[lvl_id]
        cls = lvl.classes[cls_id]
        
        if on:
            if self.c_subjects:
                for c_subject in self.c_subjects:
                    if c_subject.id not in cls.subjects:
                        cls.subjects[c_subject.id] = c_subject.passCopy()
            
            self.subject.classes[cls_id] = cls
            cls.subjects[self.id] = self.subject.passCopy()
            
            if self.id not in lvl.subjects_occurence:
                per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
                min_rem = self.class_check_box_tracker["min_rem"][lvl_id]
                
                lvl.subjects_occurence[self.id] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))
        else:
            self.subject.classes.pop(cls_id)
            
            if self.id in cls.subjects:
                cls.subjects.pop(self.id)
            
            for teacher_widget_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                for teacher_attendance_entry_widget in teacher_widget_dict.values():
                    if cls_id in teacher_attendance_entry_widget.class_labels:
                        for s_id, _ in teacher_attendance_entry_widget.class_labels[cls_id]:
                            if s_id == self.id:
                                teacher_attendance_entry_widget.remove_class(self.id, cls_id)
            
            if self.id in lvl.subjects_occurence and next((False for cls in lvl.classes.values() if self.id in cls.subjects), True):
                lvl.subjects_occurence.pop(self.id)
            
            for c_subject in self.c_subjects:
                if cls_id in c_subject.classes[self.id]:
                    c_subject.classes[self.id].pop(cls_id)
                
                if next((False for s in c_subject.subjects if s.id in cls.subjects), True):
                    cls.subjects.pop(c_subject.id)

class CombinedSubjectDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.__init = True
        
        self.id = id
        self._parent = parent
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.combined_subject: CombinedSubject = SCHOOL.subjects[self.id]
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.subject_check_box_tracker = {}
        self.class_check_box_tracker = {}
        
        for subject in self.combined_subject.subjects:
            self.subject_check_box_tracker[subject.id] = {}
            self.class_check_box_tracker[subject.id] = {"main_cb": {}, "sub_cbs": {}, "cls_cb_widget": {}, "icon": {}, "max_random": {}, "widget": {}}
            
            self.subject_check_box_tracker[subject.id]["widget"] = self.make_subject_widget(subject)
            
            main_widget = WidgetDropdown(subject.name.full(), self.subject_check_box_tracker[subject.id]["widget"])
            
            self.subject_check_box_tracker[subject.id]["icon"] = main_widget.toogle_icon
            
            self.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
        
        self.__init = False
    
    def make_subject_widget(self, subject: Subject):
        widgets: list[QWidget] = []
        
        cls_lvls = []
        for cls in subject.classes.values():
            if cls.level.id not in cls_lvls:
                cls_lvls.append(cls.level.id)
            else:
                continue
            
            select_all_check_box = QCheckBox()
            select_all_check_box.clicked.connect(self.make_select_all_checkbox_func(subject, cls.level.id))
            
            self.class_check_box_tracker[subject.id]["sub_cbs"][cls.level.id] = {}
            self.class_check_box_tracker[subject.id]["cls_cb_widget"][cls.level.id] = {}
            self.class_check_box_tracker[subject.id]["main_cb"][cls.level.id] = select_all_check_box
            self.class_check_box_tracker[subject.id]["widget"][cls.level.id], to_be_clicked = self.make_level_dp_widget(subject, cls.level)
            
            widgets.append(main_widget := WidgetDropdown(cls.level.name.full(), self.class_check_box_tracker[subject.id]["widget"][cls.level.id]))
            
            main_widget.header.addWidget(select_all_check_box)
            
            self.class_check_box_tracker[subject.id]["icon"][cls.level.id] = main_widget.toogle_icon
        
        for cb in to_be_clicked:
            cb.click()
        
        container_widget = BaseWidget()
        
        for widget in widgets:
            container_widget.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        container_widget.setVisible(False)
        
        return container_widget
    
    def make_level_dp_widget(self, subject: Subject, lvl: ClassLevel):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in subject.classes.items():
            if (
                    cls_id not in lvl.classes or
                    (subject.id in cls.subjects and cls.subjects[subject.id].teacher is not None) or
                    next((True for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and s.id != self.combined_subject.id and subject.id in s.classes and cls_id in s.classes[subject.id]), False)
                ):
                continue
            
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            dp_checkbox = QCheckBox()
            
            self.class_check_box_tracker[subject.id]["sub_cbs"][lvl.id][cls_id] = dp_checkbox
            self.class_check_box_tracker[subject.id]["cls_cb_widget"][lvl.id][cls_id] = option_widget
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(subject, lvl.id, cls_id))
            
            if cls_id in self.combined_subject.classes[subject.id]:
                clicked_cbs.append(dp_checkbox)
            
            option_widget.addSpacing(50)
            option_widget.addWidget(dp_title)
            option_widget.addStretch()
            option_widget.addWidget(dp_checkbox)
            
            dp_widget.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def make_select_all_checkbox_func(self, subject: Subject, lvl_id: ID):
        def checkbox_func(is_on):
            if not self.mini_guy_is_clicked:
                self.main_guy_is_clicked = True
                
                for c_box in self.class_check_box_tracker[subject.id]["sub_cbs"][lvl_id].values():
                    if is_on != c_box.isChecked():
                        c_box.click()
                
                self.main_guy_is_clicked = False
                
                if not self.__init:
                    self._parent.window().saved_state_changed.emit(True)
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, subject: Subject, lvl_id: ID, cls_id: CLASS_ID):
        def checkbox_func(on):
            if not self.__init:
                self.sub_checkbox_func(on, subject, lvl_id, cls_id)
                self._parent.window().saved_state_changed.emit(True)
            
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if on:
                    for c_id, cb in self.class_check_box_tracker[subject.id]["sub_cbs"][lvl_id].items():
                        if c_id != cls_id and not cb.isChecked():
                            break
                    else:
                        self.class_check_box_tracker[subject.id]["main_cb"][lvl_id].click()
                else:
                    if self.class_check_box_tracker[subject.id]["main_cb"][lvl_id].isChecked():
                        self.class_check_box_tracker[subject.id]["main_cb"][lvl_id].click()
                
                self.mini_guy_is_clicked = False
        
        return checkbox_func
    
    def sub_checkbox_func(self, on: bool, subject: Subject, lvl_id: ID, cls_id: CLASS_ID):
        cls = SCHOOL.class_levels[lvl_id].classes[cls_id]
        
        if on:
            self.combined_subject.classes[subject.id][cls_id] = cls
            
            if subject.id in cls.subjects:
                cls.subjects.pop(subject.id)
            
            if self.id not in cls.subjects:
                cls.subjects[self.id] = self.combined_subject.passCopy()
            
            if next((False for c in cls.level.classes.values() if subject.id in c.subjects), True):
                cls.level.subjects_occurence.pop(subject.id)
            
            if self.id not in cls.level.subjects_occurence:
                per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
                
                week_total = (cls.level.period_amount - 1) * len(cls.level.weekdays)
                min_rem = min(week_total - sum(cls.level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls.level.subjects_occurence) for cls in cls.level.classes.values())
                
                cls.level.subjects_occurence[self.id] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))
        else:
            self.combined_subject.classes[subject.id].pop(cls_id)
            
            if subject.id not in cls.subjects:
                cls.subjects[subject.id] = subject.passCopy()
            
            if self.id in cls.subjects and next((False for s_c_dict in self.combined_subject.classes.values() if cls_id in s_c_dict), True):
                cls.subjects.pop(self.id)
            
            if next((False for c_id in flatten(set(subj_classes) for subj_classes in self.combined_subject.classes.values()) if c_id.class_level_id == lvl_id), True):
                cls.level.subjects_occurence.pop(self.id)
            
            if subject.id not in cls.level.subjects_occurence:
                per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
                
                week_total = (cls.level.period_amount - 1) * len(cls.level.weekdays)
                min_rem = min(week_total - sum(cls.level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls.level.subjects_occurence) for cls in cls.level.classes.values())
                
                cls.level.subjects_occurence[subject.id] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))

class TeacherDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.__init = True
        
        self.id = id
        self._parent = parent
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.teacher = SCHOOL.teachers[self.id]
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        combined_subjects = {s_id: s for s_id, s in SCHOOL.subjects.items() if isinstance(s, CombinedSubject) and next((True for s_s in s.subjects if s_s.id in self.teacher.subjects), False)}
        
        self.subject_check_box_tracker = {}
        self.class_check_box_tracker = {}
        
        for subject_id, subject in self.teacher.subjects.items():
            if next((True for c in subject.classes.values() if subject_id in c.subjects), False):
                self.subject_check_box_tracker[subject_id] = {}
                self.class_check_box_tracker[subject_id] = {"main_cb": {}, "sub_cbs": {}, "cls_cb_widget": {}, "icon": {}, "max_random": {}, "widget": {}}
                
                self.subject_check_box_tracker[subject_id]["widget"] = self.make_subject_widget(subject)
                
                main_widget = WidgetDropdown(subject.name.full(), self.subject_check_box_tracker[subject_id]["widget"])
                
                metrics = QFontMetrics(main_widget.title_label.font())
                main_widget.title_label.setText(metrics.elidedText(main_widget.title_label.text(), Qt.TextElideMode.ElideRight, 200))
                main_widget.title_label.setToolTip(main_widget.title_label.text())
                
                self.subject_check_box_tracker[subject_id]["icon"] = main_widget.toogle_icon
                
                self.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        for c_subject_id, c_subject in combined_subjects.items():
            self.subject_check_box_tracker[c_subject_id] = {}
            
            ccbt = self.class_check_box_tracker[c_subject_id] = {}
            scbt = self.subject_check_box_tracker[c_subject_id]["content"] = {}
            
            combined_subject_widget = self.subject_check_box_tracker[c_subject_id]["widget_dp"] = WidgetDropdown(c_subject.name.full(), self.c_make_subject_widget(c_subject, scbt, ccbt))
            
            metrics = QFontMetrics(combined_subject_widget.title_label.font())
            combined_subject_widget.title_label.setText(metrics.elidedText(combined_subject_widget.title_label.text(), Qt.TextElideMode.ElideRight, 200))
            combined_subject_widget.title_label.setToolTip(combined_subject_widget.title_label.text())
            
            self.addWidget(combined_subject_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
        
        self.__init = False
    
    def go_to(self, subj_id: ID, lvl_id: Optional[ID], cls_id: Optional[CLASS_ID], c_subj_id: Optional[ID] = None):
        def s_func():
            if not lvl_id and not cls_id:
                def func1():
                    if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                        self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                    
                    def in_func():
                        self.getScrollWidget().verticalScrollBar().setValue(self.subject_check_box_tracker[subj_id]["widget"].y())
                        
                        self.subject_check_box_tracker[subj_id]["widget"].setFocus()
                
                    QTimer.singleShot(200, in_func)
                
                QTimer.singleShot(200, func1)
            elif not cls_id:
                def func2():
                    if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                        self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                    
                    def in_func():
                        if not self.class_check_box_tracker[subj_id]["widget"][lvl_id].isVisible():
                            self.class_check_box_tracker[subj_id]["icon"][lvl_id].mouseclicked.emit()
                        
                        def inner_func():
                            self.getScrollWidget().verticalScrollBar().setValue(self.class_check_box_tracker[subj_id]["widget"][lvl_id].y())
                            
                            self.class_check_box_tracker[subj_id]["widget"][lvl_id].setFocus()
                    
                        QTimer.singleShot(200, inner_func)
                    
                    QTimer.singleShot(200, in_func)
                
                QTimer.singleShot(250, func2)
            else:
                def func3():
                    if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                        self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                    
                    self.update()
                    
                    def in_func():
                        if not self.class_check_box_tracker[subj_id]["widget"][lvl_id].isVisible():
                            self.class_check_box_tracker[subj_id]["icon"][lvl_id].mouseclicked.emit()
                            self.getScrollWidget().verticalScrollBar().setValue(self.class_check_box_tracker[subj_id]["widget"][lvl_id].y())
                        
                        self.update()
                        
                        def inner_func():
                            self.getScrollWidget().verticalScrollBar().setValue(self.subject_check_box_tracker[subj_id]["widget"].y() + self.class_check_box_tracker[subj_id]["sub_cbs"][lvl_id][cls_id].y())
                            
                            self.class_check_box_tracker[subj_id]["sub_cbs"][lvl_id][cls_id].setFocus()
                
                        QTimer.singleShot(500, inner_func)
                    
                    QTimer.singleShot(500, in_func)
                    
                QTimer.singleShot(500, func3)
        
        if c_subj_id is not None:
            if not self.subject_check_box_tracker[c_subj_id]["widget_dp"].widget.isVisible():
                self.subject_check_box_tracker[c_subj_id]["widget_dp"].toogle_icon.mouseclicked.emit()
            
            QTimer.singleShot(200, s_func)
        else:
            s_func()
    
    def make_subject_widget(self, subject: Subject, scbt=None, ccbt=None, m_lvl_dp_w=None, combined_subject: Optional[CombinedSubject]=None):
        scbt = scbt or self.subject_check_box_tracker
        ccbt = ccbt or self.class_check_box_tracker
        m_lvl_dp_w = m_lvl_dp_w or self.make_level_dp_widget
        
        class_level_ids = (combined_subject and set([c.level.id for c in combined_subject.classes[subject.id].values()])) or set([c.level.id for c in subject.classes.values()])
        
        container_widget = BaseWidget()
        
        random_on_checkboxes: list[QCheckBox] = []
        
        for cls_level_id in class_level_ids:
            cls_level = SCHOOL.class_levels[cls_level_id]
            
            if combined_subject is not None or subject.id in cls_level.subjects_occurence:
                def rsma_func(number: Optional[int]):
                    SCHOOL.settings.TEACHER_rsma_mapping[cls_level.id] = number
                
                max_random_text_input = NumberLineEdit(SCHOOL.settings.TEACHER_rsma_mapping[cls_level.id] if SCHOOL.settings.TEACHER_rsma_mapping[cls_level.id] is not None else 1, 1, len(cls_level.classes))
                max_random_text_input.edit.setToolTip("Maximum Classes Taught")
                max_random_text_input.setVisible(False)  # This has been disabled for now
                max_random_text_input.textChanged.connect(rsma_func)
                
                is_random_check_box = QCheckBox("Random")
                
                select_all_check_box = QCheckBox("All")
                select_all_check_box.clicked.connect(self.make_select_all_checkbox_func(subject, cls_level.id, ccbt))
                
                if SCHOOL.settings.TEACHER_rsma_mapping[cls_level.id]:
                    random_on_checkboxes.append(is_random_check_box)
                
                ccbt[subject.id]["sub_cbs"][cls_level.id] = {}
                ccbt[subject.id]["cls_cb_widget"][cls_level.id] = {}
                ccbt[subject.id]["main_cb"][cls_level.id] = select_all_check_box
                ccbt[subject.id]["widget"][cls_level.id], to_be_clicked = m_lvl_dp_w(subject, cls_level, ccbt, combined_subject)
                
                main_widget = WidgetDropdown(cls_level.name.full(), ccbt[subject.id]["widget"][cls_level.id])
                
                metrics = QFontMetrics(main_widget.title_label.font())
                main_widget.title_label.setText(metrics.elidedText(main_widget.title_label.text(), Qt.TextElideMode.ElideRight, 200))
                main_widget.title_label.setToolTip(main_widget.title_label.text())
                
                main_widget.header.addWidget(max_random_text_input)
                # main_widget.header.addWidget(is_random_check_box)
                main_widget.header.addWidget(select_all_check_box)
                
                is_random_check_box.clicked.connect(self.make_random_checkbox_func(subject, cls_level.id, main_widget, max_random_text_input, rsma_func, ccbt))
                
                ccbt[subject.id]["icon"][cls_level.id] = main_widget.toogle_icon
                
                random_on_checkboxes.extend(to_be_clicked)
                
                container_widget.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        for cb in random_on_checkboxes:
            cb.click()
        
        container_widget.setVisible(False)
        
        return container_widget
    
    def make_level_dp_widget(self, subject: Subject, lvl: ClassLevel, *args):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in lvl.classes.items():
            if subject.id not in cls.subjects:
                continue
            
            u_subject = cls.subjects[subject.id]
            
            optionState = u_subject.teacher is not None and u_subject.teacher.id == self.teacher.id
            is_disabled = u_subject.teacher is not None and u_subject.teacher.id != self.teacher.id
            
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            dp_title.setDisabled(is_disabled)
            
            dp_checkbox = QCheckBox()
            dp_checkbox.setDisabled(is_disabled)
            
            self.class_check_box_tracker[subject.id]["sub_cbs"][lvl.id][cls_id] = dp_checkbox
            self.class_check_box_tracker[subject.id]["cls_cb_widget"][lvl.id][cls_id] = option_widget
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(subject, lvl.id, cls_id))
            
            if not is_disabled and optionState and SCHOOL.settings.TEACHER_rsma_mapping[lvl.id] is None:
                clicked_cbs.append(dp_checkbox)
            
            option_widget.addSpacing(50)
            option_widget.addWidget(dp_title)
            option_widget.addStretch()
            if is_disabled:
                link_label = QLabel(u_subject.teacher.name.full())
                link_label.mousePressEvent = self.make_link_func(u_subject.id, lvl.id, cls.id, u_subject.teacher)
                link_label.setProperty("class", "Link")
                
                option_widget.addWidget(link_label)
            else:
                option_widget.addWidget(dp_checkbox)
            
            dp_widget.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def sub_checkbox_func(self, on: bool, lvl_id: ID, cls_id: ID, subject: Subject, *args):
        cls_level = SCHOOL.class_levels[lvl_id]
        cls = cls_level.classes[cls_id]
        
        if on:
            cls.subjects[subject.id].teacher = self.teacher
            self.timetable_editor.timetable_widgets[lvl_id][cls_id].change_subject_amount(subject.id, cls_level.subjects_occurence[subject.id].week_max)
            
            for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                if self.id in teacher_filtered_dict:
                    teacher_filtered_dict[self.id].add_class(subject.id, cls)
        else:
            cls.subjects[subject.id].teacher = None
            self.timetable_editor.timetable_widgets[lvl_id][cls_id].change_subject_amount(subject.id, -cls_level.subjects_occurence[subject.id].week_max)
            
            for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                if self.id in teacher_filtered_dict:
                    teacher_filtered_dict[self.id].remove_class(subject.id, cls_id)
    
    def make_link_func(self, s_id: ID, lvl_id: ID, cls_id: CLASS_ID, teacher: Teacher, c_s_id: Optional[ID] = None):
        def func(e):
            self.close()
            
            def func1():
                widget = self._parent.go_to(teacher)
                
                QTimer.singleShot(500, lambda: func2(widget.dialog_widget_funcs[0]))
            
            def func2(d_func: Callable[[], BaseSettingDialog]):
                w = d_func()
                QTimer.singleShot(500, lambda: w.go_to(s_id, lvl_id, cls_id, c_s_id))
                
                w.exec()
            
            QTimer.singleShot(500, func1)
        
        return func
    
    def make_random_checkbox_func(self, subject: Subject, class_id: ID, widget_dp: WidgetDropdown, max_random_text_input: QLineEdit, rsma_func: Callable[[Optional[int]], None], ccbt=None):
        ccbt = ccbt or self.class_check_box_tracker
        
        def checkbox_func(on):
            if on:
                for c_box in ccbt[subject.id]["sub_cbs"][class_id].values():
                    if c_box.isChecked():
                        c_box.click()
                
                if ccbt[subject.id]["icon"][class_id].angle != 270:
                    ccbt[subject.id]["icon"][class_id].mouseclicked.emit()
                
                if max_random_text_input.number() == -1:
                    max_random_text_input.setNumber(SCHOOL.settings.DEFAULT_max_classes)
                
                if not self.__init:
                    rsma_func(None)
            
            widget_dp.beDisabled(not on, True)
            max_random_text_input.setVisible(on)
            ccbt[subject.id]["icon"][class_id].setDisabled(on)
            
            if not self.__init:
                self._parent.window().saved_state_changed.emit(True)
        
        return checkbox_func
    
    def make_select_all_checkbox_func(self, subject: Subject, lvl_id: ID, ccbt=None):
        ccbt = ccbt or self.class_check_box_tracker
        
        def checkbox_func(is_on):
            if not self.mini_guy_is_clicked:
                self.main_guy_is_clicked = True
                
                for c_box in ccbt[subject.id]["sub_cbs"][lvl_id].values():
                    if is_on != c_box.isChecked() and c_box.isEnabled():
                        c_box.click()
                
                self.main_guy_is_clicked = False
                
                if not self.__init:
                    self._parent.window().saved_state_changed.emit(True)
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, subject: Subject, lvl_id: ID, cls_id: CLASS_ID, ccbt=None, s_cb_f=None, *args):
        ccbt = ccbt or self.class_check_box_tracker
        s_cb_f = s_cb_f or self.sub_checkbox_func
        
        def checkbox_func(on):
            if not self.__init:
                s_cb_f(on, lvl_id, cls_id, subject, *args)
                self._parent.window().saved_state_changed.emit(True)
            
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if on:
                    for c_id, cb in ccbt[subject.id]["sub_cbs"][lvl_id].items():
                        if cb.isEnabled() and c_id != cls_id and not cb.isChecked():
                            break
                    else:
                        ccbt[subject.id]["main_cb"][lvl_id].click()
                else:
                    if ccbt[subject.id]["main_cb"][lvl_id].isChecked():
                        ccbt[subject.id]["main_cb"][lvl_id].click()
                
                self.mini_guy_is_clicked = False
        
        return checkbox_func
    
    def c_make_subject_widget(self, combined_subject: CombinedSubject, scbt: dict[ID, dict], ccbt: dict[ID, dict]):
        c_widget = BaseWidget()
        
        for subject in combined_subject.subjects:
            if subject.id in self.teacher.subjects and combined_subject.classes[subject.id]:
                scbt[subject.id] = {}
                ccbt[subject.id] = {"main_cb": {}, "sub_cbs": {}, "cls_cb_widget": {}, "icon": {}, "max_random": {}, "widget": {}}
                
                scbt[subject.id]["widget"] = self.make_subject_widget(subject, scbt, ccbt, self.c_make_level_dp_widget, combined_subject)
                
                subject_widget = WidgetDropdown(subject.name.full(), scbt[subject.id]["widget"])
                
                scbt[subject.id]["icon"] = subject_widget.toogle_icon
                
                c_widget.addWidget(subject_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        return c_widget
    
    def c_make_level_dp_widget(self, subject: Subject, lvl: ClassLevel, ccbt: dict[ID, dict], combined_subject: CombinedSubject):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id in subject.classes:
            cls = SCHOOL.class_levels[lvl.id].classes[cls_id]
            
            if cls_id not in combined_subject.classes[subject.id]:
                continue
            
            u_subject = next(s for s in cls.subjects[combined_subject.id].subjects if s.id == subject.id)
            
            optionState = u_subject.teacher is not None and u_subject.teacher.id == self.teacher.id
            is_disabled = u_subject.teacher is not None and u_subject.teacher.id != self.teacher.id
            
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            dp_title.setDisabled(is_disabled)
            
            dp_checkbox = QCheckBox()
            dp_checkbox.setDisabled(is_disabled)
            
            ccbt[subject.id]["sub_cbs"][lvl.id][cls_id] = dp_checkbox
            ccbt[subject.id]["cls_cb_widget"][lvl.id][cls_id] = option_widget
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(subject, lvl.id, cls_id, ccbt, self.c_sub_checkbox_func, combined_subject.id, ccbt))
            
            if not is_disabled and optionState:
                clicked_cbs.append(dp_checkbox)
            
            option_widget.addSpacing(50)
            option_widget.addWidget(dp_title)
            option_widget.addStretch()
            if is_disabled:
                link_label = QLabel(u_subject.teacher.name.full())
                link_label.mousePressEvent = self.make_link_func(subject.id, lvl.id, cls.id, u_subject.teacher, combined_subject.id)
                link_label.setProperty("class", "Link")
                
                option_widget.addWidget(link_label)
            else:
                option_widget.addWidget(dp_checkbox)
            
            dp_widget.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def c_sub_checkbox_func(self, on: bool, lvl_id: ID, cls_id: ID, subject: Subject, c_subject_id: ID, ccbt: dict[ID, dict]):
        cls_level = SCHOOL.class_levels[lvl_id]
        cls = cls_level.classes[cls_id]
        c_subject = cls.subjects[c_subject_id]
        u_subject = next(s for s in c_subject.subjects if s.id == subject.id)
        
        if on:
            if next((False for s in c_subject.subjects if s.teacher is not None), True):
                self.timetable_editor.timetable_widgets[lvl_id][cls_id].change_subject_amount(c_subject_id, cls_level.subjects_occurence[c_subject_id].week_max)
            
            u_subject.teacher = self.teacher
            
            for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                if self.id in teacher_filtered_dict:
                    teacher_filtered_dict[self.id].add_class(subject.id, cls)
        else:
            if next((False for s in c_subject.subjects if s.teacher is None), True):
                self.timetable_editor.timetable_widgets[lvl_id][cls_id].change_subject_amount(c_subject_id, -cls_level.subjects_occurence[c_subject_id].week_max)
            
            u_subject.teacher = None
            
            for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                if self.id in teacher_filtered_dict:
                    teacher_filtered_dict[self.id].remove_class(subject.id, cls_id)

class OccuranceEditor(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title, BaseWidget)
        
        self.__init = True
        
        self._parent = parent
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.central_widget = BaseScrollWidget()
        self.remainder_slots_label = QLabel()
        
        self.setSpacing(5)
        self.setContentsMargins(10, 10, 10, 10)
        
        self.central_widget.setSpacing(20)
        self.central_widget.setContentsMargins(20, 20, 20, 20)
        
        self.id = id
        self.class_level = SCHOOL.class_levels[self.id]
        
        self.setFixedSize(600, 400)
        
        self.focuses_ids = {}
        self.week_total = (self.class_level.period_amount - 1) * len(self.class_level.weekdays)
        
        self.subject_widgets: dict[str, QWidget] = {}
        self.number_edits: dict[str, tuple[NumberLineEdit, NumberLineEdit]] = {}
        
        for subject_id in self.class_level.subjects_occurence:
            self.add_subject(SCHOOL.subjects[subject_id])
        
        for subject_id, (per_day_edit, per_week_edit) in self.number_edits.items():
            per_day_edit.textChanged.emit(self.class_level.subjects_occurence[subject_id].day_max)
            per_week_edit.textChanged.emit(self.class_level.subjects_occurence[subject_id].week_max)
        
        self.central_widget.addStretch()
        
        self.addWidget(self.central_widget)
        self.addWidget(self.remainder_slots_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.__init = False
    
    def go_to(self, _id):
        for subject_id, widget in self.subject_widgets.items():
            if subject_id == _id:
                def func():
                    self.getScrollWidget().verticalScrollBar().setValue(widget.y())
                    widget.setFocus()
                
                QTimer.singleShot(200, func)
                
                break
    
    def add_subject(self, subject: Subject):
        selection_widget = BaseWidget(QHBoxLayout)
        selection_widget.setProperty("class", "SubjectClassViewEntry")
        
        metrics = QFontMetrics(self.font())
        subjects_label = QLabel(metrics.elidedText(subject.name.full(), Qt.TextElideMode.ElideRight, 100))
        subjects_label.setFont(self.font())
        subjects_label.setToolTip(subject.name.full())
        subjects_label.setProperty("class", "SubjectClassViewEntryName")
        
        sub_widget = BaseWidget()
        sub_widget.setProperty("class", "SubjectClassViewEntryEdits")
        
        selection_widget.addWidget(subjects_label, alignment=Qt.AlignmentFlag.AlignCenter)
        selection_widget.addWidget(sub_widget, alignment=Qt.AlignmentFlag.AlignRight)
        
        per_day_edit = NumberLineEdit(self.class_level.subjects_occurence[subject.id].day_max, 1, self.class_level.subjects_occurence[subject.id].week_max)
        # per_day_edit.edit.setFixedWidth(50)
        per_day_edit.setPlaceholderText("Per day")
        per_day_edit.textChanged.connect(self.make_per_day_text_changed_func(subject.id))
        
        subjects = set([])
        for cls in self.class_level.classes.values():
            if subject.id in cls.subjects:
                subjects = subjects.union(set(cls.subjects))
        
        self.focuses_ids[subject.id] = subjects
        
        per_week_edit = NumberLineEdit(self.class_level.subjects_occurence[subject.id].week_max, 1, self.class_level.subjects_occurence[subject.id].week_max + 1)
        # per_week_edit.edit.setFixedWidth(54)
        per_week_edit.setPlaceholderText("Per week")
        per_week_edit.textChanged.connect(self.make_per_week_text_changed_func(subject.id))
        
        per_day_widget = BaseWidget(QHBoxLayout)
        per_day_widget.setProperty("class", "Edit")
        per_day_widget.setStyleSheet("QWidget.Edit{background: none} QLabel{background: none}")
        
        per_day_widget.addWidget(QLabel("<b>Per day</b>"))
        per_day_widget.addWidget(per_day_edit)
        
        per_week_widget = BaseWidget(QHBoxLayout)
        per_week_widget.setProperty("class", "Edit")
        per_week_widget.setStyleSheet("QWidget.Edit{background: none} QLabel{background: none}")
        
        per_week_widget.addWidget(QLabel("<b>Per week</b>"))
        per_week_widget.addWidget(per_week_edit)
        
        sub_widget.addWidget(per_day_widget)
        sub_widget.addWidget(per_week_widget)
        
        self.central_widget.addWidget(selection_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.number_edits[subject.id] = per_day_edit, per_week_edit
        self.subject_widgets[subject.id] = selection_widget
    
    def make_per_day_text_changed_func(self, subject_id: ID):
        def text_changed_func(number):
            self.class_level.subjects_occurence[subject_id].day_max = number
            self.number_edits[subject_id][0].setNumber(self.number_edits[subject_id][0].number())
            
            if not self.__init:
                self._parent.window().saved_state_changed.emit(True)
        
        return text_changed_func
    
    def make_per_week_text_changed_func(self, subject_id: ID):
        def text_changed_func(number):
            wds = self.class_level.weekdays
            diff = number - self.class_level.subjects_occurence[subject_id].week_max
            
            min_rem = min(self.week_total - (sum(self.class_level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in self.class_level.subjects_occurence) + diff) for cls in self.class_level.classes.values())
            
            for per_day_edit, per_week_edit in self.number_edits.values():
                d_amt = per_day_edit.number()
                a_max_pw = len(wds) * d_amt
                
                self.class_level.subjects_occurence[subject_id].week_max = per_week_edit.number()
                per_week_edit.max_num = min(a_max_pw, self.class_level.subjects_occurence[subject_id].week_max + min_rem)
            
            self.remainder_slots_label.setText(f"<b style='color: {THEME_MANAGER.process_stylesheet("{fg1}")}; font-size: 15px;'>Slots:</b> <b style='font-size: 15px'>{min_rem}</b>")
            
            self.number_edits[subject_id][0].max_num = min(number, self.class_level.period_amount)
            self.class_level.subjects_occurence[subject_id].week_max = number
            
            for cls_id, cls in self.class_level.classes.items():
                if (
                        subject_id in cls.subjects and
                        (
                            cls.subjects[subject_id].teacher is not None
                            if isinstance(cls.subjects[subject_id], Subject) else
                            next((False for s in cls.subjects[subject_id].subjects if s.teacher is None), True)
                        )
                    ):
                    self.timetable_editor.timetable_widgets[cls.level.id][cls_id].change_subject_amount(subject_id, diff)
            
            if not self.__init:
                self._parent.window().saved_state_changed.emit(True)
        
        return text_changed_func

class ClassOptionsMaker(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.class_level = SCHOOL.class_levels[self.id]
        
        self.max_cols = 4  # Maximum number of columns before wrapping
        
        self.main_area = BaseFlowGridWidget(self.max_cols)
        self.main_area.setSpacing(4)
        self.main_area.getLayout().setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.add_button = QPushButton("Add Option")
        self.add_button.clicked.connect(lambda: self.add_option())
        
        self.addWidget(self.main_area)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        temp_option = EditableCancelableEntry("IFE")
        
        option_width = temp_option.getWidget().width() + 4 + temp_option.getLayout().contentsMargins().right() + temp_option.getLayout().contentsMargins().left()
        self.setFixedSize(option_width * self.max_cols, 300)
        
        del temp_option
        
        # Load existing options
        for class_id, cls in self.class_level.classes.items():
            self.add_option(class_id, cls.name)
    
    def go_to(self, widget: QWidget):
        def func():
            self.getScrollWidget().verticalScrollBar().setValue(widget.y())
            widget.setFocus()
        
        QTimer.singleShot(200, func)
    
    def add_option(self, id: str | None = None, text: str | None = None):
        option = EditableCancelableEntry(text)
        
        is_new = id is None
        
        if is_new:
            id = NEW_CLASS_ID(self.class_level.id)
            
            cls = Class(id, "", self.class_level, {}, SCHOOL)
            
            SCHOOL.class_levels.add_class(self.id, cls)
            self.timetable_editor.add_timetable_class(cls)
        else:
            cls = self.class_level.classes[id]
        
        def update_option():
            u_text = option.get_text()
            
            self.timetable_editor.set_label_text(id, u_text)
            cls.name = u_text
            
            for subject in cls.subjects.values():
                if isinstance(subject, Subject):
                    subjects = [subject]
                elif isinstance(subject, CombinedSubject):
                    subjects = subject.subjects
                
                for subject in subjects:
                    if subject.teacher:
                        for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                            if subject.teacher.id in teacher_filtered_dict:
                                teacher_filtered_dict[subject.teacher.id].update_class_name(cls)
            
            self._parent.window().saved_state_changed.emit(True)
        
        update_option()
        
        option.finished_editing_signal.connect(update_option)
        
        def remove_option():
            for subject in self.class_level.classes[id].subjects.values():
                if isinstance(subject, Subject):
                    subjects = [subject]
                elif isinstance(subject, CombinedSubject):
                    subjects = subject.subjects.copy()
                    
                    for subj_classes in subject.classes.values():
                        if id in subj_classes:
                            subj_classes.pop(id)
                    
                    subjects_with_this_class = []
                    
                    for subj in subject.subjects.copy():
                        if id in subj.classes:
                            subj.classes.pop(id)
                            subjects_with_this_class.append(subj)
                
                for subject in subjects:
                    if subject.teacher:
                        for teacher_filtered_dict in self.attendance_manager.staff_list_widget.all_staff_widgets.values():
                            if subject.teacher.id in teacher_filtered_dict:
                                teacher_filtered_dict[subject.teacher.id].remove_class(subject.id, id)
            
            self.timetable_editor.delete_timetable_class(self.class_level.classes[id])
            SCHOOL.class_levels.remove_class(self.id, id)
            
            self.main_area.removeWidget(option)
            
            option.deleteLater()
            
            self._parent.window().saved_state_changed.emit(True)
        
        option.deleted.connect(remove_option)
        
        # Add to grid and wrap to next row if needed
        self.main_area.addWidget(option)
        
        if is_new:
            option.start_editing()
            self._parent.window().saved_state_changed.emit(True)


class SelectWidget(BaseWidget):
    def __init__(self, parent: BaseSelectionList, id: ID, text: str, host_container_layout: QVBoxLayout, on_remove: Callable[[ID], None], on_opp_remove: Callable[[ID], None], window: QMainWindow):
        super().__init__(QHBoxLayout)
        
        self.id = id
        self.text = text
        self._parent = parent
        self._window = window
        self.host_container_layout = host_container_layout
        
        self.on_remove = on_remove
        self.on_opp_remove = on_opp_remove
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(self.text)
        
        self.addWidget(label)
        self.addStretch()
        
        self.clicked.connect(self.sl_clicked)
    
    def sl_clicked(self, a0):
        self._window.saved_state_changed.emit(True)
        
        self._parent.removeWidget(self)
        
        insert_index, widget = self.get_new_widget_index()
        
        self._parent.insertWidget(insert_index, widget)
        
        self.on_remove(self.id)
    
    def get_new_widget_index(self) -> tuple[int, "SelectWidget"]:
        raise NotImplementedError()

class _SL_SelectedWidget(SelectWidget):
    def __init__(self, parent: BaseSelectionList, id: ID, text: str, host_container_layout: QVBoxLayout, on_remove, on_opp_remove, window):
        super().__init__(parent, id, text, host_container_layout, on_remove, on_opp_remove, window)
        
        self.setProperty("class", "SelectedSelectionListEntry")
    
    def get_new_widget_index(self):
        insert_index = self.host_container_layout.count() - 1
        
        for i in range(self.host_container_layout.count() - 1, -1, -1):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_UnSelectedWidget):
                insert_index = i
                break
        
        return insert_index, _SL_UnSelectedWidget(self._parent, self.id, self.text, self.host_container_layout, self.on_opp_remove, self.on_remove, self._window)

class _SL_UnSelectedWidget(SelectWidget):
    def __init__(self, parent: BaseSelectionList, id: ID, text: str, host_container_layout: QVBoxLayout, on_remove, on_opp_remove, window):
        super().__init__(parent, id, text, host_container_layout, on_remove, on_opp_remove, window)
        
        self.setProperty("class", "UnselectedSelectionListEntry")
    
    def get_new_widget_index(self):
        insert_index = 0
        
        for i in range(self.host_container_layout.count()):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_SelectedWidget):
                insert_index = i + 1
        
        return insert_index, _SL_SelectedWidget(self._parent, self.id, self.text, self.host_container_layout, self.on_opp_remove, self.on_remove, self._window)

