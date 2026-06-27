import pygame

from imports import *

TABLE_EXTENSION_TYPE = "ttbl"
TEMPLATE_EXTENSION_TYPE = "template"

FT_MAPPING = {
    TABLE_EXTENSION_TYPE: "Timetable Files (*.ttbl)",
    TEMPLATE_EXTENSION_TYPE: "Template Files (*.template)"
}

pygame.init()

class Thread(QThread):
    crashed = pyqtSignal(Exception)
    
    def __init__(self, main_window: QMainWindow, func: Callable):
        super().__init__()
        self.setParent(None)
        
        self.main_window = main_window
        
        self.func = func is not None and func or (lambda: ())
        main_window.close = self._window_closed()
    
    def _window_closed(self):
        def window_closed_event(self):
            self.exit(0)
            super().close()
        
        return window_closed_event
    
    def run(self):
        try:
            self.func()
        except Exception as e:
            QMessageBox.critical(None, e.__class__.__name__, str(e))
            self.crashed.emit(e)
            self.exit(-1)

class FileManager:
    def __init__(self, parent: QWidget, export_parent: QWidget, path: Optional[str], file_filter: str):
        self.path = path
        self.parent = parent
        self.export_parent = export_parent
        self.file_filter = file_filter
        
        self._from_save = False

    def set_callbacks(self, save: Optional[Callable[[str, str], str]], open_: Optional[Callable[[str, str], None] | Callable[[str, Any], None]], export: Optional[Callable[[str], str]]):
        self.save_callback = save
        self.open_callback = open_
        self.export_callback = export
    
    def new(self):
        if self.open_callback:
            self.open_callback()
    
    def open(self):
        file_path, file_type = QFileDialog.getOpenFileName(self.parent, "Open File", "", self.file_filter)
        
        if file_path:
            try:
                if self.open_callback:
                    self.open_callback(file_path, file_type)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))

    def save(self):
        if self.path:
            # try:
                if self.save_callback:
                    self.save_callback(self.path)
            # except Exception as e:
            #     QMessageBox.critical(self.parent, type(e).__name__, str(e))
        else:
            self._from_save = True
            self.save_as()

    def save_as(self):
        file_path, file_type = QFileDialog.getSaveFileName(self.parent, ("Save File" if self._from_save else "Save File As"), "", self.file_filter)
        
        if file_path:
            try:
                if self.save_callback:
                    self.path = file_path
                    self.save_callback(self.path, file_type)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))
        
        if self._from_save:
            self._from_save = False

    def export(self, export_mode: int, file_filter: str):
        if export_mode == 0:
            file_path, _ = QFileDialog.getSaveFileName(self.export_parent, "Export", "", file_filter)
        elif export_mode == 1:
            file_path = QFileDialog.getExistingDirectory(self.export_parent, "Batch Export", "")
        else:
            raise Exception("Invalid Export Mode")
        
        if file_path:
            try:
                if self.export_callback:
                    self.export_callback(file_path)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))



def _get_text(font: pygame.font.Font, text: str, color: str, spacing: int):
    if text:
        orig_text_surf = font.render(text, True, color)
        
        surfs = [font.render(c, True, color) for c in text]
        
        width_w_spacing = sum(s.get_width() for s in surfs)
        orig_spacing = (orig_text_surf.get_width() - width_w_spacing) / (len(text) - 1)
        
        width = width_w_spacing + (spacing + orig_spacing) * (len(text) - 1)
        height = max(s.get_height() for s in surfs)
        
        text_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        x = 0
        for s in surfs:
            text_surf.blit(s, (x, 0))
            
            x += s.get_width() + spacing + orig_spacing
        
        return text_surf
    
    return font.render(text, True, color)

TTBL_X_MARGIN = 100
TTBL_Y_MARGIN = 200

TTBL_EXPORT_CELL_WIDTH = 170

def get_export_surface(cls: Class):
    BG_TTBL_TITLE_EXPORT_FONT_HEIGHT = SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.size * 1.5
    
    CLS_TITLE_FONT = pygame.font.SysFont(
        SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.family,
        SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.size,
        SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.bold,
        SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.italic
    )
    TTBL_CONTENT_FONT = pygame.font.SysFont(
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.family,
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.size,
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.bold,
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.italic
    )
    WEEKDAY_FONT = pygame.font.SysFont(
        SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.family,
        SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.size,
        SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.bold,
        SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.italic
    )
    BREAK_FONT = pygame.font.SysFont(
        SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.family,
        SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.size,
        SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.bold,
        SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.italic
    )
    
    _max_title_length = max(len(d) for d in SCHOOL.settings.TIMETABLE_weekdays)
    _max_length = max(len(s.name.short()) for _, s in SCHOOL.subjects)
    
    timetable, _ = SCHOOL.timetables_data[cls.id]
    
    for i, (_, b) in enumerate(cls.level.weekdays.values()):
        if i == 0:
            r_b = b
            break_aligned_period = b
        
        if r_b != b:
            break_aligned_period = None
            break
    
    title_width = _max_title_length * BG_TTBL_TITLE_EXPORT_FONT_HEIGHT / 2
    title_height = BG_TTBL_TITLE_EXPORT_FONT_HEIGHT
    width = _max_length * SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.size / 1.5
    height = BG_TTBL_TITLE_EXPORT_FONT_HEIGHT
    
    ttbl_width = title_width + width * max(len(p) for p in timetable.values())
    ttbl_height = BG_TTBL_TITLE_EXPORT_FONT_HEIGHT * len(timetable)
    
    x1 = TTBL_X_MARGIN / 2
    y1 = TTBL_Y_MARGIN / 2
    
    cls_title_surf = _get_text(CLS_TITLE_FONT, f"{cls.level.name.full()} {cls.name}", SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.color, SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.letter_spacing)
    
    k_params = {}
    match SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.text_alignment:
        case "Left":
            k_params["midleft"] = x1, y1
        case "Center":
            k_params["center"] = ttbl_width / 2, y1
        case "Right":
            k_params["midright"] = x1 + ttbl_width, y1
    
    cls_title_rect = cls_title_surf.get_rect(**k_params)
    
    y2 = cls_title_rect.bottom
    
    screen = pygame.Surface((ttbl_width + TTBL_X_MARGIN + cls_title_rect.height, ttbl_height + TTBL_Y_MARGIN + cls_title_rect.height))
    screen.fill(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_bg_color)
    
    screen.blit(cls_title_surf, cls_title_rect)
    
    # if SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.overline:
    #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.color, (cls_title_rect.left, cls_title_rect.top), (cls_title_rect.right, cls_title_rect.top), 2)
    # if SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.underline:
    #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.color, (cls_title_rect.left, cls_title_rect.bottom), (cls_title_rect.right, cls_title_rect.bottom), 2)
    
    _y = y2
    
    for col, (day, periods) in enumerate(timetable.items()):
        ttbl_weekday_text = _get_text(WEEKDAY_FONT, day, SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.color, SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.letter_spacing)
        ttbl_weekday_rect = pygame.Rect(x1, _y, title_width, title_height) ; _y += ttbl_weekday_rect.height
        
        match SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.text_alignment:
            case "Left":
                ttbl_t_x = ttbl_weekday_rect.left
            case "Center":
                ttbl_t_x = ttbl_weekday_rect.centerx - ttbl_weekday_text.get_width() / 2
            case "Right":
                ttbl_t_x = ttbl_weekday_rect.right - ttbl_weekday_text.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
        
        ttbl_t_y = ttbl_weekday_rect.centery - ttbl_weekday_text.get_height() / 2
        
        ttbl_title_text_rect = pygame.Rect((ttbl_t_x, ttbl_t_y), ttbl_weekday_rect.size)
        
        pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.weekday_bg_color, ttbl_weekday_rect)
        screen.blit(ttbl_weekday_text, ttbl_title_text_rect)
        
        # if SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.overline:
        #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.color, (ttbl_title_text_rect.left, ttbl_title_text_rect.top), (ttbl_title_text_rect.right, ttbl_title_text_rect.top), 2)
        # if SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.underline:
        #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.weekday_text_theme.color, (ttbl_title_text_rect.left, ttbl_title_text_rect.bottom), (ttbl_title_text_rect.right, ttbl_title_text_rect.bottom), 2)
        
        pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_weekday_rect.topleft, ttbl_weekday_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
        pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_weekday_rect.topleft, ttbl_weekday_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
        
        if col == len(timetable) - 1:
            pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_weekday_rect.bottomleft, ttbl_weekday_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
        
        _x = ttbl_weekday_rect.right
        for row, subject in enumerate(periods):
            ttbl_subject_rect = pygame.Rect(_x, ttbl_weekday_rect.y, width, height) ; _x += ttbl_subject_rect.width
            
            if subject.id == BreakPeriod.id:
                pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.break_bg_color, ttbl_subject_rect)
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color if col == 0 else SCHOOL.settings.EXPORT_timetable_export_theme.break_bg_color, ttbl_subject_rect.topleft, ttbl_subject_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
                
                if col == len(timetable) - 1:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.bottomleft, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
            else:
                ttbl_subject_text_surf = _get_text(TTBL_CONTENT_FONT, subject.name.short() if subject.id != FreePeriod.id else "", SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.color, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.letter_spacing)
                
                match SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.text_alignment:
                    case "Left":
                        ttbl_s_x = ttbl_subject_rect.left
                    case "Center":
                        ttbl_s_x = ttbl_subject_rect.centerx - ttbl_subject_text_surf.get_width() / 2
                    case "Right":
                        ttbl_s_x = ttbl_subject_rect.right - ttbl_subject_text_surf.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
                
                ttbl_s_y = ttbl_subject_rect.centery - ttbl_subject_text_surf.get_height() / 2
                
                ttbl_subject_text_rect = pygame.Rect(((ttbl_s_x + (SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness if (row != 0 and periods[row - 1].id == BreakPeriod.id) or row == 0 else 0), ttbl_s_y), ttbl_subject_rect.size))
                
                pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_cell_bg_color, ttbl_subject_rect)
                screen.blit(ttbl_subject_text_surf, ttbl_subject_text_rect)
                
                # if subject.id != FreePeriod.id:
                #     if SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.overline:
                #         pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.color, (ttbl_subject_text_rect.left, ttbl_subject_text_rect.top), (ttbl_subject_text_rect.right + ttbl_subject_text_surf.get_width(), ttbl_subject_text_rect.top), 2)
                #     if SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.underline:
                #         pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.color, (ttbl_subject_text_rect.left, ttbl_subject_text_rect.top + TTBL_CONTENT_FONT.get_height()), (ttbl_subject_text_rect.right + ttbl_subject_text_surf.get_width(), ttbl_subject_text_rect.top + TTBL_CONTENT_FONT.get_height()), 2)
                
                if row + 1 < len(periods) and periods[row + 1].id == BreakPeriod.id:
                    pass
                else:
                    _addition = 0 if row == len(periods) - 1 else -SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, (ttbl_subject_rect.right + _addition, ttbl_subject_rect.top), (ttbl_subject_rect.right + _addition, ttbl_subject_rect.bottom), SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topleft, ttbl_subject_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
                
                if col == len(timetable) - 1:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.bottomleft, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
    
    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, (ttbl_weekday_rect.right, y2), (ttbl_weekday_rect.right, ttbl_weekday_rect.bottom), SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
    
    if break_aligned_period is not None:
        _temp_rect = pygame.Rect(x1 + title_width + width * (break_aligned_period - 1), y2, width, BG_TTBL_TITLE_EXPORT_FONT_HEIGHT * len(timetable))
        
        break_text_surf = pygame.transform.rotate(_get_text(BREAK_FONT, "BREAK", SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.color, SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.letter_spacing), 90)
        
        match SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.text_alignment:
            case "Right":
                break_y = _temp_rect.top
            case "Center":
                break_y = _temp_rect.centery - break_text_surf.get_height() / 2
            case "Left":
                break_y = _temp_rect.bottom - break_text_surf.get_height() - SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness
        
        break_x = _temp_rect.centerx - break_text_surf.get_width() / 2
        
        break_text_rect = pygame.Rect((break_x, break_y), _temp_rect.size)
        screen.blit(break_text_surf, break_text_rect)
        
        # if SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.overline:
        #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.color, (break_text_rect.left, break_text_rect.top), (break_text_rect.left, break_text_rect.bottom), 2)
        # if SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.underline:
        #     pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.break_text_theme.color, (break_text_rect.right, break_text_rect.top), (break_text_rect.right, break_text_rect.bottom), 2)
    
    return screen


HTML_EXPORT_STYLE = """
    body {{
        background: {ttbl_bg_color};
    }}
    
    .timetable {{
        display: grid;
        grid-template-columns: 100px repeat({subject_count}, 1fr);
        border-top: calc({border_horizontal_width}px / 2) solid {border_color};
        border-bottom: calc({border_horizontal_width}px / 2) solid {border_color};
        border-left: calc({border_vertical_width}px / 2) solid {border_color};
        border-right: calc({border_vertical_width}px / 2) solid {border_color};
        margin-bottom: 100px;
    }}
    
    .cls_title {{
        {cls_title_font_style}
    }}
    
    .ttbl_content {{
        background-color: {ttbl_content_bg_color};
        border-top: calc({border_horizontal_width}px / 2) solid {border_color};
        border-bottom: calc({border_horizontal_width}px / 2) solid {border_color};
        border-left: calc({border_vertical_width}px / 2) solid {border_color};
        border-right: calc({border_vertical_width}px / 2) solid {border_color};
    }}
    .ttbl_content h3 {{
        {ttbl_content_font_style}
    }}
    
    .weekday {{
        background-color: {weekday_bg_color};
        border-top: calc({border_horizontal_width}px / 2) solid {border_color};
        border-bottom: calc({border_horizontal_width}px / 2) solid {border_color};
        border-left: calc({border_vertical_width}px / 2) solid {border_color};
        border-right: calc({border_vertical_width}px / 2) solid {border_color};
    }}
    .weekday h3 {{
        {weekday_text_font_style}
    }}
    
    .break {{
        background-color: {break_bg_color};
    }}
    .break h3 {{
        {break_text_font_style}
    }}
"""

HTML_TEXT = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{title}}</title>
        <style>
            {HTML_EXPORT_STYLE}
        </style>
    </head>
        <body>
            {{body}}
        </body>
    </html>
"""

def get_export_html_text(cls: Class):
    timetable, _ = SCHOOL.timetables_data[cls.id]
    
    ttbl_text = ""
    
    for day in cls.level.weekdays:
        ttbl_text += f'<div class="weekday"><h3>{day}</h3></div>'
        
        for subject in timetable[day]:
            ttbl_text += (
                f'<div class="break"><h3></h3></div>'
                if subject and subject.id == BreakPeriod.id else
                (f'<div class="ttbl_content"><h3>{"" if subject.id == FreePeriod.id else subject.name.short()}</h3></div>')
            )
        
        ttbl_text += "\n\t\t\t"
    
    return f"""
        <h2 class="cls_title">{cls.level.name.full()} {cls.name}</h2>
        <div class="timetable">
            {ttbl_text}
        </div>
    """


def write_export_csv(writer, cls: Class):
    writer.writerow(cls.level.weekdays)
    
    timetable, _ = SCHOOL.timetables_data[cls.id]
    
    for i in range(max(d for d, _ in cls.level.weekdays.values())):
        writer.writerow([timetable[day][i].name.short() for day in cls.level.weekdays])


