

from imports import *


PALETTES = {
    "general-palette": {},

    "main-palette":{
        "dark": {
            "bg1": "#1e1e1e",
            "bg2": "#2a2a2a",
            "bg3": "#4b4b4b",
            "bg4": "#2c2c2c",
            "bg5": "#313131",
            "mute-bg": "#404040",
            "border1": "#505050",
            "bg6-border2": "#808080",
            "text": "#f0f0f0",
            "secondary": "#3a3a3a",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777",
            
            "maximum": "#000000",
            "minimum": "#ffffff",
            
            "e-border": "#292929",
        },
        
        "light":{
            "bg1": "#e1e1e1",
            "bg2": "#d5d5d5",
            "bg3": "#b4b4b4",
            "bg4": "#d3d3d3",
            "bg5": "#cfcfcf",
            "mute-bg": "#bfbfbf",
            "border1": "#afafaf",
            "bg6-border2": "#7e7e7e",
            "text": "#0f0f0f",
            "secondary": "#c5c5c5",
            "scrollbar": "#afafaf",
            "tooltip_bg": "#fefefe",
            "tooltip_text": "#cfcfcf",
            "disabled": "#888888",
            
            "maximum": "#ffffff",
            "minimum": "#000000",
            
            "e-border": "#d6d6d6",
        },
        
        "red": {
            "bg1": "#1e0000",
            "bg2": "#2a0000",
            "bg3": "#4b0000",
            "bg4": "#2c0000",
            "bg5": "#350000",
            "mute-bg": "#150000",
            "border1": "#505050",
            "bg6-border2": "#612121",
            "text": "#f0f0f0",
            "secondary": "#7e0000",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777",
            
            "maximum": "#ff0000",
            "minimum": "#ffffff",
            
            "e-border": "#d60000",
        },
        
        "green": {
            "bg1": "#001e00",
            "bg2": "#002a00",
            "bg3": "#004b00",
            "bg4": "#002c00",
            "bg5": "#004200",
            "mute-bg": "#001500",
            "border1": "#505050",
            "bg6-border2": "#236121",
            "text": "#f0f0f0",
            "secondary": "#00660e",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777",
            
            "maximum": "#00ff00",
            "minimum": "#ffffff",
            
            "e-border": "#00d600",
        },
        
        "darkblue": {
            "bg1": "#11001e",
            "bg2": "#11002a",
            "bg3": "#11004b",
            "bg4": "#11002c",
            "bg5": "#110031",
            "mute-bg": "#0a001f",
            "border1": "#505050",
            "bg6-border2": "#252161",
            "text": "#f0f0f0",
            "secondary": "#020066",
            "scrollbar": "#505050",
            "tooltip_bg": "#303030",
            "tooltip_text": "#e0e0e0",
            "disabled": "#777777",
            
            "maximum": "#110033",
            "minimum": "#ffffff",
            
            "e-border": "#110029",
        }
    },

    "accent-palette": {
        "blue": {
            "primary_text": "#ffffff",
            "primary_hover": "#5db5fd",
            "fg1": "#1171f7",
            "fg2": "#1a9cff",
            "fg3": "#6eb4e9",
            "fg4": "#1f7cff",
            "fg5": "#00589b",
            "highlight": "#a3d6ff",
        },

        "green": {
            "primary_text": "#f0f0f0",
            "primary_hover": "#17bb11",
            "fg1": "#0e9c15",
            "fg2": "#20b812",
            "fg3": "#5CD451",
            "fg4": "#25b917",
            "fg5": "#137c16",
            "highlight": "#00cc00",
        },

        "red": {
            "primary_text": "#f0f0f0",
            "primary_hover": "#bb1111",
            "fg1": "#9c0e0e",
            "fg2": "#810b0b",
            "fg3": "#350000",
            "fg4": "#ff0914",
            "fg5": "#f71117",
            "highlight": "#cc0000",
        }
    }
}

STYLESHEET = '''
    * {{
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        margin: 0px;
    }}
    
    QWidget.Bordered {{
        border: 1px solid {bg6-border2};
    }}
    
    QWidget.BorderRadiused {{
        border-radius: 9px;
    }}
    
    QMainWindow {{
        background-color: {bg1};
    }}
    
    QWidget.BaseWidget, QScrollArea {{
        background-color: {bg2};
        color: {text}; 
        border: none;
    }}
    
    QFrame.DPMenu {{
        border: 1px solid {bg6-border2};
    }}
    
    QScrollArea {{
        background-color: {bg2};
        border: 1px solid {border1};
        padding: 4px;
    }}
    
    
    QScrollBar::handle {{
        background: {scrollbar};
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
        background-color: {scrollbar};
        border-radius: 7px;
    }}
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background-color: {hover__scrollbar};
    }}
    QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
        background-color: {pressed__scrollbar};
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
    
    
    QWidget.LabeledContainer {{
        border: 2px solid {border1};
        border-radius: 8px;
    }}
    QWidget.LabeledContainer:disabled {{
        border: 1px solid {disabled};
    }}
    
    QLabel.LabeledContainerTitle {{
        color: {bg3};
        font-size: 11px;
        font-weight: 500;
        padding: 0 4px;
    }}
    QLabel.LabeledContainerTitle:disabled {{
        color: {disabled};
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
    QLabel.Link2 {{
        color: {text};
        text-decoration: underline;
        text-decoration-color: transparent;
        
    }}
    QLabel.Link2:hover {{
        color: {fg1};
        font-weight: bold;
        text-decoration-color: red;
    }}
    QLabel.StatusBarSeperator {{
        color: {pressed__text};
    }}
    
    QLineEdit, QTextEdit, QPlainTextEdit, QPushButton.SearchPB {{
        color: {text};
        background-color: {bg4};
        border: 1px solid {border1};
        border-radius: 5px;
        padding: 5px;
    }}
    
    QPushButton.SearchPB:hover {{
        background-color: {hover__bg4};
    }}
    QPushButton.SearchPB:disabled {{
        color: {disabled__text};
        background-color: {disabled__bg4};
    }}
    
    
    QSlider {{
        color: {fg1};
    }}
    
    QWidget.SearchOptions * {{
        background: none;
    }}
    
    QWidget.SearchOptions {{
        background-color: {hover__bg3};
        border: none;
        padding: 8px 16px;
        border-radius: 0px;
    }}
    QWidget.SearchOptions:hover {{
        background-color: {bg3};
    }}
    QWidget.SearchOptions:disabled {{
        background-color: {disabled__bg3};
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
        color: {disabled__text};
        background-color: {disabled__fg1};
    }}
    
    
    QComboBox {{
        background-color: {bg3};
        color: {text};
        border: 1px solid {bg6-border2};
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
        color: {text};
        background-color: {bg1};
        border: 1px solid {border1};
        selection-background-color: {fg1};
        selection-color: {text};
    }}
    
    QRadioButton {{
        color: {text};
        spacing: 8px;
        padding: 4px;
        background: none;
    }}
    QRadioButton::indicator {{
        width: 10px;
        height: 10px;
        border-radius: 6px;
        border: 2px solid {minimum};
    }}
    QRadioButton::indicator:unchecked {{
        background-color: {bg1};
    }}
    QRadioButton::indicator:checked {{
        background-color: {fg2};
    }}
    QRadioButton::indicator:hover {{
        border-color: {fg3};
    }}
    
    
    QToolTip {{
        background-color: {tooltip_bg};
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
        background-color: {mute-bg};
        border-bottom: 1px solid {border1};
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
        border: 1px solid {bg6-border2};
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
        gridline-color: {bg6-border2};
        selection-background-color: {fg2};
    }}
    
    
    QCheckBox {{
        color: {text};
        spacing: 8px;
        padding: 4px;
        background: none;
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
        background-color: {mute-bg};
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
    QPushButton.SettingEntryClose {{
        background-color: transparent;
        color: {text};
        font-weight: bold;
        padding: 0px;
        min-width: 0px;
        min-height: 0px;
    }}
    QPushButton.SettingEntryClose:hover {{
        color: {fg3};
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
    
    QWidget.NumberLineEdit {{
        background: none;
    }}
    
    QWidget.SubjectClassViewEntry {{
        border-radius: 8px;
        background-color: {bg5};
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
        background-color: {mute-bg};
        border: 1px solid {bg6-border2};
        border-radius: 10px;
        padding: 6px;
        color: {text};
    }}
    
    
    QWidget.OptionTag QPushButton.SettingEntryClose {{
        font-size: 16px;
        border-radius: 8px;
    }}
    QWidget.OptionTag {{
        background-color: {fg5};
        border-radius: 8px;
        margin: 2px;
        padding: 2px 4px;
        min-width: 120px;
    }}
    QWidget.OptionTag QLabel {{
        color: {primary_text};
        background-color: transparent;
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
    
    QWidget.SettingEntry {{
        background-color: {bg5};
        border-radius: 8px;
    }}
    QWidget.SettingEntry QWidget.BaseWidget {{
        background: none;
    }}
    QPushButton.SettingEntryClose {{
        font-size: 30px;
        border-radius: 15px;
    }}
    QWidget.SettingEntry QLineEdit {{
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
        gridline-color: {border1};
    }}
    QHeaderView::section {{
        background-color: {fg5};
        color: {primary_text};
        padding: 8px;
        gridline-color: {bg6-border2};
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
    
    
    QWidget.ExportEditorOptionsBG, QWidget.SC_Bordeless {{
        border: none;
    }}
    
    QLabel {{
        background: none;
    }}
    
    QSpinBox {{
        color: {text};
        background-color: {bg4};
        border: 1px solid {maximum};
    }}
    
    QColorDialog, QDialog, QWidget.ExportEditorSection {{
        background-color: {bg6-border2}
    }}
    
    QWidget.ExportEditorSideBar {{
        background-color: {bg5};
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
                palette = theme_palette.copy()
                
                palette.update(color_palette)
                palette.update(general)
                
                self._add_theme(f"{name1}-{name2}", {"palette": palette, "stylesheet": STYLESHEET})
        
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
        
        applied_stylesheet = self.process_stylesheet(stylesheet_template)
        
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

