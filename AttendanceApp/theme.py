
from imports import *

stylesheet = '''
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
        color: {text};
        background-color: {mute-bg};
        border-bottom: 1px solid {border};
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 8px 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {hover__mute-bg};
    }}
    QMenu {{
        color: {text};
        padding: 5px;
        background-color: {bg2};
        border: 1px solid {border};
        border-radius: 5px;
    }}
    QMenu::item {{
        border-radius: 4px;
        padding: 5px 20px;
        margin: 1px 3px;
    }}
    QMenu::item:selected {{
        color: {primary_text};
        background-color: {primary_pressed};
    }}
    QMenu::item:disabled {{
        color: #888;
        background-color: transparent;
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
    
    .option-menu {{
        background-color: {input_bg};
        color: {primary_text};
        border: 1px solid {border};
        padding: 0px
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
    
    .labeled-widget {{
        border-radius: 6px;
        border: 1px solid {border};
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
'''

PALETTES = {
    "general-palette": {
        "title_text_teacher": "#a6a6a6",
        "title_text_prefect": "#a6a6a6",
        
        "border_teacher": "#a6a6a6",
        "border_prefect": "#a6a6a6",

        "text_teacher": "#ffffff",
        "text_prefect": "#ffffff"
    },

    "main-palette":{
        "dark": {
            "bg": "#1e1e1e",
            "bg2": "#2a2a2a",
            "bg3": "#4b4b4b",
            "text": "#f0f0f0",
            "mute-bg": "#404040",
            "secondary": "#3a3a3d",
            "border": "#B6B6B6",
            "input_bg": "#2d2d30",
            "input_border": "#555",
            "scrollbar": "#555",
            "tooltip_bg": "#333",
            "tooltip_text": "#eee",
            "disabled": "#777777",
            "hover2": "#353536",
            "hover3": "#47474b"
        },
        
        "light":{
            "bg": "#ffffff",
            "bg2": "#ddd",
            "bg3": "#b8b8b8",
            "text": "#1a1a1a",
            "mute-bg": "#bfbfbf",
            "secondary": "#f0f0f0",
            "border": "#ccc",
            "input_bg": "#ffffff",
            "input_border": "#bbb",
            "scrollbar": "#999",
            "tooltip_bg": "#fefefe",
            "tooltip_text": "#111",
            "disabled": "#aaaaaa",
            "hover2": "#c1c1c1",
            "hover3": "#8f8f8f"
        },
        
        "red": {
            "bg": "#3f0000",
            "bg2": "#610000",
            "bg3": "#5f0000",
            "text": "#f0f0f0",
            "mute-bg": "#150000",
            "secondary": "#7e0000",
            "border": "#444",
            "input_bg": "#300000",
            "input_border": "#555",
            "scrollbar": "#555",
            "tooltip_bg": "#333",
            "tooltip_text": "#eee",
            "disabled": "#777777",
            "hover2": "#612121",
            "hover3": "#490101"
        },

        "green": {
            "bg": "#001b01",
            "bg2": "#023d00",
            "bg3": "#004910",
            "text": "#f0f0f0",
            "mute-bg": "#001500",
            "secondary": "#00660e",
            "border": "#444",
            "input_bg": "#003008",
            "input_border": "#555",
            "scrollbar": "#555",
            "tooltip_bg": "#333",
            "tooltip_text": "#eee",
            "disabled": "#777777",
            "hover2": "#236121",
            "hover3": "#014907"
        },

        "darkblue": {
            "bg": "#02001b",
            "bg2": "#01003d",
            "bg3": "#050049",
            "text": "#f0f0f0",
            "mute-bg": "#0a001f",
            "secondary": "#020066",
            "border": "#444",
            "input_bg": "#030030",
            "input_border": "#555",
            "scrollbar": "#555",
            "tooltip_bg": "#333",
            "tooltip_text": "#eee",
            "disabled": "#777777",
            "hover2": "#252161",
            "hover3": "#060149"
        }
    },

    "accent-palette": {
        "blue": {
            "primary_text": "#ffffff",
            "primary": "#32a6ff",
            "primary_hover": "#5db5fd",
            "primary_pressed": "#1a9cff",
            "highlight": "#a3d6ff",
            
            "teacher": "#002358",
            "prefect": "#010025"
        },

        "green": {
            "primary_text": "#f0f0f0",
            "primary": "#0e9c15",
            "primary_hover": "#17bb11",
            "primary_pressed": "#15810b",
            "highlight": "#00cc00",
            
            "teacher": "#008100",
            "prefect": "#002506"
        },

        "red": {
            "primary_text": "#f0f0f0",
            "primary": "#9c0e0e",
            "primary_hover": "#bb1111",
            "primary_pressed": "#810b0b",
            "highlight": "#cc0000",
            
            "teacher": "#810000",
            "prefect": "#250000"
        }
    }
}


class AttendanceThemeManager:
    def __init__(self):
        self.themes: dict[str, dict[str, dict[str, str] | str]] = {}
        
        self.current_pallete = None
        self.current_theme = None
        
        self.widget = None
        
        self._name = None
        self._load_themes()
        
        self.func_mappings: dict[str, Callable[[str, tuple[Any, ...]], str]] = {
            "hover": self.get_hover_color,
            "pressed": self.get_pressed_color,
            "disabled": self.get_disabled_color,
            "interpolate": self.interpolate_brightness
        }
    
    @staticmethod
    def hex_to_rgb(hex_color: str, brightness: int = 1) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        
        assert len(hex_color) == 6, f"Invalid color value: {"#" + hex_color}"
        
        brightness = brightness / 255
        
        assert 1 > brightness >= 0, f"Invalid brightness value: {int(brightness * 255)}"
        
        r = int(int(hex_color[0:2], 16) * brightness)
        g = int(int(hex_color[2:4], 16) * brightness)
        b = int(int(hex_color[4:6], 16) * brightness)
        
        return (r, g, b, 255)
    
    @staticmethod
    def rgb_to_hex(rgb_color: tuple[int | float, int | float, int | float]) -> str:
        color = "#"
        for index, num in enumerate(rgb_color):
            num = int(num)
            
            if index < 3:
                pass
            elif num == 255:
                continue
            
            if len(hex(num).lstrip("0x")) == 0:
                color += "00"
            elif len(hex(num).lstrip("0x")) == 1:
                color += "0"
            color += hex(num).lstrip("0x")
        
        return color
    
    @staticmethod
    def interpolate_brightness(color: str, brightness: int | str):
        brightness = int(brightness)
        return AttendanceThemeManager.rgb_to_hex(AttendanceThemeManager.hex_to_rgb(color, brightness) if color is not None else (255, 255, 255, 255 - brightness))
    
    @staticmethod
    def get_disabled_color(color: str | None) -> str:
        return AttendanceThemeManager.interpolate_brightness(color, 100)
    
    @staticmethod
    def get_hover_color(color: str | None) -> str:
        return AttendanceThemeManager.interpolate_brightness(color, 200)
    
    @staticmethod
    def get_pressed_color(color: str | None) -> str:
        return AttendanceThemeManager.interpolate_brightness(color, 150)
    
    def _process_stylesheet_func_pointers(self, delimeter: str, stylesheet: str, palette: dict[str, str]):
        index = 0
        
        replacements = {}
        
        for _ in range(stylesheet.count(delimeter)):
            index = stylesheet.find(delimeter, index + 1, -1)
            
            start_index = stylesheet.rfind("{", 0, index)
            end_index = stylesheet.find("}", index, -1)
            
            text = stylesheet[start_index + 1: end_index]
            stripped_text = text.strip()
            
            function_key, palette_key = stripped_text.split(delimeter)
            
            if "-" in function_key:
                function_key, *extra_function_params = function_key.split("-")
            else:
                extra_function_params = []
            
            replacements["{" + text + "}"] = str(self.func_mappings[function_key](palette[palette_key], *extra_function_params))
        
        for init_text, rep_text in replacements.items():
            stylesheet = stylesheet.replace(init_text, rep_text)
        
        return stylesheet
    
    def process_stylesheet(self, stylesheet: str):
        assert isinstance(self.current_pallete, dict)
        
        return self._process_stylesheet_func_pointers("__", stylesheet, self.current_pallete).format(**self.current_pallete)
    
    def _add_theme(self, name: str, theme_dict: dict):
        """Add a theme directly from a dict"""
        self.themes[name] = theme_dict
    
    def _load_themes(self):
        general = PALETTES["general-palette"]
        
        for name1, theme_palette in PALETTES["main-palette"].items():
            for name2, color_palette in PALETTES["accent-palette"].items():
                palette = theme_palette.copy()
                
                palette.update(color_palette)
                palette.update(general)
                
                self._add_theme(f"{name1}-{name2}", {"palette": palette, "stylesheet": stylesheet})

    def set_widget(self, widget: QWidget):
        self.widget = widget
    
    def apply_theme(self, name: str):
        """Apply a stylesheet-only theme using values from JSON"""
        
        assert self.widget is not None, "No app to apply theme to"
        assert name in self.themes, f"Theme '{name}' not loaded."
        
        theme = self.themes[name]
        self.current_theme = name

        self.current_pallete = theme["palette"]
        
        self.current_pallete = theme["palette"]
        
        # Inject palette variables into stylesheet using string formatting
        try:
            error = None
            stylesheet = self.process_stylesheet(theme["stylesheet"])
        except KeyError as e:
            error = e
        
        if error:
            raise KeyError(f"Missing color value for: {error} on line {next(i + 1 for i, l in enumerate(theme["stylesheet"].splitlines()) if str(error).replace("'", "") in l)}")
        
        self.widget.setStyleSheet(stylesheet)

    def get_current_theme(self):
        theme: dict[str, dict[str, str] | str] = self.themes.get(self.current_theme, None)
        
        return theme
    
    def get_theme_names(self):
        return list(self.themes.keys())
    
    def pallete_get(self, name: str):
        return self.current_pallete[name]

