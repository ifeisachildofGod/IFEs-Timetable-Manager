
from typing import Generator

from imports import *

from widgets.base import *
from widgets.timetable import *
from widgets.user_interface import *


class BaseSelectionList(BaseSettingDialog):
    def __init__(self, id: ID, title: str, selected_items: Generator[tuple[ID, Subject | Teacher], None, None], content_scope: Global):
        super().__init__(title)
        
        self.id = id
        self.setFixedSize(400, 300)
        
        selected_ids = []
        
        # Add selected items
        for item_id, item in selected_items:
            selected_ids.append(item_id)
            widget = _SL_SelectedWidget(item_id, item.name.full(), self.getLayout(), self.item_selected, self.item_removed)
            
            self.addWidget(widget)
        
        # Add unselected items
        for item_id, item in content_scope:
            if item_id not in selected_ids:
                widget = _SL_UnSelectedWidget(item_id, item.name.full(), self.getLayout(), self.item_selected, self.item_removed)
                
                self.addWidget(widget)
        
        self.addStretch()
    
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
    def __init__(self, parent: BaseSettingWidget, id, title):
        super().__init__(id, title, ((t_id, teacher) for t_id, teacher in SCHOOL.teachers if id in teacher.subjects), SCHOOL.teachers)
        
        self.subject = SCHOOL.subjects[self.id]
    
    def item_removed(self, id: ID):
        SCHOOL.teachers[id].subjects.pop(self.id)
        
        for _, cl in SCHOOL.class_levels:
            cl.delete_subject(self.id, id)
    
    def item_selected(self, id: ID):
        SCHOOL.teachers[id].subjects[self.id] = self.subject

class TeacherSelectionList(BaseSelectionList):
    def __init__(self, parent: BaseSettingWidget, id, title):
        self.teacher = SCHOOL.teachers[id]
        
        super().__init__(id, title, iter(self.teacher.subjects.items()), SCHOOL.subjects)
    
    def item_removed(self, id: ID):
        self.teacher.subjects.pop(id)
        
        for _, cl in SCHOOL.class_levels:
            cl.delete_subject(id, self.id)
    
    def item_selected(self, id: ID):
        self.teacher.subjects[id] = SCHOOL.subjects[id]

class SubjectDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingWidget, id: ID, title: str):
        super().__init__(title)
        
        self.id = id
        self.subject = SCHOOL.subjects[self.id]
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.class_check_box_tracker = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "widget": {}}
        
        self.is_init = True
        
        for widget in self._create_checkbox_widgets():
            self.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.is_init = False
        
        self.addStretch()
    
    def go_to(self, lvl_id: ID, cls_id: Optional[ID] = None):
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
    
    def _create_checkbox_widgets(self):
        widgets: list[QWidget] = []
        all_clicked_checkboxes: list[QCheckBox] = []
        
        for lvl_id, cls_lvl in SCHOOL.class_levels:
            check_box = QCheckBox()
            check_box.clicked.connect(self.make_main_checkbox_func(lvl_id))
            
            self.class_check_box_tracker["sub_cbs"][lvl_id] = {}
            self.class_check_box_tracker["main_cb"][lvl_id] = check_box
            self.class_check_box_tracker["widget"][lvl_id], to_be_clicked = self.make_dp_widget(lvl_id, cls_lvl)
            
            main_widget = WidgetDropdown(cls_lvl.name.full(), self.class_check_box_tracker["widget"][lvl_id])
            main_widget.header.addWidget(check_box)
            
            self.class_check_box_tracker["icon"][lvl_id] = main_widget.toogle_icon
            
            all_clicked_checkboxes.extend(to_be_clicked)
            
            widgets.append(main_widget)
        
        for cb in all_clicked_checkboxes:
            cb.click()
        
        return widgets
    
    def make_dp_widget(self, lvl_id: ID, cls_lvl: ClassLevel):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in cls_lvl.classes.items():
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            dp_checkbox = QCheckBox()
            
            self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id] = dp_checkbox
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(lvl_id, cls_id))
            
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
                self.main_guy_is_clicked = True
                
                if is_on:
                    if not self.class_check_box_tracker["sub_cbs"][lvl_id]:
                        QMessageBox.critical(self, "Setting SDCB Error", "No class level option has been made for this class level")
                        self.main_guy_is_clicked = False
                        self.class_check_box_tracker["main_cb"][lvl_id].click()
                    else:
                        for c_box in self.class_check_box_tracker["sub_cbs"][lvl_id].values():
                            if not c_box.isChecked():
                                c_box.click()
                else:
                    for c_box in self.class_check_box_tracker["sub_cbs"][lvl_id].values():
                        if c_box.isChecked():
                            c_box.click()
                
                self.main_guy_is_clicked = False
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, lvl_id: ID, cls_id: ID):
        def checkbox_func(on):
            if not self.is_init:
                self.sub_checkbox_func(on, lvl_id, cls_id)
            
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
    
    def sub_checkbox_func(self, on: bool, lvl_id: ID, cls_id: ID):
        if on:
            self.subject.classes[cls_id] = SCHOOL.class_levels[lvl_id].classes[cls_id]
            SCHOOL.class_levels[lvl_id].classes[cls_id].subjects[self.id] = self.subject.passCopy()
            
            if self.id not in SCHOOL.class_levels[lvl_id].subjects_occurence:
                SCHOOL.class_levels[lvl_id].subjects_occurence[self.id] = SubjectOccurrance(*SCHOOL.settings.DEFAULT_occurance_data)
        else:
            self.subject.classes.pop(cls_id)
            SCHOOL.class_levels[lvl_id].classes[cls_id].subjects.pop(self.id)
            
            for cls in SCHOOL.class_levels[lvl_id].classes.values():
                if self.id in cls.subjects:
                    break
            else:
                SCHOOL.class_levels[lvl_id].subjects_occurence.pop(self.id)

class TeacherDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, parent: BaseSettingWidget, id: ID, title: str):
        super().__init__(title)
                
        self.id = id
        self.i_parent = parent
        self.teacher = SCHOOL.teachers[self.id]
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.subject_check_box_tracker = {}
        self.class_check_box_tracker = {}
        
        self.is_init = True
        
        for subject_id, subject in self.teacher.subjects.items():
            self.subject_check_box_tracker[subject_id] = {}
            self.class_check_box_tracker[subject_id] = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "max_random": {}, "widget": {}}
            
            self.subject_check_box_tracker[subject_id]["widget"] = self.make_subject_widget(subject)
            
            main_widget = WidgetDropdown(subject.name.full(), self.subject_check_box_tracker[subject_id]["widget"])
            
            self.subject_check_box_tracker[subject_id]["icon"] = main_widget.toogle_icon
            
            self.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
        
        self.is_init = False
    
    def go_to(self, subj_id: ID, lvl_id: Optional[ID], cls_id: Optional[ID]):
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
    
    def _create_checkbox_widgets(self, subject: Subject):
        widgets: list[QWidget] = []
        random_on_checkboxes: list[QCheckBox] = []
        
        cls_lvls = []
        for cls in subject.classes.values():
            if cls.level not in cls_lvls:
                cls_lvls.append(cls.level)
                
                def rsma_func(number: Optional[int]):
                    SCHOOL.settings.TEACHER_rsma_mapping[cls.level.id] = number
                
                max_random_text_input = NumberLineEdit(SCHOOL.settings.TEACHER_rsma_mapping[cls.level.id] if SCHOOL.settings.TEACHER_rsma_mapping[cls.level.id] is not None else 1, 1, len(cls.level.classes))
                max_random_text_input.edit.setToolTip("Maximum Classes Taught")
                max_random_text_input.setVisible(False)
                max_random_text_input.textChanged.connect(rsma_func)
                
                is_random_check_box = QCheckBox("Random")
                
                select_all_check_box = QCheckBox("All")
                select_all_check_box.clicked.connect(self.make_select_all_checkbox_func(subject, cls.level.id))
                
                if SCHOOL.settings.TEACHER_rsma_mapping[cls.level.id]:
                    random_on_checkboxes.append(is_random_check_box)
                
                self.class_check_box_tracker[subject.id]["sub_cbs"][cls.level.id] = {}
                self.class_check_box_tracker[subject.id]["main_cb"][cls.level.id] = select_all_check_box
                self.class_check_box_tracker[subject.id]["widget"][cls.level.id], to_be_clicked = self.make_dp_widget(subject, cls.level)
                
                main_widget = WidgetDropdown(cls.level.name.full(), self.class_check_box_tracker[subject.id]["widget"][cls.level.id])
                main_widget.header.addWidget(max_random_text_input)
                # main_widget.header.addWidget(is_random_check_box)
                main_widget.header.addWidget(select_all_check_box)
                
                is_random_check_box.clicked.connect(self.make_random_checkbox_func(subject, cls.level.id, main_widget, max_random_text_input, rsma_func))
                
                self.class_check_box_tracker[subject.id]["icon"][cls.level.id] = main_widget.toogle_icon
                
                random_on_checkboxes.extend(to_be_clicked)
                
                widgets.append(main_widget)
        
        for cb in random_on_checkboxes:
            cb.click()
        
        return widgets
    
    def make_subject_widget(self, subject: Subject):
        container_widget = BaseWidget()
        
        for widget in self._create_checkbox_widgets(subject):
            container_widget.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        container_widget.setVisible(False)
        
        return container_widget
    
    def make_dp_widget(self, subject: Subject, lvl: ClassLevel):
        dp_widget = BaseWidget()
        dp_widget.setProperty("class", "DPC_Body")
        dp_widget.setSpacing(2)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in lvl.classes.items():
            if subject.id not in SCHOOL.class_levels[lvl.id].classes[cls_id].subjects:
                continue
            
            u_subject = SCHOOL.class_levels[lvl.id].classes[cls_id].subjects[subject.id]
            
            optionState = u_subject.teacher is not None and u_subject.teacher.id == self.teacher.id
            is_disabled = u_subject.teacher is not None and u_subject.teacher.id != self.teacher.id
            
            option_widget = BaseWidget(QHBoxLayout)
            
            dp_title = QLabel(cls.name)
            dp_title.setDisabled(is_disabled)
            
            dp_checkbox = QCheckBox()
            dp_checkbox.setDisabled(is_disabled)
            
            self.class_check_box_tracker[subject.id]["sub_cbs"][lvl.id][cls_id] = dp_checkbox
            
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
    
    def make_link_func(self, s_id: ID, lvl_id: ID, cls_id: ID, teacher: Teacher):
        def func(e):
            self.close()
            
            def func1():
                widget = self.i_parent.go_to(teacher)
                
                QTimer.singleShot(500, lambda: func2(widget.dialog_widget_funcs[0]))
            
            def func2(d_func: Callable[[], BaseSettingDialog]):
                w = d_func()
                QTimer.singleShot(500, lambda: w.go_to(s_id, lvl_id, cls_id))
                
                w.exec()
            
            QTimer.singleShot(500, func1)
        
        return func
    
    def make_random_checkbox_func(self, subject: Subject, class_id: str, widget_dp: WidgetDropdown, max_random_text_input: QLineEdit, rsma_func: Callable[[Optional[int]], None]):
        def checkbox_func(on):
            if on:
                for c_box in self.class_check_box_tracker[subject.id]["sub_cbs"][class_id].values():
                    if c_box.isChecked():
                        c_box.click()
                
                if self.class_check_box_tracker[subject.id]["icon"][class_id].angle != 270:
                    self.class_check_box_tracker[subject.id]["icon"][class_id].mouseclicked.emit()
                
                if max_random_text_input.number() == -1:
                    max_random_text_input.setNumber(SCHOOL.settings.DEFAULT_max_classes)
                
                if not self.is_init:
                    rsma_func(None)
            
            widget_dp.beDisabled(on)
            max_random_text_input.setVisible(on)
            self.class_check_box_tracker[subject.id]["icon"][class_id].setDisabled(on)
        
        return checkbox_func
    
    def make_select_all_checkbox_func(self, subject: Subject, lvl_id: ID):
        def checkbox_func(is_on):
            if not self.mini_guy_is_clicked:
                self.main_guy_is_clicked = True
                
                if is_on:
                    if not self.class_check_box_tracker[subject.id]["sub_cbs"][lvl_id]:
                        self.main_guy_is_clicked = False
                        self.class_check_box_tracker[subject.id]["main_cb"][lvl_id].click()
                    else:
                        for c_box in self.class_check_box_tracker[subject.id]["sub_cbs"][lvl_id].values():
                            if not c_box.isChecked():
                                c_box.click()
                else:
                    for c_box in self.class_check_box_tracker[subject.id]["sub_cbs"][lvl_id].values():
                        if c_box.isChecked():
                            c_box.click()
                
                self.main_guy_is_clicked = False
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, subject: Subject, lvl_id: ID, cls_id: ID):
        def checkbox_func(on):
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if not self.is_init:
                    if on:
                        SCHOOL.class_levels[lvl_id].classes[cls_id].subjects[subject.id].teacher = self.teacher
                    else:
                        SCHOOL.class_levels[lvl_id].classes[cls_id].subjects[subject.id].teacher = None
                
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

class OccuranceEditor(BaseSettingDialog):
    def __init__(self, parent: BaseSettingWidget, id: ID, title: str, timetable_editor: SchoolTimetableEditor):
        super().__init__(title)
        
        self.id = id
        self.timetable_editor = timetable_editor
        self.class_level = SCHOOL.class_levels[self.id]
        
        self.setFixedSize(600, 400)
        
        self.focuses_ids = {}
        self.week_total = sum(week_amt for week_amt, _ in SCHOOL.settings.TIMETABLE_weekdays.values())
        
        self.subject_widgets: dict[str, QWidget] = {}
        self.number_edits: dict[str, tuple[NumberLineEdit, NumberLineEdit]] = {}
        
        self.setSpacing(20)
        
        for subject_id in self.class_level.subjects_occurence:
            self.add_subject(SCHOOL.subjects[subject_id])
        
        for subject_id, (per_day_edit, per_week_edit) in self.number_edits.items():
            per_day_edit.textChanged.emit(self.class_level.subjects_occurence[subject_id].day_max)
            per_week_edit.textChanged.emit(self.class_level.subjects_occurence[subject_id].week_max)
        
        self.addStretch()
    
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
        
        self.addWidget(selection_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.number_edits[subject.id] = per_day_edit, per_week_edit
        self.subject_widgets[subject.id] = selection_widget
    
    def make_per_day_text_changed_func(self, subject_id: ID):
        def text_changed_func(number):
            self.class_level.subjects_occurence[subject_id].day_max = number
        
        return text_changed_func
    
    def make_per_week_text_changed_func(self, subject_id: ID):
        def text_changed_func(number):
            diff = number - self.class_level.subjects_occurence[subject_id].week_max
            min_rem = min(self.week_total - (sum(self.class_level.subjects_occurence[s.id].week_max for s in cls.subjects.values()) + diff) for cls in self.class_level.classes.values())
            
            for _, per_week_edit in self.number_edits.values():
                per_week_edit.max_num = self.class_level.subjects_occurence[subject_id].week_max + min_rem
            
            self.number_edits[subject_id][0].max_num = number
            self.class_level.subjects_occurence[subject_id].week_max = number
            
            for cls_id, cls in self.class_level.classes.items():
                if subject_id in cls.subjects:
                    self.timetable_editor.timetable_widgets[cls.level.id][cls_id].change_subject_amount(subject_id, diff)
        
        return text_changed_func

class ClassOptionsMaker(BaseSettingDialog):
    def __init__(self, parent: BaseSettingWidget, id: ID, title: str, timetable_editor: SchoolTimetableEditor):
        super().__init__(title)
        
        self.id = id
        self.timetable_editor = timetable_editor
        self.class_level = SCHOOL.class_levels[self.id]
        
        self.max_cols = 4  # Maximum number of columns before wrapping
        
        self.main_area = BaseGridWidget(self.max_cols)
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
            id = ID.generate_new()
            
            cls = Class(id, "", self.class_level, {}, {}, SCHOOL)
            
            SCHOOL.class_levels.add_class(self.id, cls)
            self.timetable_editor.add_timetable_class(cls)
        
        def update_option():
            u_text = option.get_text()
            
            self.timetable_editor.set_label_text(id, u_text)
            self.class_level.classes[id].name = u_text
        
        update_option()
        
        option.finished_editing_signal.connect(update_option)
        
        def remove_option():
            self.timetable_editor.delete_timetable_class(self.class_level.classes[id])
            SCHOOL.class_levels.remove_class(self.id, id)
            
            self.main_area.removeWidget(option)
            
            option.deleteLater()
        
        option.deleted.connect(remove_option)
        
        # Add to grid and wrap to next row if needed
        self.main_area.addWidget(option)
        
        if is_new:
            option.start_editing()



class _SL_SelectedWidget(BaseWidget):
    def __init__(self, id: ID, text: str, host_container_layout: QVBoxLayout, on_add: Callable[[ID, ID], None], on_delete: Callable[[ID, ID], None]):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "SelectedSelectionListEntry")
        
        self.id = id
        self.text = text
        self.host_container_layout = host_container_layout
        
        self.on_add = on_add
        self.on_delete = on_delete
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(self.text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        self.host_container_layout.removeWidget(self)
        
        widget = _SL_UnSelectedWidget(self.id, self.text, self.host_container_layout, self.on_add, self.on_delete)
        
        # Find the last unselected widget or append at the end
        insert_index = self.host_container_layout.count() - 1
        for i in range(self.host_container_layout.count() - 1, -1, -1):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_UnSelectedWidget):
                insert_index = i
                break
        
        self.host_container_layout.insertWidget(insert_index, widget)
        
        self.deleteLater()
        
        self.on_delete(self.id)
        
        return super().mousePressEvent(a0)

class _SL_UnSelectedWidget(BaseWidget):
    def __init__(self, id: ID, text: str, host_container_layout: QVBoxLayout, on_add: Callable[[ID, ID], None], on_delete: Callable[[ID, ID], None]):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "UnselectedSelectionListEntry")
        
        self.id = id
        self.text = text
        self.host_container_layout = host_container_layout
        
        self.on_add = on_add
        self.on_delete = on_delete
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        self.host_container_layout.removeWidget(self)
        
        widget = _SL_SelectedWidget(self.id, self.text, self.host_container_layout, self.on_add, self.on_delete)
        
        insert_index = 0
        for i in range(self.host_container_layout.count()):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_SelectedWidget):
                insert_index = i + 1
        
        self.host_container_layout.insertWidget(insert_index, widget)
        
        self.deleteLater()
        
        self.on_add(self.id)
        
        return super().mousePressEvent(a0)


