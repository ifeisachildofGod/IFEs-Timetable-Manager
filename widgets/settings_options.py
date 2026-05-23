
from typing import Generator

from imports import *

from widgets.base_widgets import *
from widgets.user_interface import *


class SelectionList(BaseSettingDialog):
    def __init__(self, id: ID, title: str, selected_items: Generator[tuple[ID, str], None, None], content_scope: Global):
        super().__init__(title)
        
        self.setFixedSize(400, 300)
        
        # Initialize widgets
        unselected_items = ((k, v) for k, v in content_scope if k not in selected_items)
        
        # Add selected items
        for item_id, item_name in selected_items:
            Hook.setDynamicID(id + item_id)
            widget = _SL_SelectedWidget(id, item_id, item_name, self.getLayout())
            
            self.addWidget(widget)
        
        # Add unselected items
        for item_id, item_name in unselected_items:
            Hook.setDynamicID(id + item_id)
            widget = _SL_UnSelectedWidget(id, item_id, item_name, self.getLayout())
            
            self.addWidget(widget)
        
        self.addStretch()
    
    def go_to(self, widget: "_SL_SelectedWidget"):
        def func():
            self.scroll_area.verticalScrollBar().setValue(widget.y())
            
            widget.setFocus()
        
        QTimer.singleShot(200, func)


class SubjectSelectionLst(SelectionList):
    def __init__(self, id, title):
        super().__init__(id, title, ((t_id, teacher) for t_id, teacher in TEACHERS if id in teacher.subjects), TEACHERS)

class TeacherSelectionList(SelectionList):
    def __init__(self, id, title):
        super().__init__(id, title, iter(TEACHERS[id].subjects.items()), SUBJECTS)


class SubjectDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, id: ID, title: str):
        super().__init__(title)
        
        self.id = id
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.class_check_box_tracker = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "widget": {}}
        
        for widget in self._create_checkbox_widgets():
            self.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
    
    def go_to(self, lvl_id: ID, cls_id: Optional[ID] = None):
        if cls_id is None:
            if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
            
            def func():
                self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker["widget"][lvl_id].y())
                
                self.class_check_box_tracker["widget"][lvl_id].setFocus()
            
            QTimer.singleShot(200, func)
        else:
            if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
            
            self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].y())
            
            self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].setFocus()
    
    def _create_checkbox_widgets(self):
        widgets: list[QWidget] = []
        all_clicked_checkboxes: list[QCheckBox] = []
        
        for lvl_id, cls_lvl in CLASS_LEVELS:
            check_box = QCheckBox()
            check_box.clicked.connect(self.make_main_checkbox_func(lvl_id, self.class_check_box_tracker))
            
            self.class_check_box_tracker["sub_cbs"][lvl_id] = {}
            self.class_check_box_tracker["main_cb"][lvl_id] = check_box
            self.class_check_box_tracker["widget"][lvl_id], to_be_clicked = self.make_dp_widget(lvl_id, cls_lvl)
            
            main_widget = _WidgetDropdown(cls_lvl.name, self.class_check_box_tracker["widget"][lvl_id])
            main_widget.header_layout.addWidget(check_box)
            
            self.class_check_box_tracker["icon"][lvl_id] = main_widget.toogle_icon
            
            all_clicked_checkboxes.extend(to_be_clicked)
            
            widgets.append(main_widget)
        
        for cb in all_clicked_checkboxes:
            cb.click()
        
        return widgets
    
    def make_dp_widget(self, lvl_id: ID, cls_lvl: ClassLevel):
        dp_widget = QWidget()
        dp_widget.setProperty("class", "DPC_Body")
        
        dp_layout = QVBoxLayout()
        dp_layout.setSpacing(2)
        dp_widget.setLayout(dp_layout)
        
        clicked_cbs: list[QCheckBox] = []
        
        for cls_id, cls in cls_lvl.classes.items():
            option_layout = QHBoxLayout()            
            
            dp_title = QLabel(cls.name)
            dp_checkbox = QCheckBox()
            
            self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id] = dp_checkbox
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(lvl_id, cls_id))
            
            if cls.id in SUBJECTS[self.id].classes and not dp_checkbox.isChecked():
                clicked_cbs.append(dp_checkbox)
            
            option_layout.addSpacing(50)
            option_layout.addWidget(dp_title)
            option_layout.addStretch()
            option_layout.addWidget(dp_checkbox)
            
            dp_layout.addLayout(option_layout)
        
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
            self.sub_checkbox_func(on, lvl_id, cls_id)
            
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if on:
                    lvl_set = set(CLASS_LEVELS[lvl_id].classes.items())
                    intersect_set = set(SUBJECTS[self.id].classes.items()).intersection(lvl_set)
                    
                    if len(lvl_set) == len(intersect_set) and not self.class_check_box_tracker["main_cb"][lvl_id].isChecked():
                        self.class_check_box_tracker["main_cb"][lvl_id].click()
                else:
                    if self.class_check_box_tracker["main_cb"][lvl_id].isChecked():
                        self.class_check_box_tracker["main_cb"][lvl_id].click()
                
                self.mini_guy_is_clicked = False
        
        return checkbox_func
    
    def sub_checkbox_func(self, on: bool, lvl_id: ID, cls_id: ID):
        if on:
            SUBJECTS[self.id].classes[cls_id] = CLASS_LEVELS[lvl_id].classes[cls_id]
        else:
            SUBJECTS[self.id].classes.pop(cls_id)

class TeacherDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, id: ID, title: str, info, teacher_id, default_max_classes):
        super().__init__(title)
        
        self.id = id
        
        self.teacher_id = teacher_id
        self.default_max_classes = default_max_classes
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.subject_check_box_tracker = {}
        self.class_check_box_tracker = {}
        
        for subject_id, subject in TEACHERS[self.id].subjects.items():
            self.subject_check_box_tracker[subject_id] = {}
            self.class_check_box_tracker[subject_id] = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "max_random": {}, "widget": {}}
            
            self.subject_check_box_tracker[subject_id]["widget"] = self.make_subject_widget(subject)
            
            main_widget = _WidgetDropdown(subject.name, self.subject_check_box_tracker[subject_id]["widget"])
            
            self.subject_check_box_tracker[subject_id]["icon"] = main_widget.toogle_icon
            
            self.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.addStretch()
    
    def go_to(self, subj_id: ID, lvl_id: Optional[ID], cls_id: Optional[ID]):
        if not lvl_id and not cls_id:
            def func1():
                if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                    self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                
                def in_func():
                    self.scroll_area.verticalScrollBar().setValue(self.subject_check_box_tracker[subj_id]["widget"].y())
                    
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
                        self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker[subj_id]["widget"][lvl_id].y())
                        
                        self.class_check_box_tracker[subj_id]["widget"][lvl_id].setFocus()
                
                    QTimer.singleShot(200, inner_func)
                
                QTimer.singleShot(200, in_func)
            
            QTimer.singleShot(250, func2)
        else:
            def func3():
                if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                    self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                
                def in_func():
                    if not self.class_check_box_tracker[subj_id]["widget"][lvl_id].isVisible():
                        self.class_check_box_tracker[subj_id]["icon"][lvl_id].mouseclicked.emit()
                    
                    def inner_func():
                        self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker[subj_id]["sub_cbs"][lvl_id][cls_id].y())
                        
                        self.class_check_box_tracker[subj_id]["sub_cbs"][lvl_id][cls_id].setFocus()
            
                    QTimer.singleShot(200, inner_func)
                
                QTimer.singleShot(200, in_func)
                
            QTimer.singleShot(300, func3)
    
    def _create_checkbox_widgets(self, subject: Subject):
        widgets: list[QWidget] = []
        random_on_checkboxes: list[QCheckBox] = []
        
        cls_lvls = []
        for cls in subject.classes:
            if cls.level not in cls_lvls:
                cls_lvls.append(cls.level)
                
                def rsma_func(number: Optional[int]):
                    SETTINGS.TEACHER_rsma_mapping[cls.level.id] = number
                
                max_random_text_input = NumberLineEdit(SETTINGS.TEACHER_rsma_mapping[cls.level.id] if SETTINGS.TEACHER_rsma_mapping[cls.level.id] is not None else 1, 1, len(cls.level.classes))
                max_random_text_input.edit.setToolTip("Maximum Classes Taught")
                max_random_text_input.setVisible(False)
                max_random_text_input.textChanged.connect(rsma_func)
                
                check_box = QCheckBox("Random")
                check_box.clicked.connect(self.make_main_checkbox_func(subject, cls.level.id, rsma_func))
                
                if SETTINGS.TEACHER_rsma_mapping[cls.level.id]:
                    random_on_checkboxes.append(check_box)
                
                self.class_check_box_tracker[subject.id]["sub_cbs"][cls.level.id] = {}
                self.class_check_box_tracker[subject.id]["main_cb"][cls.level.id] = check_box
                self.class_check_box_tracker[subject.id]["max_random"][cls.level.id] = max_random_text_input
                self.class_check_box_tracker[subject.id]["widget"][cls.level.id], to_be_clicked = self.make_dp_widget(cls.level, SETTINGS.TEACHER_rsma_mapping[cls.level.id])
                
                main_widget = _WidgetDropdown(cls.level.name, self.class_check_box_tracker[subject.id]["widget"][cls.level.id])
                main_widget.header_layout.addWidget(max_random_text_input)
                main_widget.header_layout.addWidget(check_box)
                
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
            optionState = next((True for subj in cls.subjects.values() if subj.teacher and self.id == subj.teacher.id), False)
            
            option_widget = BaseWidget()
            option_widget.setDisabled(CLASS_LEVELS[lvl.id].classes[cls_id].subjects[subject.id].teacher is not None)
            
            dp_title = QLabel(cls.name)
            
            dp_checkbox = QCheckBox()
            
            self.class_check_box_tracker[subject.id]["sub_cbs"][lvl.id][cls_id] = dp_checkbox
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(subject.id, lvl.id, cls_id))
            
            if optionState and SETTINGS.TEACHER_rsma_mapping[lvl.id] is None:
                clicked_cbs.append(dp_checkbox)
            
            option_widget.addSpacing(50)
            option_widget.addWidget(dp_title)
            option_widget.addStretch()
            option_widget.addWidget(dp_checkbox)
            
            dp_widget.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def make_main_checkbox_func(self, subject: Subject, class_id: str, rsma_func: Callable[[Optional[int]], None]):
        def checkbox_func(on):
            if on:
                for c_box in self.class_check_box_tracker[subject.id]["sub_cbs"][class_id].values():
                    if c_box.isChecked():
                        c_box.click()
                
                if self.class_check_box_tracker[subject.id]["icon"][class_id].angle != 270:
                    self.class_check_box_tracker[subject.id]["icon"][class_id].mouseclicked.emit()
                
                if self.class_check_box_tracker[subject.id]["max_random"][class_id].number() == -1:
                    self.class_check_box_tracker[subject.id]["max_random"][class_id].setNumber(self.default_max_classes)
                
                rsma_func(None)
            
            self.class_check_box_tracker[subject.id]["icon"][class_id].setDisabled(on)
            self.class_check_box_tracker[subject.id]["max_random"][class_id].setVisible(on)
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, subject_id: ID, lvl_id: ID, cls_id: ID):
        def checkbox_func(on):
            if on:
                CLASS_LEVELS[lvl_id].classes[cls_id].subjects[subject_id].teacher = TEACHERS[self.id]
            else:
                CLASS_LEVELS[lvl_id].classes[cls_id].subjects[subject_id].teacher = None
        
        return checkbox_func

class SubjectSelection(BaseSettingDialog):
    def __init__(
        self,
        title: str,
        info: dict[
            str,
            dict[
                str,
                str | dict[str, list[str | None] | dict[int, str]]
            ] | dict[int, str] | dict[str, list[str | None]]
        ],
        index: int,
        main_subjects_info: dict[str, tuple[str, dict[str, tuple[int, int, dict]]]],
        week_total: int
    ):
        super().__init__(title, info)
        
        self.setFixedSize(600, 400)
        
        self.week_total = week_total
        
        self.subject_widgets: dict[str, QWidget] = {}
        self.number_edits: dict[str, tuple[NumberLineEdit, NumberLineEdit]] = {}
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.setSpacing(20)
        
        self.main_subjects_info = {s_id: set(data[2]) for s_id, (_, values) in main_subjects_info.items() if (data := values.get(str(index)))}
        
        self.focuses_ids = {
            subject_id: list (
                    s_id
                    for s_id
                    in self.info
                    if (
                        s_id in self.main_subjects_info and
                        subject_id in self.main_subjects_info and
                        self.main_subjects_info[subject_id].intersection(self.main_subjects_info[s_id])
                    )
                )
            for subject_id
            in self.info
        }
        
        for subject_id, (subject_name, subject_info) in self.info.items():
            self.add_subject(subject_id, subject_name, subject_info) # type: ignore
        
        for subject_id, (per_day_edit, per_week_edit) in self.number_edits.items():
            per_day_edit.textChanged.emit(self.info[subject_id][1]["per_day"])
            per_week_edit.textChanged.emit(self.info[subject_id][1]["per_week"])
        
        self.addStretch()
    
    def go_to(self, _id):
        for subject_id, widget in self.subject_widgets.items():
            if subject_id == _id:
                def func():
                    self.scroll_area.verticalScrollBar().setValue(widget.y())
                    widget.setFocus()
                
                QTimer.singleShot(200, func)
                
                break
    
    def add_subject(self, subject_id: str, subject_name: str, info: dict):
        selection_widget = QWidget()
        selection_widget.setProperty("class", "SubjectClassViewEntry")
        
        layout = QHBoxLayout()
        selection_widget.setLayout(layout)
        
        metrics = QFontMetrics(self.font())
        subjects_label = QLabel(metrics.elidedText(subject_name, Qt.TextElideMode.ElideRight, 100))
        subjects_label.setFont(self.font())
        subjects_label.setToolTip(subject_name)
        subjects_label.setProperty("class", "SubjectClassViewEntryName")
        
        sub_widget = QWidget()
        sub_widget.setProperty("class", "SubjectClassViewEntryEdits")
        
        sub_layout = QVBoxLayout()
        sub_widget.setLayout(sub_layout)
        
        layout.addWidget(subjects_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_widget, alignment=Qt.AlignmentFlag.AlignRight)
        
        per_day_edit = NumberLineEdit(info["per_day"], 1, info["per_week"])
        # per_day_edit.edit.setFixedWidth(50)
        per_day_edit.setPlaceholderText("Per day")
        per_day_edit.textChanged.connect(self.make_per_day_text_changed_func(subject_id, per_day_edit))
        
        per_week_edit = NumberLineEdit(info["per_week"], 1, info["per_week"] + self.week_total - sum(self.info[s_id][1]["per_week"] for s_id in self.focuses_ids[subject_id]))
        # per_week_edit.edit.setFixedWidth(54)
        per_week_edit.setPlaceholderText("Per week")
        per_week_edit.textChanged.connect(self.make_per_week_text_changed_func(subject_id, per_day_edit, per_week_edit))
        
        per_day_widget = QWidget()
        per_day_layout = QHBoxLayout()
        per_day_widget.setProperty("class", "Edit")
        per_day_widget.setStyleSheet("QWidget.Edit{background: none} QLabel{background: none}")
        per_day_widget.setLayout(per_day_layout)
        
        per_day_layout.addWidget(QLabel("<b>Per day</b>"))
        per_day_layout.addWidget(per_day_edit)
        
        per_week_widget = QWidget()
        per_week_layout = QHBoxLayout()
        per_week_widget.setProperty("class", "Edit")
        per_week_widget.setStyleSheet("QWidget.Edit{background: none} QLabel{background: none}")
        per_week_widget.setLayout(per_week_layout)
        
        per_week_layout.addWidget(QLabel("<b>Per week</b>"))
        per_week_layout.addWidget(per_week_edit)
        
        sub_layout.addWidget(per_day_widget)
        sub_layout.addWidget(per_week_widget)
        
        self.addWidget(selection_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.number_edits[subject_id] = per_day_edit, per_week_edit
        self.subject_widgets[subject_id] = selection_widget
    
    def make_per_day_text_changed_func(self, subject_id: str, input_edit: 'NumberLineEdit'):
        def text_changed_func():
            self.info[subject_id][1]["per_day"] = input_edit.number() # type: ignore
        
        return text_changed_func
    
    def make_per_week_text_changed_func(self, subject_id: str, per_day_edit: 'NumberLineEdit', per_week_edit: 'NumberLineEdit'):
        def text_changed_func(number):
            diff = self.week_total - sum((self.info[s_id][1]["per_week"] if s_id != subject_id else number) for s_id in self.focuses_ids[subject_id])
            
            print()
            print("---", self.info[subject_id][0], diff)
            for s_id in self.focuses_ids[subject_id]:
                print(self.info[s_id][0], self.number_edits[s_id][1].number(), self.number_edits[s_id][1].max_num, self.number_edits[s_id][1].number() + diff)
                self.number_edits[s_id][1].max_num = self.number_edits[s_id][1].number() + diff
            
            per_day_edit.max_num = self.info[subject_id][1]["per_week"] = number
        
        return text_changed_func

class ClassOptionsMaker(BaseSettingDialog):
    def __init__(self, id: ID, title: str):
        super().__init__(title)
        
        self.id = id
        
        self.max_cols = 4  # Maximum number of columns before wrapping
        
        self.main_area = BaseGridWidget(self.max_cols)
        self.main_area.setSpacing(4)
        self.main_area.getLayout().setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.add_button = QPushButton("Add Option")
        self.add_button.clicked.connect(lambda: self.add_option())
        
        self.addWidget(self.main_area)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        temp_option = EditableCancelableEntry("IFE")
        self.setFixedSize((temp_option.width() + (temp_option.getLayout().spacing() * 4) + self.main_area.getLayout().spacing()) * self.max_cols, 300)
        
        del temp_option
        
        # Load existing options
        for class_id, cls in CLASS_LEVELS[self.id].classes:
            self.add_option(class_id, cls.name)
    
    def go_to(self, widget: QWidget):
        def func():
            self.scroll_area.verticalScrollBar().setValue(widget.y())
            widget.setFocus()
        
        QTimer.singleShot(200, func)
    
    def add_option(self, id: str | None = None, text: str | None = None):
        option = EditableCancelableEntry(text)
        
        if id is None:
            id = ID.generate_new()
            
            Hook.setDynamicID(id)
            self.new_class(id)
        
        def update_option():
            CLASS_LEVELS[self.id].name = option.get_text()
        
        update_option()
        
        option.finished_editing_signal.connect(update_option)
        
        def remove_option():
            Hook.setDynamicID(id)
            self.delete_class(id, option)
        
        option.deleted.connect(remove_option)
        
        # Add to grid and wrap to next row if needed
        self.main_area.addWidget(option)
        
        if id is None:
            option.start_editing()
    
    @Hook(Signal.ClassAdd, SignalType.SOURCE, True)
    def new_class(self, id: ID):
        cls = Class(id, "", CLASS_LEVELS[self.id], {})
        
        CLASS_LEVELS[self.id].add(cls)
        
        return cls
    
    @Hook(Signal.ClassRemove, SignalType.SOURCE, True)
    def delete_class(self, id: ID, option: EditableCancelableEntry):
        CLASS_LEVELS[self.id].classes.pop(id)
        
        self.main_area.removeWidget(option)
        
        option.deleteLater()
        
        return id



class _WidgetDropdown(QWidget):
    def __init__(self, title: str, widget: QWidget, parent=None):
        super().__init__(parent)
        
        self.widget = widget
        
        self.setSpacing(0)
        
        self.setProperty("class", "Bordered")
        self.setProperty("class", "DropdownCheckboxes")
        
        header = QWidget()
        header.setProperty("class", "DPC_Header")
        header.setFixedHeight(50)
        header.mousePressEvent = self.tdp_event_func
        
        self.header_layout = QHBoxLayout(header)
        self.header_layout.setContentsMargins(12, 0, 12, 0)
        
        self.toogle_icon = ArrowWidget(270)
        self.toogle_icon.setProperty("class", "Arrow")
        self.toogle_icon.mouseclicked.connect(self.toogle_widget)
        self.toogle_icon.setContentsMargins(0, 0, 10, 0)
        
        title_label = QLabel(title)
        
        self.header_layout.addWidget(self.toogle_icon)
        self.header_layout.addWidget(title_label)
        self.header_layout.addStretch()
        # self.header_layout.addWidget(check_box)
        
        self.addWidget(header)
        self.addWidget(self.widget) # type: ignore
    
    def tdp_event_func(self, a0: QMouseEvent | None):
        if a0.button() == Qt.MouseButton.LeftButton: # type: ignore
            self.toogle_widget()
    
    def toogle_widget(self):
        self.toogle_icon.setAngle(0 if self.toogle_icon.angle != 0 else 270)
        self.widget.setVisible(not self.widget.isVisible())

class _SL_SelectedWidget(BaseWidget):
    def __init__(self, parentID: ID, id: ID, text: str, host_container_layout: QVBoxLayout):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "SelectedSelectionListEntry")
        
        self.id = id
        self.text = text
        self.parentID = parentID
        self.host_container_layout = host_container_layout
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(self.text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        Hook.setDynamicID(self.parentID + self.id)
        self.delete_self()
        
        return super().mousePressEvent(a0)
    
    @Hook("SW_Delete", SignalType.SOURCE, True)
    def delete_self(self):
        self.host_container_layout.removeWidget(self)
        
        widget = _SL_UnSelectedWidget(self.id, self.text, self.host_container_layout)
        
        # Find the last unselected widget or append at the end
        insert_index = self.host_container_layout.count() - 1
        for i in range(self.host_container_layout.count() - 1, -1, -1):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_UnSelectedWidget):
                insert_index = i
                break
        
        self.host_container_layout.insertWidget(insert_index, widget)
        
        self.deleteLater()

class _SL_UnSelectedWidget(BaseWidget):
    def __init__(self, parentID: ID, id: ID, text: str, host_container_layout: QVBoxLayout):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "UnselectedSelectionListEntry")
        
        self.id = id
        self.text = text
        self.parentID = parentID
        self.host_container_layout = host_container_layout
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        Hook.setDynamicID(self.parentID + self.id)
        self.add_self()
        
        return super().mousePressEvent(a0)
    
    @Hook("SW_Add", SignalType.SOURCE, True)
    def add_self(self):
        self.host_container_layout.removeWidget(self)
        
        widget = _SL_SelectedWidget(self.id, self.text, self.host_container_layout)
        
        insert_index = 0
        for i in range(self.host_container_layout.count()):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_SelectedWidget):
                insert_index = i + 1
        
        self.host_container_layout.insertWidget(insert_index, widget)
        
        self.deleteLater()

