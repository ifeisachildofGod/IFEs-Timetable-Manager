from imports import *

from utils import *

from widgets.base import *
from widgets.settings import SubjectsMainWidget, TeachersMainWidget, ClassLevelsMainWidget
from widgets.timetable import SchoolTimetableEditor
from widgets.user_interface import MainTitleBar


class Window(QMainWindow):
    def __init__(self, arguments: list[str]):
        super().__init__()
        
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
        self.export_file_filter = "JSON File (*.json);;Image File (*.png *.jpg *.wpeg *.svg);;Microsoft Document (*.msix);;Pickle File (*.pickle);;CSV File (*.csv);;HTML File (*.html);;PDF File (*.pdf)"
        
        # Default data
        self.default_period_amt   =   10  # Being used by the timetable editor
        self.default_breakperiod  =   7   #   "     "   "  "      "       "
        self.default_per_day      =   2   # Being used by the classes editor
        self.default_per_week     =   4   #   "     "   "  "     "       "
        self.default_max_classes  =   3   # Being used by the teachers editor
        self.default_save_data    =   {"levels": [], "subjectTeacherMapping": {}}
        self.default_weekdays     =   ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        self.children_saved_tracker = {}
        
        # Setting resize geometry
        self.setGeometry(100, 100, 1000, 700)
        
        # Get saved data
        self._init_save_data()
        
        # Misc
        self.display_index = 0
        self.prev_display_index = 0
        
        self.go_focus_index = 0
        self.view_tracker = [0]
        
        menu_bar = self.create_menu_bar()
        
        # Make settings widgets
        self.timetable_widget = SchoolTimetableEditor()
        self.subjects_widget = SubjectsMainWidget()
        self.teachers_widget = TeachersMainWidget()
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
        classes_btn = QPushButton("Classes")
        timetable_btn = QPushButton("Timetable")
        
        # Add widgets to stack
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
    
    def _file_init(self, index: int, arg: str):
        if index == 0:
            self.file = FileManager(self, None, f"Timetable Files {TABLE_EXTENSION_TYPE};;Template Files {TEMPLATE_EXTENSION_TYPE}")
            self.file.set_callbacks(self.save_callback, self.open_callback, self.load_callback, None)  #, self.export_callback)
        elif index == 1:
            self.file.path = arg
    
    def _set_file_type(self, arg: str):
        self._open_file_type = arg
    
    def _goto_search(self, sw: QWidget):
        current_display_widget = self.stack.currentWidget()
        
        if isinstance(current_display_widget, BaseSettingWidget):
            current_display_widget.scroll_area.verticalScrollBar().setValue(sw.y())
    
    def _get_search_scope(self):
        display_data = SCHOOL.subjects, SCHOOL.teachers, SCHOOL.clasS_levels
        
        current_display_index = self.stack.currentIndex()
        current_display_widget = self.stack.currentWidget()
        
        if isinstance(current_display_widget, BaseSettingWidget):
            return (
                sorted(
                    [
                        (sw, " ".join(display_data[current_display_index][sw_id].name.full()), (None, sw_id, None), [])
                        for sw_id, sw in
                        current_display_widget.widgets.items()
                    ],
                    key=lambda params: params[1]
                    )
                )
        
    def _init_save_data(self):
        self.saved = True
        
        if self.file.path is not None:
            school = self.file.get_data(self._open_file_type)
            SCHOOL.set(school)
            
            self.saved_callback()
        else:
            self.setWindowTitle(self.title)
        
        THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
    
    def unsaved_callback(self):
        self.saved = False
        
        if self.file.path is not None:
            self.setWindowTitle(f"{self.title} - {Path(self.file.path).as_posix()} *Unsaved")
        else:
            self.setWindowTitle(self.title)
    
    def saved_callback(self):
        self.saved = True
        self.setWindowTitle(f"{self.title} - {Path(self.file.path).absolute().as_posix()}")
    
    def load_callback(self, path: str, file_type: str):
        if file_type == TABLE_EXTENSION_TYPE:
            with open(path, "rb") as file:
                data = pickle.load(file)
        elif file_type == TEMPLATE_EXTENSION_TYPE:
            with open(path, "r") as file:
                data = SCHOOL.from_template(file.read())
        else:
            raise TypeError(f"Unsupported file type: {file_type}")
        
        return data
    
    def open_callback(self, path: Optional[str] = None, file_type: Optional[str] = None):
        win = Window(["main.py", path, f'-ft={file_type}'] if None not in (path, file_type) else [])
        win.showMaximized()
        
        if not hasattr(self, '_windows'):
            self._windows = []
        self._windows.append(win)
    
    def save_callback(self, path: str, file_type: Optional[str] = None):
        self.file.path = path
        
        if file_type == TABLE_EXTENSION_TYPE:
            with open(self.file.path, "wb") as file:
                pickle.dump(SCHOOL, file)
        elif file_type == TEMPLATE_EXTENSION_TYPE:
            with open(self.file.path, "w") as file:
                file.write(SCHOOL.template())
        else:
            raise TypeError(f"Unsupported file type: {file_type}")
        
        self.saved_callback()
    
    # def export_callback(self, path: str, export_mode: int):
    #     if export_mode == 0:
    #         if path.endswith(("png", "jpg", "wpeg", "svg", "pdf", "html")):
    #             title = "Timetable"
                
    #             widgets = list(self.timetable_widget.timetable_widgets.values())
                
    #             widget = self.timetable_widget.exportify_widgets(widgets)
    #             widget.resize(QSize(max(w.columnCount() for w in widgets) * 90 + 114, widget.sizeHint().height()))
                
    #             if path.endswith("pdf"):
    #                 printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    #                 printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    #                 printer.setOutputFileName(path)
                    
    #                 painter = QPainter(printer)
    #                 widget.render(painter)
    #                 painter.end()
    #             elif path.endswith("html"):
    #                 style = """
    #                 body {
    #                     font-family: Arial, sans-serif;
    #                     padding: 20px;
    #                     background: #f9f9f9;
    #                 }

    #                 h2 {
    #                     text-align: left;
    #                     margin-bottom: 20px;
    #                 }

    #                 .timetable {
    #                     display: grid;
    #                     grid-template-columns: 100px repeat(5, 1fr);
    #                     border: 1px solid #ccc;
    #                     margin-bottom: 100px;
    #                 }

    #                 .cell {
    #                     border: 1px solid #ccc;
    #                     padding: 15px;
    #                     text-align: center;
    #                 }

    #                 .header {
    #                     background: black;
    #                     color: white;
    #                     font-weight: bold;
    #                 }
                    
    #                 .break {
    #                     background: #1f1f1f;
    #                     color: #1f1f1f;
    #                 }
    #                 """
                    
    #                 body = ""
    #                 for cls_ttbl in widgets:
    #                     ttbl_text = f'<div class="cell"></div>'
                        
    #                     for col in range(cls_ttbl.columnCount()):
    #                         ttbl_text += f'<div class="cell header">{cls_ttbl.horizontalHeaderItem(col).text()}</div>'
                        
    #                     for row in range(cls_ttbl.rowCount()):
    #                         ttbl_text += f'<div class="cell header">{cls_ttbl.verticalHeaderItem(row).text()}</div>'
    #                         for col in range(cls_ttbl.columnCount()):
    #                             item = cls_ttbl.item(row, col)
                                
    #                             ttbl_text += (
    #                                 f'<div class="cell break"></div>'
    #                                 if item.break_time else
    #                                 (
    #                                     f'<div class="cell"></div>'
    #                                     if item.free_period else
    #                                     f'<div class="cell">{item.subject.name}</div>'
    #                                 )
    #                             )
                        
    #                     body += f"""
    #                     <h2>{cls_ttbl.cls.name}</h2>
    #                     <div class="timetable">
    #                         {ttbl_text}
    #                     </div>
    #                     """
                    
    #                 html = f"""
    #                 <!DOCTYPE html>
    #                 <html lang="en">
    #                 <head>
    #                     <meta charset="UTF-8">
    #                     <meta name="viewport" content="width=device-width, initial-scale=1.0">
    #                     <title>{title}</title>
    #                     <style>
    #                         {style}
    #                     </style>
    #                 </head>
    #                     <body>
    #                         {body}
    #                     </body>
    #                 </html>
    #                 """
                    
    #                 with open(path, "w") as file:
    #                     file.write(html)
    #             # elif path.endswith("msix"):
    #             #     doc = Document()
                    
    #             #     doc.add_heading(title, level=1)
                    
    #             #     for cls_ttbl in widgets:
    #             #         doc.add_heading(cls_ttbl.cls.name, level=2)
                        
    #             #         # Create a Word table
    #             #         word_table = doc.add_table(cls_ttbl.rowCount(), cls_ttbl.columnCount())
    #             #         word_table.style = "Table Grid"
                        
                        
    #             #         for row in range(cls_ttbl.rowCount()):
    #             #             word_table.cell(row, 0).text = cls_ttbl.varticalHeaderItem(row).text()
    #             #             for col in range(cls_ttbl.columnCount()):
    #             #                 word_table.cell(0, col).text = cls_ttbl.horizontalHeaderItem(col).text()
                        
    #             #         for row in range(1, cls_ttbl.rowCount() + 1):
    #             #             for col in range(1, cls_ttbl.columnCount() + 1):
    #             #                 item = cls_ttbl.item(row - 1, col - 1)
    #             #                 word_table.cell(row, col).text = "" if item.break_time or item.free_period else item.text()
                        
    #             #         for r, row in enumerate(word_table.rows):
    #             #             for c, cell in enumerate(row.cells):
    #             #                 item = cls_ttbl.item(r, c)
                                
    #             #                 self._set_cell_bg(cell, "000000" if not r or not c else ("1F1F1F" if item.break_time else "FFFFFF"))

    #             #     doc.save(path)
    #             # elif path.endswith("xlsx"):
    #             #     wb = Workbook()
    #             #     ws = wb.active
    #             #     ws.title = title
                    
    #             #     bg_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
    #             #     general_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    #             #     break_fill = PatternFill(start_color="1F1F1F", end_color="1F1F1F", fill_type="solid")
                    
    #             #     for cls_ttbl in widgets:
    #             #         # Add header row
    #             #         headers = [cls_ttbl.horizontalHeaderItem(col).text() for col in range(cls_ttbl.columnCount())]
    #             #         ws.append(headers)
                        
    #             #         for row in range(cls_ttbl.rowCount()):
    #             #             row_data = [cls_ttbl.verticalHeaderItem(row).text()]
    #             #             for col in range(cls_ttbl.columnCount()):
    #             #                 item = cls_ttbl.item(row, col)
                                
    #             #                 row_data.append("" if item.break_time or item.free_period else item.text())
    #             #             ws.append(row_data)
                        
    #             #         for r, row in enumerate(ws.iter_rows()):
    #             #             for c, cell in enumerate(row):
    #             #                 item = cls_ttbl.item(r, c)
                                
    #             #                 cell.fill = break_fill if item.break_time else (bg_fill if not r or not c else general_fill)
                    
    #             #     wb.save(path)
    #             else:
    #                 pixmap = QPixmap(widget.size())
    #                 widget.render(pixmap)
    #                 pixmap.save(path)
    #     elif export_mode == 1:
    #         pass
    
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
            
            self.option_button_func(self.view_tracker[self.go_focus_index])
        
        if self.go_focus_index == 0:
            self.go_back_action.setDisabled(True)
            self.title_bar.go_back_button.setDisabled(True)
    
    def go_forward(self):
        if self.go_focus_index < len(self.view_tracker) - 1:
            self.go_focus_index += 1
            
            self.go_back_action.setDisabled(False)
            self.title_bar.go_back_button.setDisabled(False)
            
            self.option_button_func(self.view_tracker[self.go_focus_index])
        
        if self.go_focus_index == len(self.view_tracker) - 1:
            self.go_forward_action.setDisabled(True)
            self.title_bar.go_forward_button.setDisabled(True)
    
    def create_menu_bar(self):
        menubar = QMenuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        go_menu = menubar.addMenu("Go")
        palette_menu = menubar.addMenu("Palette")
        help_menu = menubar.addMenu("Help")
        
        # Export Menu
        # export_menu = QMenu("Export", self)
        
        # export_menu.addAction("Single", lambda: self.file.export(0, self.export_file_filter))
        # export_menu.addAction("Batch", lambda: self.file.export(1, self.export_file_filter))
        
        # Add all actions
        file_menu.addAction("New", "Ctrl+N", self.file.new)
        file_menu.addSeparator()
        file_menu.addAction("Open", "Ctrl+O", self.file.open)
        file_menu.addSeparator()
        file_menu.addAction("Save", "Ctrl+S", self.file.save)
        file_menu.addAction("Save As", "Ctrl+Shift+S", self.file.save_as)
        # file_menu.addMenu(export_menu)
        file_menu.addSeparator()
        file_menu.addAction("Close", self.close)
        
        # Add Edit Actions
        edit_menu.addAction("Redo", "Ctrl+Y", self.redo)
        edit_menu.addAction("Undo", "Ctrl+Z", self.undo)
        edit_menu.addSeparator()
        edit_menu.addAction("Cut", "Ctrl+X")
        edit_menu.addAction("Copy", "Ctrl+C")
        edit_menu.addAction("Paste", "Ctrl+V")
        edit_menu.addSeparator()
        edit_menu.addAction("Find", "Ctrl+F")
        
        self.go_back_action = go_menu.addAction("Back", self.go_back)
        self.go_forward_action = go_menu.addAction("Forward", self.go_forward)
        go_menu.addSeparator()
        go_menu.addAction("Go to ID")
        go_menu.addSeparator()
        go_menu.addAction("Go to Subject")
        go_menu.addAction("Go to Teacher")
        go_menu.addAction("Go to Class")
        
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
        
        help_menu.addAction("Welcome")
        help_menu.addSeparator()
        help_menu.addAction("Documentation")
        help_menu.addAction("View License")
        help_menu.addSeparator()
        help_menu.addAction("Check Updates")
        help_menu.addSeparator()
        help_menu.addAction("About")
        
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
                self.title_bar.search_pb.setText(f"Search {name}")
                
                self.view_tracker[self.go_focus_index + 1:] = []
                self.go_focus_index += 1
                
                self.view_tracker.append(index)
                
                self.go_back_action.setDisabled(False)
                self.title_bar.go_back_button.setDisabled(False)
                
                self.go_forward_action.setDisabled(True)
                self.title_bar.go_forward_button.setDisabled(True)
            
            self.option_button_func(index)
        
        return func
    
    def make_palette_action_func(self, main_color: str, accent_color: str):
        def palette_action_func():
            SCHOOL.settings.THEME = f"{main_color}-{accent_color}"
            THEME_MANAGER.apply_theme(SCHOOL.settings.THEME)
        
        return palette_action_func
    
    def option_button_func(self, index: int):
        for i, btn in enumerate(self.option_buttons):
            btn.setChecked(i == index)
        
        if self.display_index != index:
            self.stack.setCurrentIndex(index)
        
        self.display_index = index


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon("src/images/logo.ico"))
    
    THEME_MANAGER.set_application(app)
    
    window = Window(app.arguments())
    window.showMaximized()
    
    sys.exit(app.exec())
    
