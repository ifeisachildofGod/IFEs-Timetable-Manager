
from base_widgets import BaseSettingEntry

from imports import *
from base_widgets import *


class SubjectSelectionList(BaseSettingDialog):
    def __init__(self, title: str, id: ID):
        super().__init__(title)
        
        self.setFixedSize(400, 300)
        
        # Initialize widgets
        split_index = info.index(None)
        selected_items = info[:split_index]
        unselected_items = info[split_index+1:]
        
        # Add selected items
        for item_id, item_name in selected_items:
            CONNECTIONS_MANAGER.setVar(id + item_id)
            widget = _SL_SelectedWidget(item_id, item_name, self.getLayout())
            self.addWidget(widget)
        
        # Add unselected items
        for item_id, item_name in unselected_items:
            CONNECTIONS_MANAGER.setVar(id + item_id)
            widget = _SL_UnSelectedWidget(item_id, item_name, self.getLayout())
            self.addWidget(widget)
        
        CONNECTIONS_MANAGER.resetVar()
        
        self.addStretch()
    
    def go_to(self, widget: _SL_SelectedWidget, _SL_UnSelectedWidget):
        def func():
            self.scroll_area.verticalScrollBar().setValue(widget.y())
            widget.setFocus()
        
        QTimer.singleShot(200, func)

class SubjectDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, title: str, info: dict[str, dict[str, dict[str, dict[str, str | bool]]] | dict[int, str]], saved_state_changed: pyqtBoundSignal, general_data: dict):
        super().__init__(title, info, saved_state_changed)
        self.general_data = general_data
        
        self.setFixedSize(400, 300)
        
        self.saved_state_changed = saved_state_changed
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)
        
        self.class_check_box_tracker = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "widget": {}}
        
        for widget in self._create_checkbox_widgets(self.info, self.general_data, self.class_check_box_tracker):
            self.container_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.container_layout.addStretch()
    
    def go_to(self, _id):
        for lvl_id, lvl_data in self.get().items():
            if lvl_id == _id:
                if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                    self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
                
                def func():
                    self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker["widget"][lvl_id].y())
                    
                    self.class_check_box_tracker["widget"][lvl_id].setFocus()
                
                QTimer.singleShot(200, func)
                
                break
            
            for cls_id, cls_state in lvl_data.items():
                if not cls_state:
                    continue
                
                if "-" in _id or cls_id == _id:
                    if cls_id != _id:
                        f_lvl_id, f_cls_id = _id.split("-")
                        if lvl_id != f_lvl_id or cls_id != f_cls_id:
                            continue
                    
                    if not self.class_check_box_tracker["widget"][lvl_id].isVisible():
                        self.class_check_box_tracker["icon"][lvl_id].mouseclicked.emit()
                    
                    self.scroll_area.verticalScrollBar().setValue(self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].y())
                    
                    self.class_check_box_tracker["sub_cbs"][lvl_id][cls_id].setFocus()
                    
                    break
            else:
                continue
            
            break
    
    def _create_checkbox_widgets(self, data, general_data, class_check_box_tracker: dict[str, dict[str, QCheckBox | QWidget | dict[str, QCheckBox]]]):
        updated_data = deepcopy(general_data)
        for class_id, options_info in data.items():
            updated_data["content"][class_id].update(options_info)
        
        id_mapping = updated_data["id_mapping"]
        
        widgets: list[QWidget] = []
        all_clicked_checkboxes: list[QCheckBox] = []
        
        for class_id, class_options in updated_data["content"].items():
            check_box = QCheckBox()
            check_box.clicked.connect(self.make_main_checkbox_func(class_id, class_check_box_tracker))
            all_clicked = False not in list(class_options.values()) and class_options
            
            class_check_box_tracker["sub_cbs"][class_id] = {}
            class_check_box_tracker["main_cb"][class_id] = check_box
            class_check_box_tracker["widget"][class_id], to_be_clicked = self.make_dp_widget(class_id, class_options, all_clicked, data, updated_data, class_check_box_tracker)
            
            main_widget = _WidgetDropdown(id_mapping["main"][class_id], class_check_box_tracker["widget"][class_id])
            main_widget.header_layout.addWidget(check_box)
            
            class_check_box_tracker["icon"][class_id] = main_widget.toogle_icon
            
            all_clicked_checkboxes.extend(to_be_clicked)
            
            widgets.append(main_widget)
        
        for cb in all_clicked_checkboxes:
            cb.click()
        
        return widgets
    
    def make_open_dp_func(self, class_id: str, class_check_box_tracker: dict[str, Any]):
        def open_dp():
            widget: QWidget = class_check_box_tracker["widget"][class_id]
            
            class_check_box_tracker["icon"][class_id].setAngle(0 if class_check_box_tracker["icon"][class_id].angle != 0 else 270)
            
            if widget.isVisible():
                widget.setVisible(False)
            else:
                widget.setVisible(True)
        
        return open_dp
    
    def make_dp_widget(self, class_id: str, options: dict[str, bool], all_clicked: bool, info, updated_data, class_check_box_tracker: dict[str, Any]):
        dp_widget = QWidget()
        dp_widget.setProperty("class", "DPC_Body")
        
        dp_layout = QVBoxLayout()
        dp_layout.setSpacing(2)
        dp_widget.setLayout(dp_layout)
        
        clicked_cbs: list[QCheckBox] = []
        
        for optionID, optionState in options.items():
            option_layout = QHBoxLayout()            
            
            dp_title = QLabel(updated_data["id_mapping"]["sub"][class_id][optionID])
            dp_checkbox = QCheckBox()
            
            class_check_box_tracker["sub_cbs"][class_id][optionID] = dp_checkbox
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(class_id, info, updated_data, options, class_check_box_tracker))
            
            if optionState and not dp_checkbox.isChecked():
                clicked_cbs.append(dp_checkbox)
            
            option_layout.addSpacing(50)
            option_layout.addWidget(dp_title)
            option_layout.addStretch()
            option_layout.addWidget(dp_checkbox)
            
            dp_layout.addLayout(option_layout)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def make_main_checkbox_func(self, class_id: str, class_check_box_tracker: dict[str, Any]):
        def checkbox_func(is_on):
            if not self.mini_guy_is_clicked:
                self.main_guy_is_clicked = True
                
                if is_on:
                    if not class_check_box_tracker["sub_cbs"][class_id]:
                        QMessageBox.critical(self, "Setting SDCB Error", "No class level option has been made for this class level")
                        self.main_guy_is_clicked = False
                        class_check_box_tracker["main_cb"][class_id].click()
                    else:
                        for c_box in class_check_box_tracker["sub_cbs"][class_id].values():
                            if not c_box.isChecked():
                                c_box.click()
                else:
                    for c_box in class_check_box_tracker["sub_cbs"][class_id].values():
                        if c_box.isChecked():
                            c_box.click()
                
                self.main_guy_is_clicked = False
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, class_id: str, content, updated_data, options: dict[str, bool], class_check_box_tracker: dict[str, Any]):
        def checkbox_func(on):
            if class_id not in content:
                content[class_id] = {}
            
            for checkBoxID, checkBox in class_check_box_tracker["sub_cbs"][class_id].items():
                if not checkBox.isChecked() and class_id in content and checkBoxID in content[class_id]:
                    content[class_id].pop(checkBoxID)
                elif checkBox.isChecked():
                    if class_id not in content:
                        content[class_id] = {}
                    content[class_id][checkBoxID] = True
            
            # new_options = dict.fromkeys(options, False)
            # new_options.update(content[class_id])
            
            # options.update(new_options)
            
            if not sum(list(content[class_id].values())):
                content.pop(class_id)
            
            if not self.main_guy_is_clicked:
                self.mini_guy_is_clicked = True
                
                if on:
                    if len(content[class_id]) == len(updated_data["content"][class_id]) and not class_check_box_tracker["main_cb"][class_id].isChecked():
                        class_check_box_tracker["main_cb"][class_id].click()
                else:
                    if class_check_box_tracker["main_cb"][class_id].isChecked():
                        class_check_box_tracker["main_cb"][class_id].click()
                
                self.mini_guy_is_clicked = False
            
            self.saved_state_changed.emit()
        
        return checkbox_func

class TeacherDropdownCheckBoxes(BaseSettingDialog):
    def __init__(self, title, info, saved_state_changed, teacher_id, general_data, default_max_classes):
        super().__init__(title, info, saved_state_changed)
        
        self.teacher_id = teacher_id
        self.general_data = general_data
        self.default_max_classes = default_max_classes
        self.saved_state_changed = saved_state_changed
        
        self.setFixedSize(400, 300)
        
        self.main_guy_is_clicked = False
        self.mini_guy_is_clicked = False
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.container)
        
        self.subject_check_box_tracker = {}
        self.class_check_box_tracker = {}
        
        for subject_id, info in self.info["content"].items():
            self.subject_check_box_tracker[subject_id] = {}
            self.class_check_box_tracker[subject_id] = {"main_cb": {}, "sub_cbs": {}, "icon": {}, "max_random": {}, "widget": {}}
            
            self.subject_check_box_tracker[subject_id]["widget"] = self.make_subject_widget(info, self.general_data[subject_id], self.class_check_box_tracker[subject_id])
            
            main_widget = _WidgetDropdown(self.info["id_mapping"][subject_id], self.subject_check_box_tracker[subject_id]["widget"])
            
            self.subject_check_box_tracker[subject_id]["icon"] = main_widget.toogle_icon
            
            self.container_layout.addWidget(main_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.container_layout.addStretch()
    
    def go_to(self, _id):
        for subj_id, subj_data in self.get()["content"].items():
            if subj_id == _id:
                def func1():
                    if not self.subject_check_box_tracker[subj_id]["widget"].isVisible():
                        self.subject_check_box_tracker[subj_id]["icon"].mouseclicked.emit()
                    
                    def in_func():
                        self.scroll_area.verticalScrollBar().setValue(self.subject_check_box_tracker[subj_id]["widget"].y())
                        
                        self.subject_check_box_tracker[subj_id]["widget"].setFocus()
                
                    QTimer.singleShot(200, in_func)
                
                QTimer.singleShot(200, func1)
                
                break
            
            for lvl_id, (randomly_selected, lvl_data) in subj_data.items():
                if randomly_selected is None:
                    continue
                
                if _id.count("-") == 1 or lvl_id == _id:
                    if lvl_id != _id:
                        f_subj_id, f_lvl_id = _id.split("-")
                        if subj_id != f_subj_id or lvl_id != f_lvl_id:
                            continue
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
                    
                    break
                
                for cls_id, cls_state in lvl_data.items():
                    if not cls_state:
                        continue
                    
                    if _id.count("-") == 2 or cls_id == _id:
                        if cls_id != _id:
                            f_subj_id, f_lvl_id, f_cls_id = _id.split("-")
                            if subj_id != f_subj_id or lvl_id != f_lvl_id or cls_id != f_cls_id:
                                continue
                        
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
                        
                        break
                else:
                    continue
                
                break
    
    def _create_checkbox_widgets(self, data: dict[str, dict[str, dict[str, str | bool]]] | dict[int, str], general_data, class_check_box_tracker: dict[str, dict[str, QCheckBox | QWidget | dict[str, QCheckBox]]]):
        updated_data = deepcopy(general_data)
        
        for class_id, (random_on, options_info) in data.items():
            updated_data["content"][class_id][0] = random_on
            for opt_id, opt_state in options_info.items(): # type: ignore
                if not isinstance(updated_data["content"][class_id][1][opt_id], str) or opt_state:
                    updated_data["content"][class_id][1][opt_id] = options_info[opt_id]
        
        id_mapping = updated_data["id_mapping"]
        
        widgets: list[QWidget] = []
        random_on_checkboxes: list[QCheckBox] = []
        
        for class_id, (random_on, class_options) in updated_data["content"].items():
            max_random_text_input = NumberLineEdit(random_on if random_on is not None else -1, len(class_options))
            max_random_text_input.edit.setToolTip("Max Classes")
            max_random_text_input.setVisible(False)
            max_random_text_input.textChanged.connect(self.make_random_text_changed_func(class_id, data))
            
            check_box = QCheckBox("Random")
            check_box.clicked.connect(self.make_main_checkbox_func(class_id, data, class_check_box_tracker))
            
            if random_on:
                random_on_checkboxes.append(check_box)
            
            class_check_box_tracker["sub_cbs"][class_id] = {}
            class_check_box_tracker["main_cb"][class_id] = check_box
            class_check_box_tracker["max_random"][class_id] = max_random_text_input
            class_check_box_tracker["widget"][class_id], to_be_clicked = self.make_dp_widget(class_id, class_options, random_on, data, general_data, updated_data, class_check_box_tracker)
            
            main_widget = _WidgetDropdown(id_mapping["main"][class_id], class_check_box_tracker["widget"][class_id])
            main_widget.header_layout.addWidget(max_random_text_input)
            main_widget.header_layout.addWidget(check_box)
            
            class_check_box_tracker["icon"][class_id] = main_widget.toogle_icon
            
            random_on_checkboxes.extend(to_be_clicked)
            
            widgets.append(main_widget)
        
        for cb in random_on_checkboxes:
            cb.click()
        
        return widgets
    
    def make_open_dp_func(self, class_id: str, class_check_box_tracker: dict[str, Any]):
        def open_dp():
            widget: QWidget = class_check_box_tracker["widget"][class_id]
            
            class_check_box_tracker["icon"][class_id].setAngle(0 if class_check_box_tracker["icon"][class_id].angle != 0 else 270)
            
            if widget.isVisible():
                widget.setVisible(False)
            else:
                widget.setVisible(True)
        
        return open_dp
    
    def make_random_text_changed_func(self, class_id, data):
        def func(number: int):
            data[class_id][0] = number if number != -1 else None
        
        return func
    
    def make_subject_widget(self, info, general_data, class_check_box_tracker):
        container_widget = QWidget()
        
        container_layout = QVBoxLayout()
        container_widget.setLayout(container_layout)
        
        for widget in self._create_checkbox_widgets(info, general_data, class_check_box_tracker):
            container_layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        container_widget.setVisible(False)
        
        return container_widget
    
    def make_dp_widget(self, class_id: str, options: dict[str, bool], random_clicked: int | None, content, general_data, updated_data, class_check_box_tracker):
        dp_widget = QWidget()
        dp_widget.setProperty("class", "DPC_Body")
        
        dp_layout = QVBoxLayout()
        dp_layout.setSpacing(2)
        dp_widget.setLayout(dp_layout)
        
        clicked_cbs: list[QCheckBox] = []
        
        for optionID, optionState in options.items():
            option_widget = QWidget()
            option_layout = QHBoxLayout()
            
            option_widget.setLayout(option_layout)
            option_widget.setDisabled(isinstance(optionState, str))
            
            dp_title = QLabel(updated_data["id_mapping"]["sub"][class_id][optionID])
            
            dp_checkbox = QCheckBox()
            
            class_check_box_tracker["sub_cbs"][class_id][optionID] = dp_checkbox
            
            dp_checkbox.clicked.connect(self.make_sub_checkbox_func(class_id, content, general_data, optionID))
            
            if optionState and random_clicked is None:
                clicked_cbs.append(dp_checkbox)
            
            option_layout.addSpacing(50)
            option_layout.addWidget(dp_title)
            option_layout.addStretch()
            option_layout.addWidget(dp_checkbox)
            
            dp_layout.addWidget(option_widget)
        
        dp_widget.setVisible(False)
        
        return dp_widget, clicked_cbs
    
    def make_main_checkbox_func(self, class_id: str, content, class_check_box_tracker):
        def checkbox_func(is_on):
            if class_id not in content:
                content[class_id] = [None, {}]
            
            if is_on:
                for c_box in class_check_box_tracker["sub_cbs"][class_id].values():
                    if c_box.isChecked():
                        c_box.click()
                
                if class_check_box_tracker["icon"][class_id].angle != 270:
                    class_check_box_tracker["icon"][class_id].mouseclicked.emit()
                
                if class_check_box_tracker["max_random"][class_id].number() == -1:
                    class_check_box_tracker["max_random"][class_id].setNumber(self.default_max_classes)
            
            class_check_box_tracker["icon"][class_id].setDisabled(is_on)
            class_check_box_tracker["max_random"][class_id].setVisible(is_on)
            
            content[class_id][0] = class_check_box_tracker["max_random"][class_id].number() if is_on else None
        
        return checkbox_func
    
    def make_sub_checkbox_func(self, class_id: str, content, general_data, option_id: str):
        def checkbox_func(is_on):
            if is_on:
                if class_id not in content:
                    content[class_id] = [None, {}]
                
                content[class_id][1][option_id] = True
                general_data["content"][class_id][1][option_id] = self.teacher_id
            else:
                content[class_id][1].pop(option_id)
                general_data["content"][class_id][1][option_id] = False
            
            self.saved_state_changed.emit()
        
        return checkbox_func
    
    def make_open_subject_func(self, subject_dp_tracker: dict[str, Any]):
        def open_subject():
            widget: QWidget = subject_dp_tracker["widget"]
            
            subject_dp_tracker["icon"].setAngle(0 if subject_dp_tracker["icon"].angle != 0 else 270)
            
            if widget.isVisible():
                widget.setVisible(False)
            else:
                widget.setVisible(True)
        
        return open_subject
    
    def make_odp_func(self, content, class_id: str, class_check_box_tracker):
        open_dp_func = self.make_open_dp_func(class_id, class_check_box_tracker)
        
        def func():
            if class_id in content and content[class_id][0]:
                return
            
            open_dp_func()
        
        return func

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
        week_total: int,
        saved_state_changed: pyqtBoundSignal
    ):
        super().__init__(title, info, saved_state_changed)
        
        self.setFixedSize(600, 400)
        
        self.week_total = week_total
        
        self.subject_widgets: dict[str, QWidget] = {}
        self.number_edits: dict[str, tuple[NumberLineEdit, NumberLineEdit]] = {}
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.container_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.container)
        
        self.main_layout.addWidget(self.scroll_area)
        
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
        
        self.container_layout.addStretch()
    
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
        
        self.container_layout.addWidget(selection_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.number_edits[subject_id] = per_day_edit, per_week_edit
        self.subject_widgets[subject_id] = selection_widget
    
    def make_per_day_text_changed_func(self, subject_id: str, input_edit: 'NumberLineEdit'):
        def text_changed_func():
            self.info[subject_id][1]["per_day"] = input_edit.number() # type: ignore
            
            self.saved_state_changed.emit()
        
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
            
            self.saved_state_changed.emit()
        
        return text_changed_func

class OptionsMaker(BaseSettingDialog):
    def __init__(self, title: str, info: dict[str, str], saved_state_changed: pyqtBoundSignal):
        super().__init__(title, info, saved_state_changed)
        self.option_widgets: dict[str, _OW_Entry] = {}
        self.current_row = 0
        self.current_col = 0
        self.max_cols = 4  # Maximum number of columns before wrapping
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        del self.container, self.container_layout
        
        self.container = QWidget()
        self.container_layout = QGridLayout(self.container)  # Use QGridLayout
        self.container_layout.setSpacing(4)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.container)
        
        self.add_button = QPushButton("Add Option")
        self.add_button.clicked.connect(lambda: self.add_option())
        
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        temp_option = _OW_Entry("IFE")
        self.setFixedSize((temp_option.width() + (temp_option.main_layout.spacing() * 4) + self.container_layout.spacing()) * self.max_cols, 300)
        
        del temp_option
        
        # Load existing options
        for option_id, option_name in self.info.items():
            self.add_option(option_id, option_name)
    
    def go_to(self, _id: str):
        for option_id, widget in self.option_widgets.items():
            if option_id == _id:
                def func():
                    self.scroll_area.verticalScrollBar().setValue(widget.y())
                    widget.setFocus()
                
                QTimer.singleShot(200, func)
                
                break
    
    def add_option(self, _id: str | None = None, text: str | None = None):
        option = _OW_Entry(text)
        
        _id = str(hex(id(option)).lower().replace("0x", "")) if _id is None else _id
        
        def update_option():
            self.info[_id] = option.get_text()
            self.saved_state_changed.emit()
        
        update_option()
        
        option.finished_editing_signal.connect(update_option)
        
        def remove_option():
            self.info.pop(_id)
            self.option_widgets.pop(_id)
            self.container_layout.removeWidget(option)
            option.deleteLater()
            self.reflow_items()  # Reflow remaining items
        
        option.deleted.connect(remove_option)
        self.option_widgets[_id] = option
        
        # Add to grid and wrap to next row if needed
        self.container_layout.addWidget(option, self.current_row, self.current_col)
        self.current_col += 1
        if self.current_col >= self.max_cols:
            self.current_col = 0
            self.current_row += 1
        
        if text is None:
            option.start_editing()
    
    def reflow_items(self):
        # Remove all widgets from grid
        for option in self.option_widgets.values():
            self.container_layout.removeWidget(option)
        
        # Re-add widgets in order
        self.current_row = 0
        self.current_col = 0
        for option in self.option_widgets.values():
            self.container_layout.addWidget(option, self.current_row, self.current_col)
            self.current_col += 1
            if self.current_col >= self.max_cols:
                self.current_col = 0
                self.current_row += 1
    
    def closeEvent(self, a0):
        for option in self.option_widgets.values():
            if option.is_editing:
                QMessageBox.critical(self, "Setting OM Error", "Please finish edting the option")
                a0.ignore() # type: ignore
                option.start_editing()
                return
        
        return super().closeEvent(a0)

class OptionSelector(BaseSettingDialog):
    closed = pyqtSignal()
    
    def __init__(self, title: str, info: dict[str, list[str] | dict[int, str]], saved_state_changed: pyqtBoundSignal):
        super().__init__(title, info, saved_state_changed)
        self.setFixedHeight(400)
        
        self.content = self.info["content"]
        self.id_mapping = self.info["id_mapping"]
        
        self.main_options_rows_layout_list: list[QHBoxLayout] = []
        self.sub_options_rows_layout_list: list[QHBoxLayout] = []
        
        self.main_options_tracker: list[list[_OW_Entry]] = []
        self.sub_options_tracker: list[list[QLabel]] = []
        
        self.container_layout.setSpacing(10)
        
        self.container.setContentsMargins(10, 10, 10, 10)
        
        
        self.main_max_cols = 4
        
        main_options_widget = QWidget()
        self.main_options_layout = QVBoxLayout(main_options_widget)
        
        # main_options_scroll_area = QScrollArea()
        # main_options_scroll_area.setProperty("class", "MainOptionSelector")
        # main_options_scroll_area.setWidget(main_options_widget)
        
        main_options_widget.setProperty("class", "MainOptionSelector")
        main_options_widget.setLayout(self.main_options_layout)
        
        for index, option_name in enumerate(self.content[:self.content.index(None)].copy()):
            self._add_new_option(option_name, index)
        
        
        self.sub_max_cols = 6
        
        sub_options_widget = QWidget()
        self.sub_options_layout = QVBoxLayout(sub_options_widget)
        
        # sub_options_scroll_area = QScrollArea()
        # sub_options_scroll_area.setProperty("class", "SubOptionSelector")
        # sub_options_scroll_area.setWidget(sub_options_widget)
        
        sub_options_widget.setProperty("class", "SubOptionSelector")
        sub_options_widget.setLayout(self.sub_options_layout)
        
        for index, option_name in enumerate(self.content[self.content.index(None) + 1:].copy()):
            self._remove_new_option(option_name, index)
        
        self.container_layout.setSpacing(20)
        
        self.container_layout.addWidget(QLabel("Selected"))
        self.container_layout.addWidget(main_options_widget, 8)
        self.container_layout.addWidget(QLabel("Unselected"))
        self.container_layout.addWidget(sub_options_widget, 2)
        # self.container_layout.addWidget(main_options_scroll_area, 7)
        # self.container_layout.addWidget(sub_options_scroll_area, 3)
        
        
        self.main_layout.addWidget(self.container)
        
        temp_option = _OW_Entry("Ife")
        self.setFixedWidth((temp_option.width() + (temp_option.main_layout.spacing() * 4) + self.main_options_layout.spacing()) * self.sub_max_cols)
    
    def _make_add_option_func_in_remove_opt(self, name: str, option: QLabel):
        def add_option(_):
            opt_index = None
            
            for row_index, option_row in enumerate(self.sub_options_tracker):
                if option in option_row:
                    opt_index = option_row.index(option) + self.sub_max_cols*row_index
                    break
            else:
                raise ValueError(f"{option} is not in the sub options tracker")
            
            row = opt_index // self.sub_max_cols
            col = opt_index % self.sub_max_cols
            
            self.sub_options_rows_layout_list[row].removeWidget(self.sub_options_tracker[row][col])
            old_option = self.sub_options_tracker[row].pop(col)
            old_option.deleteLater()
            
            self._add_new_option(name, opt_index)
            
            none_index = self.content.index(None)
            
            content_sub_opt_index = opt_index + none_index + 1
            
            id_mapping_copy = self.id_mapping.copy()
            for i in id_mapping_copy:
                if none_index < i < content_sub_opt_index:
                    self.id_mapping[i + 1] = id_mapping_copy[i]
            
            self.id_mapping[none_index] = self.id_mapping.pop(none_index + 1)
            
            self.content.insert(none_index, self.content.pop(content_sub_opt_index))
        
        return add_option
    
    def _make_remove_option_func_in_add_opt(self, name: str, option: "_OW_Entry"):
        def remove_option():
            opt_index = None
            
            for row_index, option_row in enumerate(self.main_options_tracker):
                if option in option_row:
                    opt_index = option_row.index(option) + self.main_max_cols*row_index
                    break
            else:
                raise ValueError(f"{option} is not in the main options tracker")
            
            row = opt_index // self.main_max_cols
            col = opt_index % self.main_max_cols
            
            self.main_options_rows_layout_list[row].removeWidget(self.main_options_tracker[row][col])
            old_option = self.main_options_tracker[row].pop(col)
            old_option.deleteLater()
            
            self._remove_new_option(name, opt_index)
            
            id_mapping_copy = self.id_mapping.copy()
            for i in id_mapping_copy:
                if i > opt_index:
                    self.id_mapping[i - 1] = id_mapping_copy[i]
            
            self.id_mapping[len(self.content) - 1] = self.id_mapping.pop(opt_index)
            
            self.content.append(self.content.pop(opt_index))
        
        return remove_option
    
    def _add_new_option(self, name: str, index: int):
        option = _OW_Entry(name)
        
        option.deleted.disconnect()
        option.deleted.connect(self._make_remove_option_func_in_add_opt(name, option))
        option.started_editing_signal.disconnect()
        
        row = index // self.main_max_cols
        col = index % self.main_max_cols
        
        if row + 1 >= len(self.main_options_tracker):
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            
            row_widget.setProperty("class", "OptionSelectorRow")
            row_widget.setLayout(row_layout)
            
            self.main_options_layout.addWidget(row_widget)
            
            self.main_options_rows_layout_list.append(row_layout)
            self.main_options_tracker.append([])
        
        if col < len(self.main_options_tracker[row]):
            self.main_options_rows_layout_list[row].insertWidget(col, option)
            self.main_options_tracker[row].insert(col, option)
        else:
            self.main_options_rows_layout_list[row].addWidget(option)
            self.main_options_tracker[row].append(option)
    
    def _remove_new_option(self, name: str, index: int):
        option = QLabel(name)
        
        option.setFixedWidth(150)
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        option.setProperty("class", "OptionSelectorNotSelected")
        option.mousePressEvent = self._make_add_option_func_in_remove_opt(name, option)
        
        row = index // self.sub_max_cols
        col = index % self.sub_max_cols
        
        if row + 1 >= len(self.sub_options_rows_layout_list):
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            
            row_widget.setProperty("class", "OptionSelectorRow")
            row_widget.setLayout(row_layout)
            
            self.sub_options_layout.addWidget(row_widget)
            
            self.sub_options_rows_layout_list.append(row_layout)
            self.sub_options_tracker.append([])
        
        if col < len(self.sub_options_tracker[row]):
            self.sub_options_rows_layout_list[row].insertWidget(col, option)
            self.sub_options_tracker[row].insert(col, option)
        else:
            self.sub_options_rows_layout_list[row].addWidget(option)
            self.sub_options_tracker[row].append(option)
    
    def get_selected(self):
        return self.info["content"][:self.info["content"].index(None)]
    
    def close(self):
        self.closed.emit()
        return super().close()



class _WidgetDropdown(QWidget):
    def __init__(self, title: str, widget: QWidget, parent=None):
        super().__init__(parent)
        
        self.widget = widget
        
        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.setLayout(layout)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.container.setLayout(self.main_layout)
        
        self.container.setProperty("class", "Bordered")
        self.container.setProperty("class", "DropdownCheckboxes")
        
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
        
        self.main_layout.addWidget(header)
        self.main_layout.addWidget(self.widget) # type: ignore
        
        layout.addWidget(self.container)
    
    def tdp_event_func(self, a0: QMouseEvent | None):
        if a0.button() == Qt.MouseButton.LeftButton: # type: ignore
            self.toogle_widget()
    
    def toogle_widget(self):
        self.toogle_icon.setAngle(0 if self.toogle_icon.angle != 0 else 270)
        self.widget.setVisible(not self.widget.isVisible())

class _OW_Entry(QWidget):
    deleted = pyqtSignal()
    started_editing_signal = pyqtSignal()
    finished_editing_signal = pyqtSignal()
    
    def __init__(self, initial_text: str | None = None):
        super().__init__()
        self.setProperty("class", "OptionTag")
        
        self.text = initial_text if initial_text is not None else ""
        self.is_editing = False
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 2, 4, 2)
        self.main_layout.setSpacing(4)
        
        # Input mode widgets
        self.input = QLineEdit()
        self.input.setProperty("class", "OptionEdit")
        self.input.setText(self.text)
        self.input.setPlaceholderText("Enter option")
        self.input.setFixedWidth(80)  # Fix input width
        self.input.returnPressed.connect(self.input.clearFocus)
        self.input.editingFinished.connect(self.finish_editing)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setProperty("class", "Close")
        self.close_btn.clicked.connect(self.remove)
        self.close_btn.setFixedSize(20, 20)
        
        self.deleted.connect(self.deleteLater)
        self.started_editing_signal.connect(self.start_editing)
        self.finished_editing_signal.connect(self._finished_editing)
        
        # Label mode widget
        self.label = QLabel(self.text)
        self.label.setMinimumWidth(80)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.mousePressEvent = lambda _: self.started_editing_signal.emit()
        
        # Initialize both widgets but hide input initially
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.input)
        self.main_layout.addWidget(self.close_btn)
        self.input.hide()
        
        self.setFixedHeight(30)
        self.setFixedWidth(130)
    
    def _finished_editing(self):
        if self.is_editing:
            self.text = self.input.text().strip()
            self.is_editing = False
            self.setup_display_mode()
            self.label.setText(self.text)
            self.label.show()
    
    def setup_display_mode(self):
        self.label.show()
        self.input.hide()
        self.close_btn.show()
    
    def setup_edit_mode(self):
        self.label.hide()
        self.input.show()
        self.close_btn.show()
    
    def start_editing(self):
        if not self.is_editing:
            self.input.setText(self.text)
            self.setup_edit_mode()
            self.input.setFocus()
            
            self.is_editing = True
    
    def finish_editing(self):
        self.finished_editing_signal.emit()
    
    def remove(self):
        self.deleted.emit()
    
    def get_text(self):
        return self.text

class _SL_SelectedWidget(BaseWidget):
    def __init__(self, id: ID, text: str, host_container_layout: QVBoxLayout):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "SelectedSelectionListEntry")
        
        self.id = id
        self.text = text
        self.host_container_layout = host_container_layout
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(self.text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        self.delete_self()
        
        return super().mousePressEvent(a0)
    
    @Hook(CONNECTIONS_MANAGER.getVar(), SignalType.SOURCE)
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
    def __init__(self, _id: str, text: str, host_container_layout: QVBoxLayout):
        super().__init__(QHBoxLayout)
        
        self.setProperty("class", "UnselectedSelectionListEntry")
        
        self.id = _id
        self.text = text
        self.host_container_layout = host_container_layout
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(text)
        
        self.addWidget(label)
        self.addStretch()
    
    def mousePressEvent(self, a0):
        self.add_self()
        
        return super().mousePressEvent(a0)
    
    @Hook(CONNECTIONS_MANAGER.getVar(), SignalType.SOURCE)
    def add_self(self):
        self.host_container_layout.removeWidget(self)
        
        widget = _SL_SelectedWidget(self.id, self.text, self.host_container_layout)
        
        insert_index = 0
        for i in range(self.host_container_layout.count()):
            if isinstance(self.host_container_layout.itemAt(i).widget(), _SL_SelectedWidget):
                insert_index = i + 1
        
        self.host_container_layout.insertWidget(insert_index, widget)
        
        self.deleteLater()

# Fix the dynamic hook routing issue
