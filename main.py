import pygame

from utils import *
from imports import *

from widgets.base import *
from widgets.settings import SubjectsMainWidget, TeachersMainWidget, ClassLevelsMainWidget
from widgets.user_interface import MainTitleBar
from widgets.timetable import SchoolTimetableEditor
from widgets.export import ExportsEditorDialogWidget

pygame.init()

class Window(QMainWindow):
    saved_state_changed = pyqtSignal(bool)
    crashed_signal = pyqtSignal(Exception)
    
    def __init__(self, arguments: list[str]):
        super().__init__()
        
        self.crashed_signal.connect(lambda e: QMessageBox.critical(None, e.__class__.__name__, str(e)))
        
        def ssc_func(state: bool):
            if state:
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
        self.timetable_widget = SchoolTimetableEditor()
        
        self.subjects_widget = SubjectsMainWidget(self.timetable_widget)
        self.teachers_widget = TeachersMainWidget(self.timetable_widget)
        self.classes_widget = ClassLevelsMainWidget(self.timetable_widget)
        
        # Create viewing container
        main_container = BaseWidget()
        main_container.setContentsMargins(0, 0, 5, 5)
        
        self.title_bar = MainTitleBar(self, menu_bar, self._get_search_scope, self._goto_search, self.go_back, self.go_forward)
        main_container.addWidget(self.title_bar)
        
        # Create viewing container
        viewing_container = BaseWidget(QHBoxLayout)
        viewing_container.setContentsMargins(0, 10, 5, 5)
        main_container.addWidget(viewing_container)
        
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
        timetable_btn = QPushButton("Timetable")
        
        # Add widgets to stack
        self.is_option_sidebar_focused = True
        self.option_buttons = [subjects_btn, teachers_btn, classes_btn, timetable_btn]
        
        self.stack.addWidget(self.subjects_widget)
        self.stack.addWidget(self.teachers_widget)
        self.stack.addWidget(self.classes_widget)
        self.stack.addWidget(self.timetable_widget)
        
        # Connect buttons
        for index, button in enumerate(self.option_buttons):
            button.setCheckable(True)
            button.clicked.connect(self.make_option_button_func(button.text(), index))
            self.sub_sidebar_widget.addWidget(button)
        
        self.sub_sidebar_widget.insertStretch(3)
        
        # Add sub sidebar widgets to main sidebar layout
        main_sidebar_widget.addWidget(self.sub_sidebar_widget)
        # main_sidebar_widget.addWidget(self.toggle_sidebar_button)
        
        # Add widgets to main layout
        viewing_container.addWidget(main_sidebar_widget)
        viewing_container.addWidget(self.stack)
        
        self.setCentralWidget(main_container)
        subjects_btn.click()  # Start with subjects page selected
        
        self.go_back_action.setDisabled(True)
        self.title_bar.go_back_button.setDisabled(True)
        
        self.go_forward_action.setDisabled(True)
        self.title_bar.go_forward_button.setDisabled(True)
        
        self.view_tracker = [self.option_buttons[0]]
    
    def _file_init(self, index: int, arg: str):
        if index == 0:
            self.export_editor = ExportsEditorDialogWidget(self)
            self.file = FileManager(self, self.export_editor, None, f"{FT_MAPPING[TABLE_EXTENSION_TYPE]};;{FT_MAPPING[TEMPLATE_EXTENSION_TYPE]}")
        elif index == 1:
            self.file.path = arg
    
    def _set_file_type(self, arg: str):
        self._open_file_type = arg
    
    def _goto_search(self, sw: BaseSettingEntry):
        current_display_widget = self.stack.currentWidget()
        
        if isinstance(current_display_widget, BaseSettingWidget):
            current_display_widget.scroll_widget.getScrollWidget().verticalScrollBar().setValue(sw.y())
            sw.focusInput()
    
    def _get_search_scope(self):
        display_data = SCHOOL.subjects, SCHOOL.teachers, SCHOOL.class_levels
        
        current_display_index = self.stack.currentIndex()
        current_display_widget = self.stack.currentWidget()
        
        if isinstance(current_display_widget, BaseSettingWidget):
            return (
                sorted(
                    [
                        (sw, " ".join(display_data[current_display_index][sw_id].name.full()), (display_data[current_display_index][sw_id].name.short() if display_data[current_display_index][sw_id].name.full() != display_data[current_display_index][sw_id].name.short() else None, sw_id, None), [])
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
            SCHOOL.set(self.LOADED_SCHOOL)
            
            self.saved_callback()
        else:
            self.setWindowTitle(self.title)
        
        THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
        
        self.export_editor._init(self.file)
        self.file.set_callbacks(self.save_callback, self.open_callback, self.export_editor.export_callback)
    
    def load(self):
        assert self.file.path
        
        if self._open_file_type is None:
            print("No file type specified; Defaulting to default file type")
            
            self._open_file_type = TABLE_EXTENSION_TYPE
        
        if self._open_file_type == TABLE_EXTENSION_TYPE:
            with open(self.file.path, "rb") as file:
                data = pickle.load(file)
        elif self._open_file_type == TEMPLATE_EXTENSION_TYPE:
            with open(self.file.path, "r") as file:
                data = SCHOOL.from_template(file.read())
        else:
            raise TypeError(f"Unsupported file type: '{self._open_file_type}'")
        
        return data
    
    def unsaved_callback(self):
        self.saved = False
        
        if self.file.path is not None:
            self.setWindowTitle(f"{self.title} - {Path(self.file.path).absolute().as_posix()} *Unsaved")
        else:
            self.setWindowTitle(self.title)
    
    def saved_callback(self):
        self.saved = True
        self.setWindowTitle(f"{self.title} - {Path(self.file.path).absolute().as_posix()}")
    
    def open_callback(self, path: Optional[str] = None, file_type: Optional[str] = None):
        arguments = [c for i, c in enumerate(["main.py", f'-ft={REV_FT_MAPPING[file_type]}', path]) if i == 0 or (i == 1 and file_type is not None) or (i == 2 and path is not None)]
        
        win = Window(arguments)
        win.show()
        
        if not hasattr(self, '_windows'):
            self._windows = []
        self._windows.append(win)
    
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
        go_menu = menubar.addMenu("Go")
        palette_menu = menubar.addMenu("Palette")
        help_menu = menubar.addMenu("Help")
        
        # Add all actions
        file_menu.addAction("New", "Ctrl+N", self.file.new)
        file_menu.addSeparator()
        file_menu.addAction("Open", "Ctrl+O", self.file.open)
        file_menu.addSeparator()
        file_menu.addAction("Save", "Ctrl+S", self.file.save)
        file_menu.addAction("Save As", "Ctrl+Shift+S", self.file.save_as)
        file_menu.addSeparator()
        file_menu.addAction("Export Subjects", coming_soon)
        file_menu.addAction("Export Teachers", coming_soon)
        file_menu.addAction("Export Class Levels", coming_soon)
        file_menu.addAction("Export Timetable", lambda: self.export_editor.exec())
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
    
    def make_option_button_func(self, name: str, index: int):
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
                
                self.title_bar.search_pb.setText(f"Search {name}")
                
                if self.display_index != index:
                    self.title_bar.search_pb.setDisabled(index == 3)
                    self.stack.setCurrentIndex(index)
                
                self.display_index = index
            
            for i, btn in enumerate(self.option_buttons):
                btn.setChecked(i == index)
        
        return func
    
    def make_palette_action_func(self, main_color: str, accent_color: str):
        def palette_action_func():
            SCHOOL.settings.THEME = f"{main_color}-{accent_color}"
            THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
        
        return palette_action_func



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon("src/images/logo.ico"))
    
    THEME_MANAGER.set_application(app)
    
    window = Window(app.arguments())
    window.showMaximized()
    
    sys.exit(app.exec())
    
