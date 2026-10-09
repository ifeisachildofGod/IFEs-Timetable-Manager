
from imports import *

from .base import *
from .timetable import *
from .user_interface import *

from AttendanceApp import AttendanceManager


class Subject_SelectionList(BaseSelectionList[Teacher]):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.subject: Subject = SCHOOL.subjects[id]
        
        self.combined_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and id in s.classes]
        
        selected, scope = self._get_list_data(id)
        
        super().__init__(parent, id, title, selected.items(), scope)
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
    
    def _get_list_data(self, id: ID):
        selected = {t_id: teacher for t_id, teacher in SCHOOL.teachers.items() if id in teacher.subjects}
        
        scope = SCHOOL.teachers
        if next(
                (
                    False
                    for cls in
                    self.subject.classes.values()
                    if (
                        (id in cls.subjects and cls.subjects[id].teacher is None) or
                        next(
                            (
                                True
                                for s in
                                self.combined_subjects
                                if (
                                    s.id in cls.subjects and
                                    next(
                                        (
                                            True
                                            for s_s in
                                            cls.subjects[s.id].subjects
                                            if s_s.id == id and s_s.teacher is None
                                        ),
                                        False
                                    )
                                )
                            ),
                            False
                        )
                    )
                ),
                True
            ):
            scope = selected.copy()
        
        return selected, scope
    
    def item_selected(self, id: ID, _):
        assign_teacher(SCHOOL.teachers[id], self.id, self.attendance_manager)
    
    def item_removed(self, id: ID, _):
        c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and self.id in s.classes]
        
        deassign_teacher(SCHOOL.teachers[id], self.id, self.timetable_editor, self.attendance_manager, c_subjects)
        
        _, scope = self._get_list_data(self.id)
        selected_ids = [item_id for item_id, item_widget in self.widgets.items() if isinstance(item_widget, SL_SelectedWidget)]
        
        for item_id, item in scope.items():
            if item_id not in selected_ids and item_id not in self.widgets:
                self.insertWidget(len(self.widgets), SL_UnSelectedWidget(self, item_id, item.name.full(), self.item_selected, self.item_removed, self._parent.window()))

class CombinedSubject_SelectionList(BaseSelectionList[Subject]):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.c_subject: CombinedSubject = SCHOOL.subjects[id]
        
        self.selected_items = {s.id: s for s in self.c_subject.subjects}
        self.full_scope = {s_id: s for s_id, s in SCHOOL.subjects.items() if self._scope_check(s)}
        
        super().__init__(parent, id, title, self.selected_items.items(), self.full_scope)
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
    
    def _scope_check(self, subject: Subject | CombinedSubject):
        return isinstance(subject, Subject) and subject.classes
    
    def item_selected(self, id, _):
        subject = SCHOOL.subjects[id]
        assign_combined_subject_sub_subject(self.c_subject, subject, self._parent)
        
        for s_id, s in SCHOOL.subjects.items():
            if not self._scope_check(s) and s_id in self.full_scope:
                self.full_scope.pop(s_id)
                self.removeWidget(self.widgets[s_id])
    
    def item_removed(self, id, _):
        deassign_combined_subject_sub_subject(self.c_subject, id, self.timetable_editor, self.attendance_manager, self._parent)
        
        for s_id, s in SCHOOL.subjects.items():
            if self._scope_check(s) and s_id not in self.full_scope and s_id not in self.selected_items:
                self.full_scope[s_id] = s
                self.insertWidget(len(self.full_scope) - 1, SL_UnSelectedWidget(self, s_id, s.name.full(), self.item_selected, self.item_removed, self._parent.window()))

class Teacher_SelectionList(BaseSelectionList[Subject]):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        self.teacher = SCHOOL.teachers[id]
        
        self.combined_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject)]
        scope = {s.id: s for s in SCHOOL.subjects.values() if self._scope_check(id, s)}
        
        super().__init__(parent, id, title, self.teacher.subjects.items(), scope)
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
    
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
    
    def item_selected(self, id, _):
        assign_teacher(self.teacher, id, self.attendance_manager)
    
    def item_removed(self, id, _):
        c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and id in s.classes]
        
        deassign_teacher(self.teacher, id, self.timetable_editor, self.attendance_manager, c_subjects)

class Subject_DropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.__init = True
        
        self.id = id
        self._parent = parent
        self.subject = SCHOOL.subjects[self.id]
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and self.id in s.classes]
        
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
            assign_subject_class(self.subject, cls, self.timetable_editor)
        else:
            deassign_subject_class(self.id, cls, self.timetable_editor, self.attendance_manager, self.c_subjects)

class CombinedSubject_DropdownCheckBoxes(BaseSettingDialog):
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
        
        all_clicked = []
        
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
            
            all_clicked.extend(to_be_clicked)
            
            widgets.append(main_widget := WidgetDropdown(cls.level.name.full(), self.class_check_box_tracker[subject.id]["widget"][cls.level.id]))
            
            main_widget.header.addWidget(select_all_check_box)
            
            self.class_check_box_tracker[subject.id]["icon"][cls.level.id] = main_widget.toogle_icon
        
        for cb in all_clicked:
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
            assign_combined_subject_sub_subject_class(self.combined_subject, subject.id, cls, self.timetable_editor, self.attendance_manager)
        else:
            deassign_combined_subject_sub_subject_class(self.combined_subject, subject.id, cls, self.timetable_editor, self.attendance_manager)

class Teacher_DropdownCheckBoxes(BaseSettingDialog):
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
        
        all_clicked: list[QCheckBox] = []
        
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
                    all_clicked.append(is_random_check_box)
                
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
                
                all_clicked.extend(to_be_clicked)
                
                container_widget.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        for cb in all_clicked:
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
            assign_subject_class_teacher(self.teacher, subject.id, cls, self.timetable_editor, self.attendance_manager)
        else:
            deassign_subject_class_teacher(subject.id, cls, self.timetable_editor, self.attendance_manager)
    
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
            assign_combined_subject_class_teacher(c_subject.id, u_subject.id, self.teacher, cls, self.timetable_editor, self.attendance_manager)
        else:
            deassign_combined_subject_class_teacher(c_subject.id, u_subject.id, cls, self.timetable_editor, self.attendance_manager)

class ClassLevel_OccuranceEditor(BaseSettingDialog):
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
                    self.scroll_to(widget, 100)
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
                            next((True for s in cls.subjects[subject_id].subjects if s.teacher is not None), False)
                        )
                    ):
                    self.timetable_editor.timetable_widgets[cls.level.id][cls_id].change_subject_amount(subject_id, number)
            
            if not self.__init:
                self._parent.window().saved_state_changed.emit(True)
        
        return text_changed_func

class ClassLevel_ClassMaker(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.timetable_editor = timetable_editor
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.class_level = SCHOOL.class_levels[self.id]
        
        self.max_cols = 4  # Maximum number of columns before wrapping
        
        self.main_area = BaseFlowGridWidget(self.max_cols)
        self.main_area.setVerticalSpacing(4)
        self.main_area.setContentsMargins(0, 0, 0, 0)
        self.main_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
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
            self.scroll_to(widget, 100)
            widget.setFocus()
        
        QTimer.singleShot(200, func)
    
    def add_option(self, id: str | None = None, text: str | None = None):
        option = EditableCancelableEntry(text)
        
        is_new = id is None
        
        if is_new:
            id = NEW_CLASS_ID(self.class_level.id)
            
            cls = Class(id, "", self.class_level, {})
            
            SCHOOL.class_levels.add_class(self.id, cls)
            self.timetable_editor.add_timetable_class(cls)
        else:
            cls = self.class_level.classes[id]
            cls.SCHOOL = SCHOOL
        
        def update_option():
            cls.name = option.get_text()
            class_name_update(cls.id, self.timetable_editor, self.attendance_manager)
            
            self._parent.window().saved_state_changed.emit(True)
        
        update_option()
        
        option.finished_editing_signal.connect(update_option)
        
        def remove_option():
            delete_class(id, self.timetable_editor, self.attendance_manager)
            
            self.main_area.removeWidget(option)
            option.deleteLater()
            
            self._parent.window().saved_state_changed.emit(True)
        
        option.deleted.connect(remove_option)
        
        # Add to grid and wrap to next row if needed
        self.main_area.addWidget(option, alignment=Qt.AlignmentFlag.AlignCenter)
        
        if is_new:
            option.start_editing()
            self.main_area.scroll_to(self.main_area.widgets[-1], 100)
            
            self._parent.window().saved_state_changed.emit(True)

class Prefect_ClassSelector(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.setFixedSize(250, 200)
        
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.prefect = SCHOOL.prefects[self.id]
        
        overflow_limit = 10
        
        col_widget_1 = BaseWidget()
        col_widget_2 = BaseWidget()
        
        classes = [cls for cls_level in SCHOOL.class_levels.values() for cls in cls_level.classes.values()]
        
        for i, cls in enumerate(classes):
            rb = QRadioButton(f"{cls.level.name.full()} {cls.name}")
            rb.setChecked(bool(self.prefect.cls and self.prefect.cls.id == cls.id))
            rb.clicked.connect(self._make_select_func(cls))
            
            if len(classes) < overflow_limit or (len(classes) < overflow_limit * 2 and (i + 1) // overflow_limit == 0) or (len(classes) >= overflow_limit * 2 and (i + 1) <= len(classes) / 2):
                col_widget_1.addWidget(rb, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                col_widget_2.addWidget(rb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        col_widget_1.addStretch()
        col_widget_2.addStretch()
        
        main_widget = BaseWidget(QHBoxLayout)
        
        main_widget.addWidget(col_widget_1, stretch=5)
        main_widget.addWidget(col_widget_2, stretch=5)
        
        self.addWidget(main_widget)
    
    def _make_select_func(self, cls: Class):
        def func():
            self.prefect.cls = cls
        
        return func

class Prefect_PostAssigner(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.prefect = SCHOOL.prefects[self.id]
        
        main_widget = BaseScrollWidget()
        
        add_new_pb = QPushButton("Add New")
        
        self.addWidget(main_widget)
        self.addWidget(add_new_pb)

class Prefect_DutyAssigner(BaseSettingDialog):
    def __init__(self, parent: BaseSettingEntry, id: ID, title: str, attendance_manager: AttendanceManager):
        super().__init__(title)
        
        self.setFixedSize(650, 450)
        self.setContentsMargins(10, 10, 10, 10)
        
        self.attendance_manager = attendance_manager
        
        self.id = id
        self._parent = parent
        self.prefect = SCHOOL.prefects[self.id]
        
        self.duty_widgets: dict[str, list[EditableCancelableEntry]] = {}
        
        if self.prefect.cls:
            for day in self.prefect.cls.level.weekdays:
                main_widget = BaseFlowGridWidget(4)
                main_widget.setMinimumHeight(150)
                main_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                
                day_widg = LabeledField(day, main_widget)
                
                add_duty_button = QPushButton("Add Duty")
                add_duty_button.clicked.connect(self._make_add_duty_func(main_widget, day))
                
                day_widg.title_area.addWidget(add_duty_button)
                
                if day in self.prefect.duties:
                    for duty in self.prefect.duties[day]:
                        main_widget.addWidget(self._duty_entry(main_widget, day, duty))
                
                self.addWidget(day_widg)
            
            self.addStretch()
    
    def _make_entry_action_funcs(self, main_widget: BaseWidget, entry: EditableCancelableEntry, day: str):
        def update():
            index = self.duty_widgets[day].index(entry)
            
            self.prefect.duties[day][index] = entry.get_text()
            self.attendance_manager.update_staff_list_prefect_duty(self.prefect.id, day, index)
            
            self._parent.window().saved_state_changed.emit(True)
        
        def remove():
            index = self.duty_widgets[day].index(entry)
            
            self.prefect.duties[day].pop(index)
            self.duty_widgets[day].pop(index)
            
            if not self.prefect.duties[day]:
                self.prefect.duties.pop(day)
                self.duty_widgets.pop(day)
            
            main_widget.removeWidget(entry)
            entry.deleteLater()
            
            self.attendance_manager.remove_staff_list_prefect_duty(self.prefect.id, day, index)
            
            self._parent.window().saved_state_changed.emit(True)
        
        return update, remove
    
    def _duty_entry(self, main_widget: BaseWidget, day: str, duty: Optional[str] = None):
        duty_entry = EditableCancelableEntry(duty)
        
        update_option, remove_option = self._make_entry_action_funcs(main_widget, duty_entry, day)
        
        duty_entry.finished_editing_signal.connect(update_option)
        duty_entry.deleted.connect(remove_option)
        
        if day not in self.duty_widgets:
            self.duty_widgets[day] = []
        
        self.duty_widgets[day].append(duty_entry)
        
        return duty_entry
    
    def _make_add_duty_func(self, main_widget: BaseWidget, day: str):
        def func():
            if day not in self.prefect.duties:
                self.prefect.duties[day] = []
            
            self.prefect.duties[day].append("")
            
            entry = self._duty_entry(main_widget, day)
            
            main_widget.addWidget(entry)
            main_widget.scroll_to(main_widget.widgets[-1], 100)
            entry.start_editing()
            
            self.attendance_manager.add_staff_list_prefect_duty(self.prefect.id, day, None)
            
            self._parent.window().saved_state_changed.emit(True)
        
        return func


# Assignments
def deassign_subject_class_teacher(subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    if subjectID not in cls.subjects:
        return
    
    timetable_editor.timetable_widgets[cls.level.id][cls.id].change_subject_amount(subjectID, 0)
    
    cls_subject = cls.subjects[subjectID]
    
    if cls_subject.teacher is not None:
        for teacher_filtered_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
            if cls_subject.teacher.id in teacher_filtered_dict:
                teacher_filtered_dict[cls_subject.teacher.id].remove_class(subjectID, cls.id)
        
        cls_subject.teacher = None

def deassign_subject_class(subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, c_subjects: Optional[list[CombinedSubject]] = None):
    deassign_subject_class_teacher(subjectID, cls, timetable_editor, attendance_manager)
    
    if c_subjects:
        for c_subject in c_subjects:
            deassign_combined_subject_sub_subject_class(c_subject, subjectID, cls, timetable_editor, attendance_manager)
    
    SCHOOL.subjects[subjectID].classes.pop(cls.id)
    
    if subjectID in cls.subjects:
        cls.subjects.pop(subjectID)
        
        if subjectID in cls.level.subjects_occurence and next((False for c in cls.level.classes.values() if subjectID in c.subjects), True):
            cls.level.subjects_occurence.pop(subjectID)
    
    combination_widget = timetable_editor.combination_widgets[cls.level.id]
    
    for set_index, combo_dict in enumerate(combination_widget.combo_box_widgets):
        for cb_index, cb in enumerate(combo_dict["subjects"].copy()):
            if subjectID not in cls.level.subjects_occurence:
                continue
            
            curr_index = cb.currentIndex()
            
            if (index := next((i for i in range(cb.count()) if cb.itemData(i) == subjectID), None)) is not None:
                if index == curr_index:
                    combination_widget.subject_cancel_button_widgets[set_index]["subjects"][cb_index].click()
                else:
                    cb.removeItem(index)

def deassign_teacher(teacher: Teacher, subjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, c_subjects: Optional[list[CombinedSubject]] = None):
    if subjectID not in teacher.subjects:
        return
    
    subject = teacher.subjects.pop(subjectID)
    
    for cls in subject.classes.values():
        if subject.id not in cls.subjects:
            continue
        
        cls_subject = cls.subjects[subject.id]
        
        if cls_subject.teacher and cls_subject.teacher.id == teacher.id:
            deassign_subject_class_teacher(subject.id, cls, timetable_editor, attendance_manager)
    
    if c_subjects:
        for c_subject in c_subjects:
            for cls in c_subject.classes[subject.id].values():
                cls_subject = next(s for s in cls.subjects[c_subject.id].subjects if s.id == subjectID)
                
                if cls_subject.teacher and cls_subject.teacher.id == teacher.id:
                    deassign_combined_subject_class_teacher(c_subject.id, subject.id, cls, timetable_editor, attendance_manager)
    
    for staff_widget_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
        if teacher.id in staff_widget_dict:
            staff_widget_dict[teacher.id].remove_subject(subject)

def deassign_combined_subject_class_teacher(combinedSubjectID: ID, subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    if combinedSubjectID not in cls.subjects:
        return
    
    cls_subject = cls.subjects[combinedSubjectID]
    
    if next((False for s in cls_subject.subjects if s.id != subjectID and s.teacher is not None), True):
        timetable_editor.timetable_widgets[cls.level.id][cls.id].change_subject_amount(combinedSubjectID, 0)
    
    cls_focus_subject = next(s for s in cls_subject.subjects if s.id == subjectID)
    
    if cls_focus_subject.teacher is not None:
        for teacher_filtered_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
            if cls_focus_subject.teacher.id in teacher_filtered_dict:
                teacher_filtered_dict[cls_focus_subject.teacher.id].remove_class(subjectID, cls.id)
        
        cls_focus_subject.teacher = None
    
    if cls_subject.name.first is None:
        timetable_editor.update_subject_name(cls_subject)

def deassign_combined_subject_sub_subject_class(c_subject: CombinedSubject, subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    deassign_combined_subject_class_teacher(c_subject.id, subjectID, cls, timetable_editor, attendance_manager)
    
    if cls.id in c_subject.classes[subjectID]:
        c_subject.classes[subjectID].pop(cls.id)
        
        if c_subject.id in cls.subjects and next((False for subj_classes in c_subject.classes.values() if next((True for c in subj_classes.values() if c.id == cls.id), False)), True):
            cls.subjects.pop(c_subject.id)
        
        if c_subject.id in cls.level.subjects_occurence and next((False for subj_classes in c_subject.classes.values() if next((True for c in subj_classes.values() if c.level.id == cls.level.id), False)), True):
            cls.level.subjects_occurence.pop(c_subject.id)
    
    if subjectID not in cls.subjects:
        cls.subjects[subjectID] = SCHOOL.subjects[subjectID].passCopy()
        
        if subjectID not in cls.level.subjects_occurence:
            per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
            
            week_total = (cls.level.period_amount - 1) * len(cls.level.weekdays)
            min_rem = min(week_total - sum(cls.level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls.level.subjects_occurence) for cls in cls.level.classes.values())
            
            cls.level.subjects_occurence[subjectID] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))
    
    combination_widget = timetable_editor.combination_widgets[cls.level.id]
    
    for set_index, combo_dict in enumerate(combination_widget.combo_box_widgets):
        for cb_index, cb in enumerate(combo_dict["subjects"].copy()):
            if subjectID not in cls.level.subjects_occurence:
                continue
            
            curr_index = cb.currentIndex()
            
            if (index := next((i for i in range(cb.count()) if cb.itemData(i) == subjectID), None)) is not None:
                if index == curr_index:
                    combination_widget.subject_cancel_button_widgets[set_index]["subjects"][cb_index].click()
                else:
                    cb.removeItem(index)

def deassign_combined_subject_sub_subject(c_subject: CombinedSubject, subjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, parent: BaseSettingEntry):
    for cls in c_subject.classes[subjectID].copy().values():
        deassign_combined_subject_sub_subject_class(c_subject, subjectID, cls, timetable_editor, attendance_manager)
    
    c_subject.classes.pop(subjectID)
    c_subject.subjects.pop(next(i for i, s in enumerate(c_subject.subjects) if s.id == subjectID))
    
    if not parent.simple_line_edit.text():
        parent.simple_name_changed(parent.simple_line_edit.text(), None)

def assign_subject_class_teacher(teacher: Teacher, subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    cls.subjects[subjectID].teacher = teacher
    timetable_editor.timetable_widgets[cls.level.id][cls.id].change_subject_amount(subjectID, cls.level.subjects_occurence[subjectID].week_max)
    
    for teacher_filtered_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
        if teacher.id in teacher_filtered_dict:
            teacher_filtered_dict[teacher.id].add_class(subjectID, cls)

def assign_subject_class(subject: Subject, cls: Class, timetable_editor: SchoolTimetableEditor):
    subject.classes[cls.id] = cls
    cls.subjects[subject.id] = subject.passCopy()
    
    if subject.id not in cls.level.subjects_occurence:
        per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
        
        week_total = (cls.level.period_amount - 1) * len(cls.level.weekdays)
        min_rem = min(week_total - sum(cls.level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls.level.subjects_occurence) for cls in cls.level.classes.values())
        
        cls.level.subjects_occurence[subject.id] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))
    
    for combo_dict in timetable_editor.combination_widgets[cls.level.id].combo_box_widgets:
        for cb in combo_dict["subjects"]:
            if next((False for i in range(cb.count()) if cb.itemData(i) == subject.id), True):
                cb.addItem(subject.name.full(), userData=subject.id)

def assign_teacher(teacher: Teacher, subjectID: ID, attendance_manager: AttendanceManager):
    subject = SCHOOL.subjects[subjectID]
    
    teacher.subjects[subjectID] = subject
    
    for staff_widget_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
        if teacher.id in staff_widget_dict:
            staff_widget_dict[teacher.id].add_subject(subject)

def assign_combined_subject_class_teacher(combinedSubjectID: ID, subjectID: ID, teacher: Teacher, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    cls_subject = cls.subjects[combinedSubjectID]
    
    c_cls_subject = next(s for s in cls_subject.subjects if s.id == subjectID)
    c_cls_subject.teacher = teacher
    
    if next((False for s in cls_subject.subjects if s.id != subjectID and s.teacher is not None), True):
        timetable_editor.timetable_widgets[cls.level.id][cls.id].change_subject_amount(combinedSubjectID, cls.level.subjects_occurence[combinedSubjectID].week_max)
    
    for teacher_filtered_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
        if teacher.id in teacher_filtered_dict:
            teacher_filtered_dict[teacher.id].add_class(subjectID, cls)
    
    if cls_subject.name.first is None:
        timetable_editor.update_subject_name(cls_subject)

def assign_combined_subject_sub_subject_class(c_subject: CombinedSubject, subjectID: ID, cls: Class, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    c_subject.classes[subjectID][cls.id] = cls
    
    if subjectID in cls.subjects:
        deassign_subject_class_teacher(subjectID, cls, timetable_editor, attendance_manager)
        cls.subjects.pop(subjectID)
    
    cls.subjects[c_subject.id] = c_subject.passCopy()
    
    if next((False for c in cls.level.classes.values() if subjectID in c.subjects), True):
        cls.level.subjects_occurence.pop(subjectID)
    
    if c_subject.id not in cls.level.subjects_occurence:
        per_day, per_week = SCHOOL.settings.DEFAULT_occurance_data
        
        week_total = (cls.level.period_amount - 1) * len(cls.level.weekdays)
        min_rem = min(week_total - sum(cls.level.subjects_occurence[s.id].week_max for s in cls.subjects.values() if s.id in cls.level.subjects_occurence) for cls in cls.level.classes.values())
        
        cls.level.subjects_occurence[c_subject.id] = SubjectOccurrance(min(per_day, min_rem), min(per_week, min_rem))

def assign_combined_subject_sub_subject(c_subject: CombinedSubject, subject: Subject, parent: BaseSettingEntry):
    c_subject.classes[subject.id] = {}
    c_subject.subjects.append(subject)
    
    if not parent.simple_line_edit.text():
        parent.simple_name_changed(parent.simple_line_edit.text(), None)

# Deletions
def delete_subject(subjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, subjects_setting_widget: BaseSettingWidget):
    subject: Subject = SCHOOL.subjects[subjectID]
    c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and subjectID in s.classes]
    
    if c_subjects:
        for c_subject in c_subjects:
            deassign_combined_subject_sub_subject(c_subject, subjectID, timetable_editor, attendance_manager, subjects_setting_widget.widgets[c_subject.id])
    
    for cls in subject.classes.copy().values():
        deassign_subject_class(subjectID, cls, timetable_editor, attendance_manager)
    
    for teacher in SCHOOL.teachers.values():
        if subjectID in teacher.subjects:
            deassign_teacher(teacher, subjectID, timetable_editor, attendance_manager)
    
    attendance_manager.punctuality_graph_widget.delete_subject(subjectID)
    attendance_manager.attendance_chart_widget.delete_subject(subjectID)

def delete_combined_subject(combinedSubjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    c_subject: CombinedSubject = SCHOOL.subjects[combinedSubjectID]
    
    for subjectID, subject_classes in c_subject.classes.copy().items():
        for cls in subject_classes.copy().values():
            deassign_combined_subject_sub_subject_class(c_subject, subjectID, cls, timetable_editor, attendance_manager)
        
        deassign_combined_subject_sub_subject(c_subject, subjectID, timetable_editor, attendance_manager)
        
        attendance_manager.punctuality_graph_widget.delete_subject(subjectID)
    
def delete_teacher(teacherID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    teacher = SCHOOL.teachers[teacherID]
    
    for subjectID in teacher.subjects.copy():
        c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and subjectID in s.classes]
        
        deassign_teacher(teacher, subjectID, timetable_editor, attendance_manager, c_subjects)
    
    attendance_manager.staff_list_widget.delete_staff(teacher)

def delete_class(classID: CLASS_ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    cls = SCHOOL.class_levels[classID.class_level_id].classes[classID]
    
    for subject in cls.subjects.copy().values():
        if isinstance((c_subject := subject), CombinedSubject):
            for subSubjectID in c_subject.classes:
                deassign_combined_subject_sub_subject_class(c_subject, subSubjectID, cls, timetable_editor, attendance_manager)
    
    for subjectID, subject in cls.subjects.copy().items():
        if isinstance(subject, Subject):
            deassign_subject_class(subjectID, cls, timetable_editor, attendance_manager)
    
    timetable_editor.delete_timetable_class(cls)
    SCHOOL.class_levels.remove_class(cls.level.id, classID)

def delete_class_level(classLevelID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    class_level: ClassLevel = SCHOOL.class_levels[classLevelID]
    
    for cls in class_level.classes.values():
        delete_class(cls, timetable_editor, attendance_manager)
    
    timetable_editor.delete_timetable_level(classLevelID)
    
    SCHOOL.gen_data.combined_subjects.pop(classLevelID)
    SCHOOL.settings.TEACHER_rsma_mapping.pop(classLevelID)
    SCHOOL.settings.EXPORT_selected_classes.pop(classLevelID)
    SCHOOL.settings.TIMETABLE_time_settings.pop(classLevelID)

# Names Update
def subject_name_update(subjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, subjects_setting_widget: BaseSettingWidget):
    subject: Subject = SCHOOL.subjects[subjectID]
    
    cls_lvl_ids = []
    
    for cls in subject.classes.values():
        if cls.level.id not in cls_lvl_ids:
            cls_lvl_ids.append(cls.level.id)
        else:
            continue
        
        for combo_dict in timetable_editor.combination_widgets[cls.level.id].combo_box_widgets:
            for cb in combo_dict["subjects"]:
                if subjectID in cls.level.subjects_occurence:
                    curr_index = cb.currentIndex()
                    
                    if (c_index := next((i for i in range(cb.count()) if cb.itemData(i) == subjectID), None)) is not None:
                        cb.blockSignals(True)
                        
                        cb.removeItem(c_index)
                        cb.addItem(subject.name.full(), userData=subjectID)
                        
                        if c_index == curr_index:
                            cb.setCurrentIndex(cb.count() - 1)
                        
                        cb.blockSignals(False)
    
    c_subjects = [s for s in SCHOOL.subjects.values() if isinstance(s, CombinedSubject) and subjectID in s.classes and s.name.first is None]
    
    for teacher in SCHOOL.teachers.values():
        if subjectID in teacher.subjects:
            for teacher_widget_dict in attendance_manager.staff_list_widget.all_staff_widgets.values():
                if teacher.id in teacher_widget_dict:
                    teacher_widget_dict[teacher.id].update_subject_name(subject)
    
    timetable_editor.update_subject_name(subject)
    
    for c_subject in c_subjects:
        if c_subject.id in subjects_setting_widget.widgets:
            combined_subject_name_update(c_subject.id, timetable_editor, attendance_manager, subjects_setting_widget.widgets[c_subject.id])

def combined_subject_name_update(combinedSubjectID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager, parent: BaseSettingEntry):
    c_subject = SCHOOL.subjects[combinedSubjectID]
    
    cls_lvl_ids = []
    
    for subj_clses in c_subject.classes.values():
        for cls in subj_clses.values():
            if cls.level.id not in cls_lvl_ids:
                cls_lvl_ids.append(cls.level.id)
            else:
                continue
            
            for combo_dict in timetable_editor.combination_widgets[cls.level.id].combo_box_widgets:
                for cb in combo_dict["subjects"]:
                    curr_index = cb.currentIndex()
                    index = next((i for i in range(cb.count()) if cb.itemData(i) == combinedSubjectID), None)
                    
                    if index is not None:
                        cb.blockSignals(True)
                        
                        cb.removeItem(index)
                        cb.addItem(c_subject.name.full(), userData=combinedSubjectID)
                        
                        if index == curr_index:
                            cb.setCurrentIndex(cb.count() - 1)
                        
                        cb.blockSignals(False)
    
    if not parent.simple_line_edit.text():
        if c_subject.name.abbrev:
            default = f"Default: {c_subject.name.abbrev}"
            parent.status_widget.removeLinient("EmptyNameWarning")
        else:
            default = "No Child Subjects"
            parent.simple_name_empty("")
        
        parent.simple_line_edit.setPlaceholderText(f"{parent.simple_placeholder}; {default}")
    
    timetable_editor.update_subject_name(c_subject)
    attendance_manager.update_staff_list_teacher_subject_name(c_subject)

def teacher_name_update(teacherID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    teacher = SCHOOL.teachers[teacherID]
    attendance_manager.update_staff_list_staff_name(teacherID)
    
    for subjectID, subject in teacher.subjects.items():
        for cls in subject.classes.values():
            if (cls_subj := cls.subjects.get(subjectID, None)) and cls_subj.teacher and cls_subj.teacher.id == teacherID:
                timetable_editor.update_subject_name(subject, cls)

def class_name_update(classID: CLASS_ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    cls = SCHOOL.class_levels[classID.class_level_id].classes[classID]
    
    timetable_editor.update_class_name(cls)
    attendance_manager.update_staff_list_teacher_class_name(cls)
    
    for combo_dict in timetable_editor.combination_widgets[cls.level.id].combo_box_widgets:
        for cb in combo_dict["classes"]:
            curr_index = cb.currentIndex()
            index = next((i for i in range(cb.count()) if cb.itemData(i) == cls.id), None)
            
            if index is not None:
                cb.blockSignals(True)
                
                cb.removeItem(index)
                cb.addItem(f"{cls.level.name.full()} {cls.name}", userData=cls.id)
                
                if index == curr_index:
                    cb.setCurrentIndex(cb.count() - 1)
                
                cb.blockSignals(False)

def class_level_name_update(classLevelID: ID, timetable_editor: SchoolTimetableEditor, attendance_manager: AttendanceManager):
    class_level = SCHOOL.class_levels[classLevelID]
    
    timetable_editor.update_class_level_name(class_level)
    for cls in class_level.classes.values():
        attendance_manager.update_staff_list_teacher_class_name(cls)
    
    for combo_dict in timetable_editor.combination_widgets[classLevelID].combo_box_widgets:
        for cb in combo_dict["classes"]:
            cb.blockSignals(True)
            
            curr_c_id = cb.itemData(cb.currentIndex())
            
            for _ in range(cb.count()):
                c_id = cb.itemData(0)
                cls = class_level.classes[c_id]
                
                cb.removeItem(0)
                cb.addItem(f"{class_level.name.full()} {cls.name}", userData=c_id)
            
            cb.setCurrentIndex(next(i for i in range(cb.count()) if curr_c_id == cb.itemData(i)))
            
            cb.blockSignals(False)

