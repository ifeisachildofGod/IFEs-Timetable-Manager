

from imports import *


STYLESHEET = '''
    QWidget {{
        background-color: {bg};
        color: {text};
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        margin: 0px
    }}
    
    QLabel:disabled {{
        color: {disabled};
    }}
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {input_bg};
        color: {text};
        border: 1px solid {input_border};
        border-radius: 5px;
        padding: 5px;
    }}
    
    QSlider {{
        color: {primary};
    }}
    
    QPushButton, .QPushButton {{
        background-color: {primary};
        color: {primary_text};
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
    }}
    
    QPushButton:hover, .QPushButton:hover {{
        background-color: {primary_hover};
    }}

    QPushButton:pressed, .QPushButton:pressed {{
        background-color: {primary_pressed};
    }}
    
    QPushButton:disabled, .QPushButton:disabled {{
        background-color: {disabled};
    }}
    
    QPushButton.cancel {{
        background-color: transparent;
        font-size: 30px;
        border-radius: 15px;
        padding: 0px;
    }}
    QPushButton.cancel:hover {{
        color: {disabled};
    }}
    
    QPushButton.search-button {{
        color: {text};
        background-color: {bg2};
        border: 1px solid {border};
    }}
    QPushButton.search-button:hover {{
        color: {tooltip_text};
        background-color: {hover2};
        border: 1px solid {disabled};
    }}
    
    QComboBox {{
        background-color: {input_bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px;
        min-width: 120px;
    }}
    
    QComboBox::drop-down {{
        border: none;
        padding-right: 6px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border: none;
        width: 12px;
        height: 12px;
        background-color: {primary};
        border-radius: 100%;
    }}
    
    QComboBox::down-arrow:hover {{
        background-color: {primary_hover};
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {bg};
        border: 1px solid {border};
        selection-background-color: {primary};
        selection-color: {text};
    }}
    
    QCheckBox, QRadioButton {{
        spacing: 6px;
    }}
    
    QMenuBar {{
        color: {primary_text};
        background-color: {primary_pressed};
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 4px 10px;
    }}

    QMenuBar::item:selected {{
        background: {primary_hover};
    }}
    
    QMenu::item {{
        color: {text};
    }}
    
    QMenu::item:selected {{
        color: {primary_text};
    }}
    
    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle {{
        background: {scrollbar};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar:vertical, QScrollBar:horizontal {{
        border: none;
        background-color: {bg};
        width: 14px;
    }}
    QScrollBar::handle:vertical {{
        min-height: 30px;
    }}
    QScrollBar::handle:horizontal {{
        min-width: 30px;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background-color: {scrollbar};
        border-radius: 7px;
    }}
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background-color: {hover2};
    }}
    QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
        background-color: {hover3};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        border: none;
        background: none;
        width: 0px;
    }}
    

    QToolTip {{
        background-color: {tooltip_bg};
        color: {tooltip_text};
        border: 1px solid {border};
        padding: 5px;
        border-radius: 3px;
    }}

    QTabWidget::pane {{
        border: 1px solid {border};
    }}

    QTabBar::tab {{
        background: {secondary};
        color: {text};
        padding: 6px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}

    QTabBar::tab:selected {{
        background: {input_bg};
        font-weight: bold;
    }}
    
    QMenu, .option-menu {{
        background-color: {input_bg};
        color: {primary_text};
        border: 1px solid {border};
        padding: 0px
    }}
    
    QMenu::item:selected {{
        background-color: {primary_pressed};
    }}
    
    .option-menu QPushButton, .option-menu .QPushButton {{
        border-radius: 0px;
        margin: 0px;
        border: none;
        background-color: {input_bg};
    }}
    
    .option-menu QPushButton:hover, .option-menu .QPushButton:hover {{
        color: {primary_text};
        background-color: {primary};
    }}

    QTableView {{
        background-color: {bg};
        color: {text};
        gridline-color: {border};
        selection-background-color: {highlight};
    }}
    
    QPushButton.VerticalTab {{
        width: 100%;
        height: 50px;
        border-radius: 0px;
        border-right: 3px solid {bg2};
        background-color: {bg2};
        color: {text};
        margin: 0px;
    }}
    
    QPushButton.VerticalTab:hover {{
        border-right-color: {hover2};
        background-color: {hover2};
    }}
    
    QPushButton.VerticalTab:checked {{
        border-right-color: {primary};
        background-color: {secondary};
    }}
    
    QPushButton.VerticalTab:checked:hover {{
        background-color: {hover3};
    }}
    
    QPushButton.HorizontalTab {{
        width: 100%;
        height: 30px;
        border-top: 3px solid {bg2};
        background-color: {bg2};
        color: {text};
        border-radius: 0px;
        margin: 0px;
    }}
    
    QPushButton.HorizontalTab:hover {{
        border-top-color: {hover2};
        background-color: {hover2};
    }}
    
    QPushButton.HorizontalTab:checked {{
        border-top-color: {primary};
        background-color: {secondary};
    }}
    
    QPushButton.HorizontalTab:checked:hover {{
        background-color: {hover3};
    }}
    
    QCheckBox {{
        color: {text};
        spacing: 8px;
        padding: 4px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 1px solid {border};
    }}
    
    QCheckBox::indicator:unchecked {{
        background-color: {bg};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {primary};
        border-color: {primary};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {primary_hover};
    }}

    .labeled-container {{
        border: 2px solid {border};
        border-radius: 8px;
        /*background-color: #1e1e1e;*/
    }}
    .labeled-container:disabled {{
        border: 1px solid {disabled};
    }}
    
    .labeled-title {{
        font-size: 11px;
        font-weight: 500;
        padding: 0 4px;
    }}
    .labeled-title:disabled {{
        color: {disabled};
    }}
    
    .options-button {{
        font-size: 20px;
    }}
    
    QWidget.AttendanceTeacherEntryWidget * .labeled-container, QWidget.StaffListTeacherEntryWidget * .labeled-container {{
        border: 1px solid {border_teacher};
    }}
    
    QWidget.AttendancePrefectEntryWidget * .labeled-container, QWidget.StaffListPrefectEntryWidget * .labeled-container {{
        border: 1px solid {border_prefect};
    }}
    
    QWidget.AttendanceTeacherEntryWidget * .labeled-title, QWidget.StaffListTeacherEntryWidget * .labeled-title {{
        color: {text_teacher};
    }}
    
    QWidget.AttendancePrefectEntryWidget * .labeled-title, QWidget.StaffListPrefectEntryWidget * .labeled-title {{
        color: {text_prefect};
    }}
    
    QWidget.AttendanceTeacherEntryWidget *, QWidget.StaffListTeacherEntryWidget * {{
        background-color: {teacher};
    }}
    
    QWidget.AttendancePrefectEntryWidget *, QWidget.StaffListPrefectEntryWidget * {{
        background-color: {prefect};
        color: {text_prefect};
    }}
    
    QWidget.StaffListTeacherEntryWidget,
    QWidget.StaffListPrefectEntryWidget,
    QWidget.AttendanceTeacherEntryWidget,
    QWidget.AttendancePrefectEntryWidget
    {{
        border-radius: 25px;
        padding: 50px;
        border: 2px solid grey;
    }}
    
    QWidget.StaffListTeacherEntryWidget * QLabel,
    QWidget.AttendanceTeacherEntryWidget * QLabel
    {{
        color: {text_teacher};
        font-weight: bold;
    }}
    
    QWidget.StaffListPrefectEntryWidget * QLabel,
    QWidget.AttendancePrefectEntryWidget * QLabel
    {{
        color: {text_prefect};
        font-weight: bold;
    }}
    
    QWidget.StaffListTeacherEntryWidget * .labeled-title,
    QWidget.StaffListTeacherEntryWidget * .options-button,
    QWidget.AttendanceTeacherEntryWidget * .labeled-title,
    QWidget.AttendanceTeacherEntryWidget * .options-button
    {{
        color: {title_text_teacher};
    }}
    
    QWidget.StaffListPrefectEntryWidget * .labeled-title,
    QWidget.StaffListPrefectEntryWidget * .options-button,
    QWidget.AttendancePrefectEntryWidget * .labeled-title,
    QWidget.AttendancePrefectEntryWidget * .options-button
    {{
        color: {title_text_prefect};
    }}
    
    QWidget.AttendanceTeacherEntryWidget * .labeled-widget,
    QWidget.StaffListTeacherEntryWidget * .labeled-widget
    {{
        border: 1px solid {title_text_teacher};
    }}
    
    QWidget.AttendancePrefectEntryWidget * .labeled-widget,
    QWidget.StaffListPrefectEntryWidget * .labeled-widget
    {{
        border: 1px solid {title_text_prefect};
    }}
    
    .labeled-title {{
        font-size: 11px;
        padding: 0 4px;
        padding-bottom: 0px;
    }}
    
    .labeled-widget {{
        border-radius: 6px;
        border: 1px solid {border};
    }}

'''


class ThemeManager:
    def __init__(self):
        self.themes: dict[str, dict[str, dict[str, str] | str]] = {}
        
        self.current_pallete = None
        self.current_theme = None
        
        self.app = None
        
        self._name = None

    def _add_theme(self, name: str, theme_dict: dict):
        """Add a theme directly from a dict"""
        self.themes[name] = theme_dict
    
    def set_application(self, app: QApplication):
        self.app = app
    
    def load_theme_from_file(self, file_path: str):
        """Load theme from a JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Theme file not found: {file_path}")
        with open(file_path, 'r') as f:
            palettes = json.load(f)
            
            general = palettes["general-palette"]
            
            for name1, theme_palette in palettes["main-palette"].items():
                for name2, color_palette in palettes["accent-palette"].items():
                    palette = deepcopy(theme_palette)
                    palette.update(color_palette)
                    palette.update(general)
                    
                    self._add_theme(f"{name1}-{name2}", {"palette": palette, "stylesheet": STYLESHEET})

    def apply_theme(self, name: str):
        """Apply a stylesheet-only theme using values from JSON"""
        
        assert self.app is not None, "No app to apply theme to"
        assert name in self.themes, f"Theme '{name}' not loaded."
        
        theme = self.themes[name]
        self.current_theme = name

        self.current_pallete = theme.get("palette")
        stylesheet_template = theme.get("stylesheet")

        # Inject palette variables into stylesheet using string formatting
        try:
            error = None
            applied_stylesheet = stylesheet_template.format(**self.current_pallete)
        except KeyError as e:
            error = e
        
        if error:
            KeyError(f"Missing color value for: {error} on line {stylesheet_template[:stylesheet_template.find(str(error))].count("\n") + 1}")
        
        self.app.setStyleSheet(applied_stylesheet)

    def get_current_theme(self):
        theme: dict[str, dict[str, str] | str] = self.themes.get(self.current_theme, None)
        
        return theme
    
    def get_theme_names(self):
        return list(self.themes.keys())
    
    def pallete_get(self, name: str):
        return self.current_pallete[name]


THEME_MANAGER = ThemeManager()
THEME_MANAGER.load_theme_from_file("src/palette.json")

