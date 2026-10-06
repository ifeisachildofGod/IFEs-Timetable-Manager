import os
import subprocess
import traceback

import threading

from utils import *
from imports import *
from widgets import *

from AttendanceApp import AttendanceManager


class CmdListener(QObject):
    command_recieved = pySignal(str)
    listener_killed = pySignal()
    
    def start(self):
        def loop():
            print(f"TASS 1.0.0 on {os.name}")
            print('Type "help" for further information')
            
            while True:
                try:
                    cmd = input(">> ")
                    self.command_recieved.emit(cmd)
                except (EOFError, OSError):
                    self.listener_killed.emit()
                    print()
                    break
            
            print("TASS 1.0.0 says Goodbye")
        
        threading.Thread(target=loop, daemon=True).start()
class Window(QMainWindow):
    saved_state_changed = pySignal(bool)
    crashed_signal = pySignal(Exception)
    
    def __init__(self, arguments: list[str], cmd_listener: Optional[CmdListener] = None):
        super().__init__()
        
        if cmd_listener:
            cmd_listener.command_recieved.connect(self.handle_cmd)
            cmd_listener.listener_killed.connect(self.close)
        
        self.crashed_signal.connect(lambda e: QMessageBox.critical(None, e.__class__.__name__, str(e)))
        
        def ssc_func(state: bool):
            if state:
                if SCHOOL.settings.auto_save:
                    self.file.save()
                else:
                    self.unsaved_callback()
            else:
                self.saved_callback()
        
        self.saved_state_changed.connect(ssc_func)
        
        self.flag_mapping = {
            "-ft": self._set_file_type,
            "-ftype": self._set_file_type,
            
            "--arg--": self._file_init
        }
        
        self._open_file_type = None
        self._default_file_path = None
        self.arguments = arguments
        
        i = 0
        for arg in self.arguments:
            arg = arg.strip()
            
            if "=" in arg:
                n, v = arg.split("=")
                
                self.flag_mapping[n](v)
            elif arg.startswith("--") and not arg.endswith("--"):
                self.flag_mapping[arg[2:]]()
            else:
                self.flag_mapping["--arg--"](i, arg)
                
                i += 1
        
        self.title = "IFEs Timetable Generator"
        
        # Setting resize geometry
        self.setGeometry(100, 100, 1000, 700)
        
        # Create menu bar
        menu_bar = self.create_menu_bar()
        
        # Get saved data
        self.LOADED_SCHOOL = None
        
        self._init_save_data()
        
        # Misc
        self.display_index = 0
        self.prev_display_index = 0
        
        self.go_focus_index = 0
        
        # Make settings widgets
        self.attendance_manager = AttendanceManager()
        self.timetable_widget = SchoolTimetableEditor()
        
        self.subjects_widget = SubjectsMainWidget(self.timetable_widget, self.attendance_manager)
        self.teachers_widget = TeachersMainWidget(self.timetable_widget, self.attendance_manager)
        self.classes_widget = ClassLevelsMainWidget(self.timetable_widget, self.attendance_manager)
        
        self.attendance_manager.search_state_changed.connect(lambda v: self.title_bar.search_pb.setDisabled(not v))
        self.attendance_manager.search_state_changed.connect(lambda v: self.title_bar.search_pb.setText(f"Search {v}") if v else self.title_bar.search_pb.setText(None))
        
        # Title bar widget
        self.title_bar = MainTitleBar(self, menu_bar, self._get_search_scope, self._goto_search, self.go_back, self.go_forward)
        
        # Create viewing container
        viewing_container = BaseWidget(QHBoxLayout)
        viewing_container.setContentsMargins(0, 10, 5, 5)
        
        # Create sidebar
        main_sidebar_widget = BaseWidget(QHBoxLayout)
        main_sidebar_widget.setProperty("class", "Sidebar")
        
        self.sub_sidebar_widget = BaseWidget()
        self.sub_sidebar_widget.setFixedWidth(200)
        self.sub_sidebar_widget.setProperty("class", "SubSidebar")
        
        self.sub_sidebar_widget.setSpacing(0)
        self.sub_sidebar_widget.setContentsMargins(0, 0, 0, 0)
        
        # Create stacked widget for content
        self.stack = QStackedWidget()
        
        # Create navigation buttons
        subjects_btn = QPushButton("Subjects")
        teachers_btn = QPushButton("Teachers")
        classes_btn = QPushButton("Class Levels")
        
        attendance_btn = QPushButton("Attendance")
        timetable_btn = QPushButton("Timetable")
        
        def reset(name: str):
            self.title_bar.search_pb.setDisabled(False)
            self.title_bar.search_pb.setText(f"Search {name}")
        
        def on_att_widget_func(name):
            reset(name)
            
            if self.attendance_manager.current_tab and (func := self.attendance_manager.tab_src_changed_func_mapping[self.attendance_manager.current_tab]):
                try:
                    func(self.attendance_manager.tab_name_index_mapping[self.attendance_manager.current_tab], True)
                except TypeError:
                    func(self.attendance_manager.tab_name_index_mapping[self.attendance_manager.current_tab])
        
        def on_ttbl_widget_func(_):
            self.title_bar.search_pb.setDisabled(True)
            self.title_bar.search_pb.setText(None)
        
        # Add widgets to stack
        self.is_option_sidebar_focused = True
        self.option_buttons: list[Optional[tuple[QPushButton, BaseSettingWidget | SchoolTimetableEditor | AttendanceManager]]] = [
            (subjects_btn, (self.subjects_widget, reset)),
            (teachers_btn, (self.teachers_widget, reset)),
            (classes_btn, (self.classes_widget, reset)),
            None,
            (attendance_btn, (self.attendance_manager, on_att_widget_func)),
            (timetable_btn, (self.timetable_widget, on_ttbl_widget_func))
        ]
        
        # Connect buttons
        for index, op_info in enumerate(self.option_buttons):
            if op_info is not None:
                button, widget_info = op_info
                
                if isinstance(widget_info, tuple):
                    widget, custom_func = widget_info
                else:
                    widget = widget_info
                    custom_func = None
                
                button.setCheckable(True)
                button.clicked.connect(self.make_option_button_func(button.text(), index, custom_func))
                
                self.stack.addWidget(widget)
                self.sub_sidebar_widget.addWidget(button)
            else:
                self.sub_sidebar_widget.addStretch()
        
        # Add sub sidebar widgets to main sidebar layout
        main_sidebar_widget.addWidget(self.sub_sidebar_widget)
        # main_sidebar_widget.addWidget(self.toggle_sidebar_button)
        
        # Add widgets to main layout
        viewing_container.addWidget(main_sidebar_widget)
        viewing_container.addWidget(self.stack)
        
        subjects_btn.click()  # Start with subjects page selected
        
        self.go_back_action.setDisabled(True)
        self.title_bar.go_back_button.setDisabled(True)
        
        self.go_forward_action.setDisabled(True)
        self.title_bar.go_forward_button.setDisabled(True)
        
        self.view_tracker = [self.option_buttons[0]]
        
        self.auto_save_action.setChecked(SCHOOL.settings.auto_save)
        
        # Create viewing widget
        central_widget = BaseWidget()
        central_widget.setContentsMargins(0, 0, 5, 5)
        
        central_widget.addWidget(self.title_bar)
        central_widget.addWidget(viewing_container)
        
        self.setCentralWidget(central_widget)
        
        self.CMD_ACTIONS = self._get_cmd_actions()
    
    def _file_init(self, index: int, arg: str):
        if index == 0:
            self.export_editor = ExportsEditorDialogWidget(self)
            self.file = FileManager(self, self.export_editor, None, f"{FT_MAPPING[TABLE_EXTENSION_TYPE]};;{FT_MAPPING[TEMPLATE_EXTENSION_TYPE]}")
        elif index == 1:
            self.file.path = arg
    
    def _set_file_type(self, arg: str):
        self._open_file_type = arg
    
    def _get_cmd_actions(self):
        cmd_actions = {
            "NEW": self.file.new,
            "OPEN": self.file.open,
            "SAVE": self.file.save,
            "SAVE-AS": self.file.save_as,
            "QUIT": self.close,
            
            "HELP": lambda: print("Not Implemented")
        }
        
        cmd_actions.update({n.lower(): f for n, f in cmd_actions.items()})
        
        return cmd_actions
    
    def _goto_search(self, sw: BaseSettingEntry):
        current_display_index = self.stack.currentIndex()
        
        if current_display_index == 3:
            if self.attendance_manager.search_state:
                widget = self.attendance_manager.get(self.attendance_manager.current_tab)
                widget.search_goto(sw)
        else:
            current_display_widget = self.stack.currentWidget()
            
            if isinstance(current_display_widget, BaseSettingWidget):
                current_display_widget.scroll_widget.scroll_to(sw, 100)
                sw.focusInput()
    
    def _get_search_scope(self):
        current_display_index = self.stack.currentIndex()
        
        if current_display_index == 3:
            if self.attendance_manager.search_state:
                widget = self.attendance_manager.stack.currentWidget()
                return widget.search_get_scope()
        else:
            display_data = SCHOOL.subjects, SCHOOL.teachers, SCHOOL.class_levels
            
            current_display_widget = self.stack.currentWidget()
            
            if isinstance(current_display_widget, BaseSettingWidget):
                return (
                    sorted(
                        [
                            (sw, "".join(display_data[current_display_index][sw_id].name.full()), (display_data[current_display_index][sw_id].name.short() if display_data[current_display_index][sw_id].name.full() != display_data[current_display_index][sw_id].name.short() else None, sw_id, None), [])
                            for sw_id, sw in
                            current_display_widget.widgets.items()
                        ],
                        key=lambda params: params[1]
                        )
                    )
    
    def _init_save_data(self):
        self.saved = True
        
        if self.file.path is not None:
            self.LOADED_SCHOOL = self.load()
            
            if self.LOADED_SCHOOL is not None:
                SCHOOL.set(self.LOADED_SCHOOL)
                self.saved_callback()
        else:
            self.setWindowTitle(self.title)
        
        THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
        
        self.export_editor._init(self.file)
        self.file.set_callbacks(self.save_callback, self.open_callback, self.export_editor.export_callback)
    
    def _parse_string_arg(self, arg: str):
        # index = arg.find(":")
        # a_type, a_value = arg[:index], arg[index + 1:]
        
        # def str_func(v: str):
        #     assert v.startswith('"') and v.endswith('"')
        #     return v.removeprefix('"').removesuffix('"')
        
        # def list_func(v: str):
        #     assert v.startswith('[') and v.endswith(']')
        #     return v.removeprefix('[').removesuffix(']').split()
        
        # {
        #     "str": str_func,
        #     "list": list_func,
        # }
        
        return arg
    
    def handle_cmd(self, cmd: str):
        key, *values = cmd.split()
        
        if key in self.CMD_ACTIONS:
            self.CMD_ACTIONS[key](*[self._parse_string_arg(arg) for arg in values])
    
    def load(self):
        try:
            assert self.file.path
            
            if self._open_file_type == ALL_EXTENSION_TYPE:
                self._open_file_type = None
            
            if self._open_file_type is None:
                try:
                    with open(self.file.path, "r") as file:
                        data = SCHOOL.from_template(file.read())
                
                    self._open_file_type = TEMPLATE_EXTENSION_TYPE
                except Exception as e:
                    with open(self.file.path, "rb") as file:
                        data = pickle.load(file)
                    
                    self._open_file_type = TABLE_EXTENSION_TYPE
            else:
                if self._open_file_type == TABLE_EXTENSION_TYPE:
                    with open(self.file.path, "rb") as file:
                        data = pickle.load(file)
                elif self._open_file_type == TEMPLATE_EXTENSION_TYPE:
                    with open(self.file.path, "r") as file:
                        data = SCHOOL.from_template(file.read())
                else:
                    raise TypeError(f"Unsupported file type: '{self._open_file_type}'")
            
            return data
        except Exception as e:
            QMessageBox.critical(None, e.__class__.__name__, str(e))
            traceback.print_exc()
            
            self.saved = True
            QTimer.singleShot(500, lambda: self.close())
    
    def unsaved_callback(self):
        self.saved = False
        
        if self.file.path is not None:
            self.setWindowTitle(f"{self.title} - {os.path.abspath(self.file.path)} *Unsaved")
        else:
            self.setWindowTitle(self.title)
    
    def saved_callback(self):
        self.saved = True
        self.setWindowTitle(f"{self.title} - {os.path.abspath(self.file.path)}")
    
    def open_callback(self, path: Optional[str] = None, file_type: Optional[str] = None):
        arguments = []
        
        if path is not None or file_type is not None:
            arguments = [f'-ft={REV_FT_MAPPING[file_type]}', path]
        elif path is not None:
            arguments = [path]
        
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable] + arguments)
        else:
            subprocess.Popen([sys.executable, __file__] + arguments)
    
    def save_callback(self, path: str, file_type: Optional[str] = None, school: Optional[School] = None):
        self.file.path = path
        
        if school is None:
            school = SCHOOL
        
        self._open_file_type = REV_FT_MAPPING[file_type] if file_type is not None else self._open_file_type
        
        if self._open_file_type == TABLE_EXTENSION_TYPE:
            with open(self.file.path, "wb") as file:
                pickle.dump(school, file)
        elif self._open_file_type == TEMPLATE_EXTENSION_TYPE:
            with open(self.file.path, "w", encoding="utf-8") as file:
                file.write(school.framework())
        else:
            raise TypeError(f"Unsupported file type: '{self._open_file_type}'")
        
        self.saved_state_changed.emit(False)
    
    def undo(self):
        undo_func = self.focusWidget().__dict__.get("undo")
        if undo_func is not None:
            undo_func()
    
    def redo(self):
        redo_func = self.focusWidget().__dict__.get("redo")
        if redo_func is not None:
            redo_func()
    
    def go_back(self):
        if self.go_focus_index > 0:
            self.go_focus_index -= 1
            
            self.go_forward_action.setDisabled(False)
            self.title_bar.go_forward_button.setDisabled(False)
            
            self.is_option_sidebar_focused = False
            self.view_tracker[self.go_focus_index].click()
            self.is_option_sidebar_focused = True
        
        if self.go_focus_index == 0:
            self.go_back_action.setDisabled(True)
            self.title_bar.go_back_button.setDisabled(True)
    
    def go_forward(self):
        if self.go_focus_index < len(self.view_tracker) - 1:
            self.go_focus_index += 1
            
            self.go_back_action.setDisabled(False)
            self.title_bar.go_back_button.setDisabled(False)
            
            self.is_option_sidebar_focused = False
            self.view_tracker[self.go_focus_index].click()
            self.is_option_sidebar_focused = True
        
        if self.go_focus_index == len(self.view_tracker) - 1:
            self.go_forward_action.setDisabled(True)
            self.title_bar.go_forward_button.setDisabled(True)
    
    def create_menu_bar(self):
        menubar = QMenuBar()
        
        coming_soon = lambda: QMessageBox.information(self, "Coming Soon", "This feature has not been implemented yet")
        
        # File Menu
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        attendance_menu = menubar.addMenu("Attendance")
        go_menu = menubar.addMenu("Go")
        palette_menu = menubar.addMenu("Palette")
        help_menu = menubar.addMenu("Help")
        
        # Add all actions
        def auto_save_clicked(state):
            SCHOOL.settings.auto_save = state
            
            self.file.save()
        
        self.auto_save_action = QAction("Auto Save", self)
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.triggered.connect(auto_save_clicked)
        
        file_menu.addAction("New", "Ctrl+N", self.file.new)
        file_menu.addSeparator()
        file_menu.addAction("Open", "Ctrl+O", self.file.open)
        file_menu.addSeparator()
        file_menu.addAction("Save", "Ctrl+S", self.file.save)
        file_menu.addAction("Save As", "Ctrl+Shift+S", self.file.save_as)
        file_menu.addAction(self.auto_save_action)
        file_menu.addSeparator()
        file_menu.addAction("Export", lambda: self.export_editor.exec())
        file_menu.addSeparator()
        file_menu.addAction("Close", self.close)
        
        # Add Edit Actions
        edit_menu.addAction("Redo", "Ctrl+Y", self.redo)
        edit_menu.addAction("Undo", "Ctrl+Z", self.undo)
        edit_menu.addSeparator()
        edit_menu.addAction("Cut", "Ctrl+X", coming_soon)
        edit_menu.addAction("Copy", "Ctrl+C", coming_soon)
        edit_menu.addAction("Paste", "Ctrl+V", coming_soon)
        edit_menu.addSeparator()
        edit_menu.addAction("Find", "Ctrl+F", coming_soon)
        
        attendance_menu.addAction("Connection", "Ctrl+Shift+A", lambda: self.attendance_manager.activate_connection_screen())
        
        self.go_back_action = go_menu.addAction("Back", self.go_back)
        self.go_forward_action = go_menu.addAction("Forward", self.go_forward)
        
        palette_action_group = QActionGroup(self)
        palette_action_group.setExclusive(True)
        
        palette_dict: dict[str, QMenu] = {}
        for name in THEME_MANAGER.themes:
            main_color, accent_color = name.split("-")
            
            if main_color not in palette_dict:
                palette_dict[main_color] = palette_menu.addMenu(main_color.title())
            
            accent_action = QAction(accent_color.title(), self)
            accent_action.setCheckable(True)
            if name == SCHOOL.settings.THEME:
                accent_action.setChecked(True)
            
            accent_action.triggered.connect(self.make_palette_action_func(main_color, accent_color))
            
            palette_action_group.addAction(accent_action)
            palette_dict[main_color].addAction(accent_action)
        
        help_menu.addAction("Welcome", coming_soon)
        help_menu.addSeparator()
        help_menu.addAction("Documentation", coming_soon)
        help_menu.addAction("View License", coming_soon)
        help_menu.addSeparator()
        help_menu.addAction("Check Updates", coming_soon)
        help_menu.addSeparator()
        help_menu.addAction("About", coming_soon)
        help_menu.addAction("What Next", coming_soon)
        
        return menubar
    
    def keyPressEvent(self, a0):
        if a0.key() == 16777220: # type: ignore
            focus_widget = self.focusWidget()
            
            if isinstance(focus_widget, QPushButton):
                focus_widget.click()
        
        return super().keyPressEvent(a0)
    
    def closeEvent(self, event):
        if not self.saved:
            reply = QMessageBox.question(self, "Save", "Save before quitting?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.file.save()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        event.accept()
    
    def make_option_button_func(self, name: str, index: int, custom_func: Optional[Callable[[str], None]]):
        def func():
            if self.display_index != index:
                if self.is_option_sidebar_focused:
                    self.go_focus_index += 1
                    
                    self.view_tracker[self.go_focus_index:] = []
                    
                    self.go_back_action.setDisabled(False)
                    self.title_bar.go_back_button.setDisabled(False)
                    
                    self.go_forward_action.setDisabled(True)
                    self.title_bar.go_forward_button.setDisabled(True)
                    
                    self.view_tracker.append(self.option_buttons[index])
                
                custom_func(name)
                widget_info = self.option_buttons[index][1]
                
                if isinstance(widget_info, tuple):
                    widget, _ = widget_info
                else:
                    widget = widget_info
                
                self.stack.setCurrentWidget(widget)
                
                self.display_index = index
            
            for i, op_info in enumerate(self.option_buttons):
                if op_info is not None:
                    btn, _ = op_info
                    
                    btn.setChecked(i == index)
        
        return func
    
    def make_palette_action_func(self, main_color: str, accent_color: str):
        def palette_action_func():
            SCHOOL.settings.THEME = f"{main_color}-{accent_color}"
            
            THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
            self.attendance_manager.THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
            self.attendance_manager.connection_set_up_screen.THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
            
            for lvl_id, level_widgets in self.timetable_widget.timetable_widgets.items():
                for cls_id, cls_ttbl in level_widgets.items():
                    for col, periods in enumerate(SCHOOL.class_levels[lvl_id].classes[cls_id].timetable.table.values()):
                        row = next(r for r, s in enumerate(periods) if s.id == BreakPeriod.id)
                        
                        break_item = cls_ttbl.item(row, col)
                        break_item.set_color()
        
        return palette_action_func


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("src/images/logo.png")))
    
    THEME_MANAGER.set_application(app)
    
    listener = CmdListener()
    window = Window(app.arguments(), listener)
    window.showMaximized()
    
    listener.start()
    
    sys.exit(app.exec())
    
