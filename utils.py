import pygame

from imports import *


TABLE_EXTENSION_TYPE = "(*.ttbl)"
TEMPLATE_EXTENSION_TYPE = "(*.template)"

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
    def __init__(self, parent: QWidget, path: Optional[str], file_filter: str):
        self.path = path
        self.parent = parent
        self.file_filter = file_filter
        self._from_save = False

    def set_callbacks(self, save: Optional[Callable[[str, str], str]], open_: Optional[Callable[[str, str], None] | Callable[[str, Any], None]], load: Optional[Callable[[str, str], Any]]):
        self.save_callback = save
        self.open_callback = open_
        self.load_callback = load
    
    def get_data(self, file_type: str):
        if self.path:
            return self.load_callback(self.path, file_type)
    
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

    def export(self, export_mode: int, file_type: str, file_filter: str):
        if export_mode == 0:
            file_path, _ = QFileDialog.getSaveFileName(self.parent, "Export File", "", file_filter)
        elif export_mode == 1:
            file_path = QFileDialog.getExistingDirectory(self.parent, "Batch Export Folder", "")
        else:
            raise Exception("Invalid Export Mode")
        
        if file_path:
            try:
                if self.export_callback:
                    self.export_callback(file_path, file_type, export_mode)
            except Exception as e:
                QMessageBox.critical(self.parent, type(e).__name__, str(e))


TTBL_X_MARGIN = 100
TTBL_Y_MARGIN = 200
SPACING = 50

TTBL_EXPORT_CELL_WIDTH = 170
TTBL_EXPORT_FONT_HEIGHT = 100
BG_TTBL_TITLE_EXPORT_FONT_HEIGHT = TTBL_EXPORT_FONT_HEIGHT * 1.5

TITLE_FONT = pygame.font.SysFont("Sans Serif", 200, True)
TTBL_FONT = pygame.font.SysFont("Sans Serif", TTBL_EXPORT_FONT_HEIGHT)
BREAK_TEXT_FONT = pygame.font.SysFont("Sans Serif", 210)

def get_export_surface(cls: Class):
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
    width = _max_length * TTBL_EXPORT_FONT_HEIGHT / 1.5
    
    ttbl_width = title_width + width * max(len(p) for p in timetable.values())
    ttbl_height = BG_TTBL_TITLE_EXPORT_FONT_HEIGHT * len(timetable)
    
    x1 = TTBL_X_MARGIN / 2
    y1 = TTBL_Y_MARGIN / 2
    
    cls_title_surf = TITLE_FONT.render(f"{cls.level.name.full()} {cls.name}", True, "black")
    cls_title_rect = cls_title_surf.get_rect(center=(ttbl_width / 2, y1))
    
    y2 = cls_title_rect.bottom + SPACING
    
    screen = pygame.Surface((ttbl_width + TTBL_X_MARGIN, ttbl_height + TTBL_Y_MARGIN + SPACING + cls_title_rect.height))
    screen.fill("white")
    
    screen.blit(cls_title_surf, cls_title_rect)
    
    for col, (day, periods) in enumerate(timetable.items()):
        ttbl_title_surf = TTBL_FONT.render(day, True, "white")
        ttbl_title_rect = pygame.Rect(x1, y2 + col * BG_TTBL_TITLE_EXPORT_FONT_HEIGHT, title_width, BG_TTBL_TITLE_EXPORT_FONT_HEIGHT)
        
        pygame.draw.rect(screen, "black", ttbl_title_rect)
        screen.blit(ttbl_title_surf, ((ttbl_title_rect.centerx - ttbl_title_surf.get_width() / 2, ttbl_title_rect.centery - ttbl_title_surf.get_height() / 2), ttbl_title_rect.size))
        
        if col == 0:
            pygame.draw.line(screen, "black", ttbl_title_rect.topleft, (ttbl_title_rect.x + ttbl_width, ttbl_title_rect.top), 3)
        
        pygame.draw.line(screen, "black", ttbl_title_rect.bottomleft, (ttbl_title_rect.x + ttbl_width, ttbl_title_rect.bottom), 3)
        
        for row, subject in enumerate(periods):
            ttbl_subject_rect = pygame.Rect(ttbl_title_rect.right + row * width, ttbl_title_rect.y, width, ttbl_title_rect.height)
            
            if subject.id == BreakPeriod.id:
                pygame.draw.rect(screen, "black", ttbl_subject_rect)
            else:
                if subject.id != FreePeriod.id:
                    ttbl_subject_surf = TTBL_FONT.render(subject.name.short(), True, "black")
                    
                    screen.blit(ttbl_subject_surf, ((ttbl_subject_rect.centerx - ttbl_subject_surf.get_width() / 2, ttbl_subject_rect.centery - ttbl_subject_surf.get_height() / 2), ttbl_subject_rect.size))
                
                if row + 1 >= len(periods) or periods[row + 1].id != BreakPeriod.id:
                    pygame.draw.line(screen, "black", ttbl_subject_rect.topright, ttbl_subject_rect.bottomright, 3)
    
    if break_aligned_period is not None:
        break_text_surf = pygame.transform.rotate(BREAK_TEXT_FONT.render("BREAK", True, "white"), 90)
        break_text_rect = pygame.Rect(x1 + title_width + width * (break_aligned_period - 1), y2, width, BG_TTBL_TITLE_EXPORT_FONT_HEIGHT * len(timetable))
        
        screen.blit(break_text_surf, ((break_text_rect.centerx - break_text_surf.get_width() / 2, break_text_rect.centery - break_text_surf.get_height() / 2), break_text_rect.size))
    
    return screen


HTML_EXPORT_STYLE = """
    body {{
        font-family: Arial, sans-serif;
        padding: 20px;
        background: #f9f9f9;
    }}
    
    h2 {{
        text-align: left;
        margin-bottom: 20px;
    }}
    
    .timetable {{
        display: grid;
        grid-template-columns: 100px repeat(5, 1fr);
        border: 1px solid #ccc;
        margin-bottom: 100px;
    }}
    
    .cell {{
        border: 1px solid #ccc;
        padding: 15px;
        text-align: center;
    }}
    
    .header {{
        background: black;
        color: white;
        font-weight: bold;
    }}
    
    .break {{
        background: #1f1f1f;
        color: #1f1f1f;
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
    
    ttbl_text = f'<div class="cell"></div>'
    
    for day in timetable:
        ttbl_text += f'<div class="cell header">{day}</div>'
    
    for row in range(max(d for d, _ in cls.level.weekdays.values())):
        ttbl_text += f'<div class="cell header">Period {row + 1}</div>'
        
        for periods in timetable.values():
            subject = periods[row] if row < len(periods) else None
            
            ttbl_text += (
                f'<div class="cell break"></div>'
                if subject and subject.id == BreakPeriod.id else
                (
                    f'<div class="cell"></div>'
                    if subject is None or subject.id == FreePeriod.id else
                    f'<div class="cell">{subject.name.short()}</div>'
                )
            )
    
    return f"""
        <h2>{cls.level.name.full()} {cls.name}</h2>
        <div class="timetable">
            {ttbl_text}
        </div>
    """



