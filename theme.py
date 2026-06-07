

from imports import *


PALETTES = {
    "general-palette": {},

    "main-palette":{
        "dark": {
            "bg1": "#1e1e1e",
            "bg2": "#2a2a2a",
            "bg3": "#4b4b4b",
            "bg4": "#2d2d30",
            "bg5": "#404040",
            "text": "#f0f0f0",
            "border1": "#505050",
            "border2": "#353536",
            "secondary": "#3a3a3d",
            "hover": "#47474b",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777"
        },
        
        "light":{
            "bg1": "#ffffff",
            "bg2": "#d0d0d0",
            "bg3": "#b8b8b8",
            "bg4": "#ffffff",
            "bg5": "#c0c0c0",
            "text": "#1a1a1a",
            "border1": "#b0b0b0",
            "border2": "#c1c1c1",
            "secondary": "#f0f0f0",
            "hover": "#8f8f8f",
            "scrollbar": "#909090",
            "tooltip_bg": "#fefefe",
            "tooltip_text": "#101010",
            "disabled": "#aaaaaa"
        },
        
        "red": {
            "bg1": "#3f0000",
            "bg2": "#610000",
            "bg3": "#5f0000",
            "bg4": "#300000",
            "bg5": "#404040",
            "text": "#f0f0f0",
            "border1": "#505050",
            "border2": "#612121",
            "secondary": "#7e0000",
            "hover": "#490101",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777"
        },

        "green": {
            "bg1": "#001b01",
            "bg2": "#023d00",
            "bg3": "#004910",
            "bg4": "#003008",
            "bg5": "#404040",
            "text": "#f0f0f0",
            "border1": "#505050",
            "border2": "#236121",
            "secondary": "#00660e",
            "hover": "#014907",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777"
        },

        "lightblue": {
            "bg1": "#001b17",
            "bg2": "#003d3a",
            "bg3": "#004945",
            "bg4": "#002d30",
            "bg5": "#404040",
            "text": "#f0f0f0",
            "border1": "#505050",
            "border2": "#215f61",
            "secondary": "#006666",
            "hover": "#014945",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777"
        },

        "darkblue": {
            "bg1": "#02001b",
            "bg2": "#01003d",
            "bg3": "#050049",
            "bg4": "#030030",
            "bg5": "#404040",
            "text": "#f0f0f0",
            "border1": "#505050",
            "border2": "#252161",
            "secondary": "#020066",
            "hover": "#060149",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777"
        }
    },

    "accent-palette": {
        "blue": {
            "primary_text": "#ffffff",
            "primary_hover": "#5db5fd",
            "fg1": "#32a6ff",
            "fg2": "#1a9cff",
            "fg3": "#6eb4e9",
            "highlight": "#a3d6ff",
        },

        "green": {
            "primary_text": "#f0f0f0",
            "primary_hover": "#17bb11",
            "fg1": "#0e9c15",
            "fg2": "#15810b",
            "fg3": "#064900",
            "highlight": "#00cc00",
        },

        "red": {
            "primary_text": "#f0f0f0",
            "primary_hover": "#bb1111",
            "fg1": "#9c0e0e",
            "fg2": "#810b0b",
            "fg3": "#350000",
            "highlight": "#cc0000",
        }
    }
}

STYLESHEET = '''
    QWidget.Bordered {{
        border-radius: 9px;
        border: 1.5px solid {border2};
    }}
    
    
    QMainWindow {{
        background-color: {bg1};
    }}
    
    
    QWidget, QScrollArea {{
        background-color: {bg2};
        color: {text}; 
        border: none;
    }}
    
    QWidget {{
        background-color: {bg2};
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        margin: 0px;
    }}
    
    QScrollArea {{
        background-color: {bg2};
        border: 1px solid {border1};
        padding: 4px;
    }}
    
    
    QScrollBar::handle {{
        background: {bg4};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar:vertical, QScrollBar:horizontal {{
        border: none;
        background-color: {bg2};
        width: 14px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        min-height: 30px;
    }}
    QScrollBar::handle:horizontal {{
        min-width: 30px;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background-color: {bg3};
        border-radius: 7px;
    }}
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background-color: {hover__bg3};
    }}
    QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
        background-color: {pressed__bg3};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        border: none;
        background: none;
        width: 0px;
    }}
    
    QWidget.Sidebar {{
        background-color: none;
        border: 1px solid {text};
    }}
    QWidget.SubSidebar {{
        background-color: {bg1};
        border: none;
    }}
    QWidget.SubSidebar QPushButton {{
        text-align: left;
        padding: 12px 20px;
        border-radius: 0px;
        background-color: {bg1};
        color: {text};
        border-left: 0px solid {fg1};
    }}
    QWidget.SubSidebar QPushButton:hover {{
        background-color: {hover__bg1};
    }}
    QWidget.SubSidebar QPushButton:checked {{
        background-color: {pressed__bg1};
        border-left: 4px solid {fg2};
    }}
    
    
    
    QLabel {{
        color: {text};
    }}
    QLabel:disabled {{
        color: {disabled__text};
    }}
    QLabel.Link {{
        color: {fg1};
        font-weight: bold;
        text-decoration: underline;
    }}
    QLabel.Link:hover {{
        color: {hover__fg1};
    }}
    
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        color: {text};
        background-color: {bg4};
        border: 1px solid {border1};
        border-radius: 5px;
        padding: 5px;
    }}
    
    
    QSlider {{
        color: {fg1};
    }}
    
    
    QPushButton {{
        background-color: {fg1};
        color: {primary_text};
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 15px;
    }}
    QPushButton:hover {{
        background-color: {hover__fg1};
    }}
    QPushButton:disabled {{
        background-color: {disabled__fg1};
    }}
    
    
    QComboBox {{
        background-color: {bg3};
        color: {text};
        border: 1px solid {border2};
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
        background-color: {fg1};
        border-radius: 100%;
    }}
    QComboBox::down-arrow:hover {{
        background-color: {hover__fg1};
    }}
    QComboBox QAbstractItemView {{
        background-color: {bg1};
        border: 1px solid {border1};
        selection-background-color: {fg1};
        selection-color: {text};
    }}
    
    QCheckBox, QRadioButton {{
        spacing: 6px;
        background: none;
    }}
    
    
    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 4px;
    }}
    
    
    QToolTip {{
        background-color: {bg5};
        color: {text};
        border: 1px solid {border1};
        padding: 5px;
        border-radius: 3px;
    }}
    
    
    QTabWidget::pane {{
        border: 1px solid {border1};
    }}
    
    
    QTabBar::tab {{
        background: {fg2};
        color: {text};
        padding: 6px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {bg2};
        font-weight: bold;
    }}
    
    
    QMenuBar {{
        color: {text};
        background-color: {bg5};
        border-bottom: 1px solid {border1};
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 8px 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {hover__bg5};
    }}
    QMenu {{
        color: {text};
        padding: 5px;
        background-color: {bg2};
        border: 1px solid {border2};
        border-radius: 5px;
    }}
    QMenu::item {{
        border-radius: 4px;
        padding: 5px 20px;
        margin: 1px 3px;
    }}
    QMenu::item:selected {{
        color: {primary_text};
        background-color: {fg2};
    }}
    QMenu::item:disabled {{
        color: #888;
        background-color: transparent;
    }}
    
    
    
    QTableView {{
        background-color: {bg1};
        color: {text};
        gridline-color: {border2};
        selection-background-color: {fg2};
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
        border: 1px solid {bg4};
    }}
    QCheckBox::indicator:unchecked {{
        background-color: {bg1};
    }}
    QCheckBox::indicator:checked {{
        background-color: {fg1};
        border-color: {fg1};
    }}
    QCheckBox::indicator:hover {{
        border-color: {hover__fg1};
    }}
    
    
    QFrame.Seperators {{
        background-color: {fg1};
        border-radius: 8px;
    }}
    
    
    QLabel.Arrow {{
        color: {fg2};
        background: none;
        font-weight: bold;
    }}
    
    
    QWidget.TimetableWidget {{
        background-color: {bg5};
        border-radius: 8px;
    }}
    
    
    QWidget.DropdownCheckboxes {{
        background-color: {bg4};
        margin: 0px 8px 4px 8px;
        padding: 4px;
        border: 1px solid {border1};
        border-radius: 8px;
    }}
    QWidget.DPC_Header {{
        margin: 2px 4px;
        background-color: {bg4};
    }}
    QWidget.DPC_Header QLabel {{
        font-size: 20px;
        background-color: {bg4};
    }}
    QWidget.DPC_Header QLabel.Arrow {{
        font-size: 16px;
    }}
    QWidget.DPC_Header QLabel.Arrow:hover {{
        color: {hover__fg2};
    }}
    QWidget.DPC_Header QLabel.Arrow:disabled {{
        color: {disabled__fg2};
    }}
    QWidget.DPC_Header * QCheckbox {{
        background-color: {bg4};
    }}
    QWidget.DPC_Body QLabel {{
        font-size: 15px;
    }}
    
    
    QLabel.SidebarToggleButton {{
        background-color: {bg2};
    }}
    QLabel.SidebarToggleButton:hover {{
        background-color: {hover__bg2};
    }}
    QPushButton.Close {{
        background-color: transparent;
        color: {text};
        font-weight: bold;
        padding: 0px;
        min-width: 0px;
        min-height: 0px;
    }}
    QPushButton.Close:hover {{
        color: {fg1};
    }}
    
    
    QWidget.SelectedSelectionListEntry, QWidget.UnselectedSelectionListEntry  {{
        background-color: transparent;
        border-radius: 10px;
        border: none;
    }}
    QWidget.SelectedSelectionListEntry QLabel, QWidget.UnselectedSelectionListEntry QLabel {{
        color: {text};
        font-size: 25px;
        font-weight: bold;
        background: none;
    }}
    QWidget.SelectedSelectionListEntry {{
        background-color: green;
    }}
    QWidget.UnselectedSelectionListEntry {{
        background-color: red;
    }}
    QWidget.SelectedSelectionListEntry QPushButton, QWidget.UnselectedSelectionListEntry QPushButton {{
        font-size: 20px;
    }}
    QWidget.SelectedSelectionListEntry QPushButton:hover, QWidget.UnselectedSelectionListEntry QPushButton:hover {{
        color: #bbb;
    }}
    
    QWidget.SubjectClassViewEntry {{
        border-radius: 8px;
        background-color: {bg4};
    }}
    QWidget.SubjectClassViewEntry QLabel.SubjectClassViewEntryName {{
        font-size: 30px;
        font-weight: bold;
        background: none;
    }}
    QWidget.SubjectClassViewEntryEdits {{
        background: none;
    }}
    QWidget.SubjectClassViewEntryEdits QLineEdit {{
        min-width: 60px;
        background-color: {bg5};
        border: 1px solid {border2};
        border-radius: 10px;
        padding: 6px;
        color: {text};
    }}
    
    
    QWidget.OptionTag QPushButton.Close {{
        font-size: 16px;
        border-radius: 8px;
    }}
    QWidget.OptionTag {{
        background-color: {fg1};
        border-radius: 8px;
        margin: 2px;
        padding: 2px 4px;
        min-width: 120px;
    }}
    QWidget.OptionTag QLabel {{
        color: {primary_text};
        background-color: {fg1};
        font-size: 13px;
        border-radius: 8px;
        padding: 4px 8px;
    }}
    QLineEdit.OptionEdit {{
        color: {text};
        border: none;
        max-width: 100px;
        font-size: 13px;
        padding: 4px 8px;
        border-radius: 8px;
    }}
    
    QMessageBox {{
        background-color: white;
    }}
    QMessageBox * {{
        color: black;
        background-color: white;
    }}
    QMessageBox QPushButton {{
        color: black;
        border-radius: 0px;
        border: 1px solid grey;
        background-color: whitesmoke;
        padding: 0px;
        min-width: 80px;
    }}
    QMessageBox QPushButton:hover {{
        border: 1px solid #2c59d3;
        background-color: #eefbff;
    }}
    
    
    QWidget.SettingOptionEntry {{
        background-color: {bg3};
        border-radius: 8px;
    }}
    QWidget.SettingOptionEntry QPushButton.Close {{
        font-size: 30px;
        border-radius: 15px;
    }}
    QWidget.SettingOptionEntry QLineEdit {{
        background-color: {bg4};
        color: {text};
        border: 1px solid {border1};
        padding: 8px;
        border-radius: 8px;
        font-size: 40px;
        margin: 4px 0px;
    }}
    
    
    QLabel.OptionSelectorNotSelected {{
        background-color: {bg4};
        border-radius: 8px;
        color: {text};
        padding: 8px;
        margin: 2px;
    }}
    QWidget.MainOptionSelector, QWidget.SubOptionSelector {{
        background-color: {bg3};
        border: none;
        border-radius: 10px;
    }}
    
    QWidget.OptionSelectorRow {{
        background: none;
    }}
    
    QTableWidget {{
        background-color: {bg4};
        border: none;
        border-radius: 8px;
        gridline-color: {border2};
    }}
    QHeaderView::section {{
        background-color: {bg4};
        color: {text};
        padding: 8px;
        border: none;
    }}
    QLabel.RemSubjectItem {{
        color: {text};
        background-color: {bg3};
        padding: 8px;
        border-radius: 4px;
        margin: 2px;
    }}
    QLabel.RemSubjectItem:hover {{
        background-color: {hover__bg3};
    }}
    
    
    .NoBackground {{
        background: none;
    }}
    
    
    QLabel.Title {{
        font-weight: bold;
        padding: 10px;
        background: none;
    }}
    
    QPushButton.Timetable_DP_OptionText {{
        color: {text};
        padding: 2px;
        min-width: 20px;
        font-weight: bold;
        background-color: transparent;
    }}
    QPushButton.Timetable_DP_OptionText:hover {{
        background-color: {hover__bg3};
    }}
    
    
    QWidget.TitleBar {{
        background-color: {bg1};
    }}
    QPushButton.FileClose, QPushButton.FileMinumum, QPushButton.FileMaximum {{
        color: {text};
        background-color: transparent;
        border: none;
        border-radius: 0px;
        min-width: 50px;
        min-height: 40px;
        padding: 0px;
        font-size: 20px;
    }}
    QPushButton.FileClose {{
        font-size: 15px;
    }}
    QPushButton.FileMinumum {{
        font-size: 10px;
    }}
    QPushButton.FileMinumum:hover, QPushButton.FileMaximum:hover {{
        background-color: {hover__bg3};
    }}
    QPushButton.FileClose:hover {{
        color: white;
        background-color: red;
    }}
    QPushButton.GoButton {{
        color: {text};
        padding: 0px;
        background-color: transparent;
        min-width: 30px;
        min-height: 30px;
        font-size: 20px;
        padding: 0px;
    }}
    QPushButton.GoButton:hover {{
        background-color: {bg3};
    }}
'''


class ThemeManager:
    def __init__(self):
        self.themes: dict[str, dict[str, dict[str, str] | str]] = {}
        
        self.current_pallete = None
        self.current_theme = None
        
        self.app = None
        
        self._name = None
        
        general = PALETTES["general-palette"]
        
        for name1, theme_palette in PALETTES["main-palette"].items():
            for name2, color_palette in PALETTES["accent-palette"].items():
                palette = deepcopy(theme_palette)
                palette.update(color_palette)
                palette.update(general)
                
                self._add_theme(f"{name1}-{name2}", {"palette": palette, "stylesheet": STYLESHEET})
        
        self.func_mappings = {
            "hover": self.get_hover_color,
            "pressed": self.get_pressed_color,
            "disabled": self.get_disabled_color
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
    def interpolate_brightness(color: str, brightness: int):
        return ThemeManager.rgb_to_hex(ThemeManager.hex_to_rgb(color, brightness) if color is not None else (255, 255, 255, 255 - brightness))
    
    @staticmethod
    def get_disabled_color(color: str | None) -> str:
        return ThemeManager.interpolate_brightness(color, 100)
    
    @staticmethod
    def get_hover_color(color: str | None) -> str:
        return ThemeManager.interpolate_brightness(color, 200)
    
    @staticmethod
    def get_pressed_color(color: str | None) -> str:
        return ThemeManager.interpolate_brightness(color, 150)
    
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
            
            replacements["{" + text + "}"] = str(self.func_mappings[function_key](palette[palette_key]))
        
        for init_text, rep_text in replacements.items():
            stylesheet = stylesheet.replace(init_text, rep_text)
        
        return stylesheet
    
    def _add_theme(self, name: str, theme_dict: dict):
        """Add a theme directly from a dict"""
        self.themes[name] = theme_dict
    
    def set_application(self, app: QApplication):
        self.app = app
    
    def apply_theme(self, name: str):
        """Apply a stylesheet-only theme using values from JSON"""
        
        assert self.app is not None, "No app to apply theme to"
        assert name in self.themes, f"Theme '{name}' not loaded."
        
        theme = self.themes[name]
        self.current_theme = name

        self.current_pallete = theme.get("palette")
        stylesheet_template = theme.get("stylesheet")

        # Inject palette variables into stylesheet using string formatting
        # try:
        #     error = None
            
        stylesheet_template = self._process_stylesheet_func_pointers("__", stylesheet_template, self.current_pallete)
        applied_stylesheet = stylesheet_template.format(**self.current_pallete)
        
        # except KeyError as e:
        #     error = e
        
        # if error:
        #     KeyError(f"Missing color value for: {error} on line {stylesheet_template[:stylesheet_template.find(str(error))].count("\n") + 1}")
        
        self.app.setStyleSheet(applied_stylesheet)

    def get_current_theme(self):
        theme: dict[str, dict[str, str] | str] = self.themes.get(self.current_theme, None)
        
        return theme
    
    def get_theme_names(self):
        return list(self.themes.keys())
    
    def pallete_get(self, name: str):
        return self.current_pallete[name]


THEME_MANAGER = ThemeManager()

