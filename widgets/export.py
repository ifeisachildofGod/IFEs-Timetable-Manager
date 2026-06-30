
import csv
from io import StringIO

from utils import *
from imports import *

from widgets.base import *
from widgets.user_interface import *

from PIL import Image as PILImage


class TextThemeEditor(IconToolBarOption):
    def __init__(self, text_theme: Optional[TextTheme] = None, cast_labels: Optional[list[QLabel]] = None):
        super().__init__()
        
        self.font_display_label = QLabel("Text")
        
        self.cast_labels = (cast_labels or []) + [self.font_display_label]
        
        for label in self.cast_labels:
            label.setStyleSheet("background: none;")
        
        self.initialize(self._getFontSection(), title=self.font_display_label)
        
        self.font_cb.currentTextChanged.connect(self._fontFamilyChanged)
        self.s_sb.valueChanged.connect(self._fontSizeChanged)
        self.ls_sb.valueChanged.connect(self._fontLetterSpacingChanged)
        self.o_slider.valueChanged.connect(lambda v: self.o_sb.setValue(v))
        self.o_sb.valueChanged.connect(lambda v: self.o_slider.setValue(v))
        self.o_sb.valueChanged.connect(self._fontOpacityChanged)
        self.b_cb.clicked.connect(self._fontWeightChanged)
        self.i_cb.clicked.connect(self._fontStyleChanged)
        self.ul_cb.clicked.connect(lambda s: self._fontLineStyleChanged(s, False))
        self.ol_cb.clicked.connect(lambda s: self._fontLineStyleChanged(False, s))
        self.c_cb.colorSelected.connect(self._fontColorChanged)
        
        if text_theme is not None:
            self.font_cb.setCurrentText(text_theme.family)
            self.s_sb.setValue(text_theme.size)
            self.ls_sb.setValue(text_theme.letter_spacing)
            self.o_slider.setValue(text_theme.opacity)
            self.o_sb.setValue(text_theme.opacity)
            self.b_cb.setChecked(text_theme.bold)
            self.i_cb.setChecked(text_theme.italic)
            self.ul_cb.setChecked(text_theme.underline)
            self.ol_cb.setChecked(text_theme.overline)
            self.c_cb.setColor(text_theme.color)
            self.ta_cb.setCurrentText(text_theme.text_alignment.title())
        
        self._fontFamilyChanged(self.font_cb.currentText())
        self._fontSizeChanged(self.s_sb.value())
        self._fontLetterSpacingChanged(self.ls_sb.value())
        self._fontWeightChanged(self.b_cb.isChecked())
        self._fontStyleChanged(self.i_cb.isChecked())
        self._fontOpacityChanged(self.o_sb.value())
        self._fontLineStyleChanged(self.ul_cb.isChecked(), self.ol_cb.isChecked())
        self._fontColorChanged(self.c_cb.currentColor())
        self._textAlignment(self.ta_cb.currentText())
    
    def text_theme(self):
        return TextTheme(
            self.font_cb.currentText(),
            
            self.s_sb.value(),
            self.b_cb.isChecked(),
            self.i_cb.isChecked(),
            
            self.c_cb.currentColor(),
            self.ls_sb.value(),
            self.o_sb.value(),
            self.ul_cb.isChecked(),
            self.ol_cb.isChecked(),
            self.ta_cb.currentText(),
            
            self.font_display_label.styleSheet()
        )
    
    def _fontFamilyChanged(self, font_family: str):
        for label in self.cast_labels:
            font = label.font()
            
            # label.setText(font_family)
            
            font.setFamily(font_family)
            self.setStyleProperty(label, "font-family", f"'{font_family}'")
    
    def _fontSizeChanged(self, size: int):
        for label in self.cast_labels:
            font = label.font()
            
            font.setPointSize(size)
            
            self.setStyleProperty(label, "font-size", f"{size}pt")
    
    def _fontOpacityChanged(self, opacity: int):
        for label in self.cast_labels:
            self.setStyleProperty(label, "opacity", str(opacity))
    
    def _fontWeightChanged(self, bold: bool):
        for label in self.cast_labels:
            font = label.font()
            
            font.setBold(bold)
            self.setStyleProperty(label, "font-weight", "bold" if bold else "normal")
    
    def _fontStyleChanged(self, italic: bool):
        for label in self.cast_labels:
            font = label.font()
            
            font.setItalic(italic)
            self.setStyleProperty(label, "font-style", "italic" if italic else "normal")
    
    def _fontLineStyleChanged(self, underline: bool, overline: bool):
        for label in self.cast_labels:
            font = label.font()
            
            font.setOverline(overline)
            font.setUnderline(underline)
            
            self.setStyleProperty(label, "text-decoration", "underline" if underline else ("overline" if overline else "none"))
            
            if underline:
                self.ol_cb.blockSignals(True)
                self.ol_cb.setChecked(False)
                self.ol_cb.blockSignals(False)
            elif overline:
                self.ul_cb.blockSignals(True)
                self.ul_cb.setChecked(False)
                self.ul_cb.blockSignals(False)
    
    def _fontColorChanged(self, color: str):
        for label in self.cast_labels:
            self.setStyleProperty(label, "color", color)
    
    def _fontLetterSpacingChanged(self, spacing: float):
        for label in self.cast_labels:
            font = label.font()
            
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
            self.setStyleProperty(label, "letter-spacing", f"{spacing}px")
    
    def _textAlignment(self, alignment: str):
        for label in self.cast_labels:
            self.setStyleProperty(label, "text-align", alignment.lower())
    
    def _getFontSection(self):
        font_section = BaseWidget()
        font_section.setProperty("class", "ExportEditorOptionsBG")
        
        # -----------------------------------------------------------------------------------------------------------
        
        f_widget = BaseWidget() ; f_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        self.font_cb = QFontComboBox()
        self.s_sb = QSpinBox() ; self.s_sb.setValue(self.font_display_label.font().pointSize()) ; self.s_sb.setMaximum(500)
        self.ls_sb = QSpinBox() ; self.ls_sb.setValue(int(self.font_display_label.font().letterSpacing()))
        self.c_cb = ColorComboBox("white")
        fs_widget = BaseWidget(QHBoxLayout) ; fs_widget.setContentsMargins(0, 5, 0, 5)
        fs_widget.addWidget(b_cb := QCheckBox("Bold"))
        fs_widget.addWidget(i_cb := QCheckBox("Italic"))
        uss_widget = BaseWidget(QHBoxLayout) ; uss_widget.setContentsMargins(0, 5, 0, 5)
        uss_widget.addWidget(ul_cb := QCheckBox("Underline"))
        uss_widget.addWidget(ol_cb := QCheckBox("Overline"))
        o_widget = BaseWidget(QHBoxLayout)
        o_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        o_widget.setContentsMargins(0, 0, 0, 0)
        o_widget.addWidget(o_slider := QSlider(Qt.Orientation.Horizontal)) ; o_slider.setMaximum(100) ; o_slider.setValue(100)
        o_widget.addWidget(o_sb := QSpinBox()) ; o_sb.setMaximum(100) ; o_sb.setValue(100)
        self.o_slider = o_slider
        self.o_sb = o_sb
        self.ul_cb = ul_cb
        self.ol_cb = ol_cb
        self.b_cb = b_cb
        self.i_cb = i_cb
        
        f_widget.addWidget(LabeledWidget("Font Name", self.font_cb))
        f_widget.addWidget(LabeledWidget("Size", self.s_sb))
        f_widget.addWidget(LabeledWidget("Letter Spacing", self.ls_sb))
        f_widget.addWidget(LabeledWidget("Color", self.c_cb))
        f_widget.addWidget(SeparatorLabel("Style"))
        f_widget.addWidget(fs_widget)
        f_widget.addWidget(uss_widget)
        f_widget.addWidget(LabeledWidget("Opacity", o_widget))
        
        # -----------------------------------------------------------------------------------------------------------
        
        a_widget = BaseWidget() ; a_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        
        self.ta_cb = QComboBox() ; self.ta_cb.addItems(["Left", "Center", "Right"])
        self.ta_cb.currentTextChanged.connect(self._textAlignment)
        
        a_widget.addWidget(LabeledWidget("Text Alignment", self.ta_cb))
        
        # -----------------------------------------------------------------------------------------------------------
        
        font_section.addWidget(SeparatorLabel("Font"))
        font_section.addWidget(f_widget)
        font_section.addWidget(SeparatorLabel("Alignment"))
        font_section.addWidget(a_widget)
        font_section.addStretch()
        
        return font_section

class ColorComboBox(IconToolBarOption):
    colorSelected = pyqtSignal(str)
    
    def __init__(self, color: QColor | str):
        super().__init__()
        
        color = QColor(color)
        
        wrapper_widget = BaseWidget(QHBoxLayout)
        wrapper_widget.setSpacing(5)
        wrapper_widget.setContentsMargins(0, 0, 0, 0)
        
        self.selected_color_display = QWidget()
        self.selected_color_display.setFixedSize(20, 20)
        
        self.selected_color_hex_label = QLabel()
        self.selected_color_hex_label.setStyleSheet("font-family: consolas; font-size: 15px;")
        
        wrapper_widget.addWidget(self.selected_color_display)
        wrapper_widget.addWidget(self.selected_color_hex_label)
        
        color_picker = QColorDialog()
        color_picker.currentColorChanged.connect(self.setColor)
        
        self._is_init = True
        self.setColor(color)
        self._is_init = False
        
        self.initialize(color_picker, title=wrapper_widget, font_size=10)
        
        wrapper_widget.getWidget().mousePressEvent = self._clicked
        self.getWidget().mousePressEvent = lambda _: None
        
        self.setContentsMargins(5, 5, 5, 5)
    
    def currentColor(self):
        return self._color
    
    def _colorToHex(self, color: QColor):
        r = hex(color.red()).replace("0x", "")
        g = hex(color.green()).replace("0x", "")
        b = hex(color.blue()).replace("0x", "")
        
        return f"#{"0" + r if len(r) == 1 else r}{"0" + g if len(g) == 1 else g}{"0" + b if len(b) == 1 else b}"
    
    def setColor(self, color: QColor | str):
        str_color = self._colorToHex(QColor(color))
        
        self.selected_color_hex_label.setText(str_color)
        self.selected_color_display.setStyleSheet(f"background-color: {str_color};")
        
        if not self._is_init:
            self.colorSelected.emit(str_color)
        
        self._color = str_color


class ExportPreviewDialog(BaseDialogWidget):
    def __init__(
        self,
        title_label: QLabel,
        p1_time_heading_label: QLabel,
        p2_time_heading_label: QLabel,
        p3_time_heading_label: QLabel,
        p4_time_heading_label: QLabel,
        p5_time_heading_label: QLabel,
        m_weekday_heading_label: QLabel,
        t_weekday_heading_label: QLabel,
        content_label: QLabel,
    ):
        super().__init__("Preview Export", BaseWidget)
        
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {"white"};")
        
        row1 = BaseWidget(QHBoxLayout) ; row1.setSpacing(0) ; row1.setContentsMargins(0, 0, 0, 0)
        row2 = BaseWidget(QHBoxLayout) ; row2.setSpacing(0) ; row2.setContentsMargins(0, 0, 0, 0)
        row3 = BaseWidget(QHBoxLayout) ; row3.setSpacing(0) ; row3.setContentsMargins(0, 0, 0, 0)
        
        row1.addWidget(self.getCell(QLabel(), "white"))
        row1.addWidget(self.getCell(p1_time_heading_label, "black"))
        row1.addWidget(self.getCell(p2_time_heading_label, "black"))
        row1.addWidget(self.getCell(p3_time_heading_label, "black"))
        row1.addWidget(self.getCell(p4_time_heading_label, "black"))
        row1.addWidget(self.getCell(p5_time_heading_label, "black"))
        
        row2.addWidget(self.getCell(m_weekday_heading_label, "black"))
        row2.addWidget(self.getCell(content_label, "white"))
        row2.addWidget(self.getCell(QLabel(), "white"))
        row2.addWidget(self.getCell(QLabel(), "grey"))
        row2.addWidget(self.getCell(QLabel(), "white"))
        row2.addWidget(self.getCell(QLabel(), "white"))
        
        row3.addWidget(self.getCell(t_weekday_heading_label, "black"))
        row3.addWidget(self.getCell(QLabel(), "white"))
        row3.addWidget(self.getCell(QLabel(), "white"))
        row3.addWidget(self.getCell(QLabel(), "grey"))
        row3.addWidget(self.getCell(QLabel(), "white"))
        row3.addWidget(self.getCell(QLabel(), "white"))
        
        self.addWidget(title_label)
        self.addWidget(row1)
        self.addWidget(row2)
        self.addWidget(row3)
    
    def getCell(self, label: QLabel, bg_color: str):
        w = BaseWidget()
        w.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        w.setStyleSheet(f"background-color: {bg_color}")
        
        w.addWidget(label)
        
        return w


class ExportsEditorDialogWidget(BaseDialogWidget):
    def __init__(self):
        super().__init__("Export Editor", BaseWidget)
    
    def _init(self, file_manager: FileManager):
        self.file_manager = file_manager
        
        self._initGeometry()
        
        self.setProperty("class", "ExportEditor")
        
        main_widget = BaseScrollWidget()
        main_widget.setProperty("class", "ExportEditorOptionsBG")
        
        e_widget = BaseWidget() ; e_widget.setContentsMargins(35, 0, 35, 0)
        et_widget = BaseWidget(QHBoxLayout) ; et_widget.setSpacing(50)
        et_widget.addWidget(s_rb := QRadioButton("School")) ; s_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        et_widget.addWidget(l_rb := QRadioButton("Level")) ; l_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        et_widget.addWidget(c_rb := QRadioButton("Class")) ; c_rb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        eft_widget = LabeledWidget("Export File Type", eft_cb := QComboBox()) ; eft_cb.addItems(["PNG", "JPG", "HTML", "CSV"])
        self.s_rb = s_rb ; self.s_rb.clicked.connect(lambda b: self._set_export_mode(0 if b else SCHOOL.settings.EXPORT_timetable_export_theme.export_mode))
        self.l_rb = l_rb ; self.l_rb.clicked.connect(lambda b: self._set_export_mode(1 if b else SCHOOL.settings.EXPORT_timetable_export_theme.export_mode))
        self.c_rb = c_rb ; self.c_rb.clicked.connect(lambda b: self._set_export_mode(2 if b else SCHOOL.settings.EXPORT_timetable_export_theme.export_mode))
        
        self.select_cb_dict: dict[ID, tuple[QCheckBox, dict[ID, QCheckBox]]] = {}
        
        e_bottom_widget = BaseWidget(QHBoxLayout)
        
        self.select_all_cb = QCheckBox("All")
        self.select_all_cb.clicked.connect(self._select_sch)
        
        self.sch_subject_selection_widget = BaseScrollWidget()
        self.sch_subject_selection_widget.getScrollWidget().setFixedHeight(300)
        self.sch_subject_selection_widget.addStretch()
        
        widget_dp = WidgetDropdown("Select Classes", self.sch_subject_selection_widget)
        widget_dp.header.addWidget(self.select_all_cb)
        
        for _, cls_level in SCHOOL.class_levels:
            self.sch_subject_selection_widget.insertWidget(len(self.sch_subject_selection_widget.getChildren()), self.get_level_widget(cls_level))
        
        e_bottom_widget.addWidget(widget_dp)
        e_bottom_widget.addStretch()
        e_bottom_widget.addWidget(eft_widget, alignment=Qt.AlignmentFlag.AlignTop)
        
        e_widget.addWidget(et_widget)
        e_widget.addWidget(e_bottom_widget)
        
        def csv_disable(text: str): 
            f_widget.setDisabled(text == "CSV")
            t_widget.setDisabled(text == "CSV")
            
            SCHOOL.settings.EXPORT_timetable_export_theme.export_file_type = text
        
        self.eft_cb = eft_cb
        self.eft_cb.currentTextChanged.connect(csv_disable)
        
        self.cls_title_text_theme = TextThemeEditor(SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme, t_labels := [QLabel("SS3 A")])
        self.ttbl_heading_text_theme = TextThemeEditor(
            SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme,
            p_labels := [
                QLabel("8:10 - 8:45"),
                QLabel("8:45 - 9:20"),
                QLabel("9:20 - 9:55"),
                QLabel("9:55 - 10:30"),
                QLabel("10:30 - 11:05"),
                QLabel("Monday"),
                QLabel("Tuesday"),
            ]
        )
        self.ttbl_content_text_theme = TextThemeEditor(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme, c_labels := [QLabel("Mathematics")])
        
        f_widget = BaseWidget() ; f_widget.setContentsMargins(35, 0, 35, 0)
        f_widget.addWidget(LabeledWidget("Class Title Text Theme", self.cls_title_text_theme))
        f_widget.addWidget(LabeledWidget("Timetable Heading Text Theme", self.ttbl_heading_text_theme))
        f_widget.addWidget(LabeledWidget("Timetable Content Text Theme", self.ttbl_content_text_theme))
        
        self.ttbl_bg_color = ColorComboBox(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_bg_color)
        self.ttbl_content_bg_color = ColorComboBox(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_bg_color)
        self.ttbl_heading_bg_color = ColorComboBox(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color)
        self.break_bg_color = ColorComboBox(SCHOOL.settings.EXPORT_timetable_export_theme.break_bg_color)
        self.border_color = ColorComboBox(SCHOOL.settings.EXPORT_timetable_export_theme.border_color)
        
        t_widget = BaseWidget() ; t_widget.setContentsMargins(35, 0, 35, 0)
        t_widget.addWidget(LabeledWidget("Timetable Background Color", self.ttbl_bg_color))
        t_widget.addWidget(LabeledWidget("Timetable Content Background Color", self.ttbl_content_bg_color))
        t_widget.addWidget(LabeledWidget("Timetabel Heading Background Color", self.ttbl_heading_bg_color))
        t_widget.addWidget(LabeledWidget("Break Background Color", self.break_bg_color))
        t_widget.addWidget(LabeledWidget("Border Color", self.border_color))
        thickness_widget = BaseWidget()
        thickness_widget.addWidget(t_l1_widg := LabeledWidget("  Vertical Line Thickness", vlt_sb := QSpinBox())) ; t_l1_widg.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        thickness_widget.addWidget(t_l2_widg := LabeledWidget("Horizontal Line Thickness", hlt_sb := QSpinBox())) ; t_l2_widg.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        t_widget.addWidget(thickness_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vlt_sb = vlt_sb ; self.vlt_sb.setMaximum(30) ; self.vlt_sb.setValue(SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
        self.hlt_sb = hlt_sb ; self.hlt_sb.setMaximum(30) ; self.hlt_sb.setValue(SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
        
        self.eft_cb.setCurrentText(SCHOOL.settings.EXPORT_timetable_export_theme.export_file_type)
        
        main_widget.addWidget(SeparatorLabel("Export"))
        main_widget.addWidget(e_widget)
        main_widget.addWidget(SeparatorLabel("Fonts"))
        main_widget.addWidget(f_widget)
        main_widget.addWidget(SeparatorLabel("Table"))
        main_widget.addWidget(t_widget)
        
        base_widget = BaseWidget(QHBoxLayout)
        
        export_dialog = ExportPreviewDialog(*(t_labels + p_labels + c_labels))
        
        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(lambda: export_dialog.exec())
        
        self.export_button = QPushButton("Export")
        self.export_button.setDisabled(True)
        self.export_button.clicked.connect(lambda: self.file_manager.export(min(SCHOOL.settings.EXPORT_timetable_export_theme.export_mode, 1), f"{eft_cb.currentText().upper()} Files (*.{eft_cb.currentText().lower()})"))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        
        base_widget.addWidget(preview_button)
        base_widget.addStretch()
        base_widget.addWidget(self.export_button)
        base_widget.addWidget(cancel_button)
        
        self.s_rb.setChecked(SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 0)
        self.l_rb.setChecked(SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 1)
        self.c_rb.setChecked(SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 2)
        
        self.addWidget(main_widget)
        self.addWidget(base_widget)
        
        for lvl_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
            for cls_id in cls_ids:
                self.select_cb_dict[lvl_id][1][cls_id].blockSignals(True)
                self.select_cb_dict[lvl_id][1][cls_id].setChecked(True)
                self.select_cb_dict[lvl_id][1][cls_id].blockSignals(False)
                
                self.export_button.setDisabled(False)
    
    def _select_sch(self, state: bool):
        for _, cls_cbs in self.select_cb_dict.values():
            for cls_cb in cls_cbs.values():
                if state != cls_cb.isChecked():
                    cls_cb.click()
    
    def _make_lvl_cb_func(self, level_id: ID):
        def lvl_cb_func(state: bool):
            for cls_cb in self.select_cb_dict[level_id][1].values():
                if state != cls_cb.isChecked():
                    cls_cb.click()
            
            if state:
                for lvl_cb, _ in self.select_cb_dict.values():
                    if lvl_cb != self.select_cb_dict[level_id] and not lvl_cb.isChecked():
                        break
                else:
                    if not self.select_all_cb.isChecked():
                        self.select_all_cb.click()
            else:
                if self.select_all_cb.isChecked():
                    self.select_all_cb.blockSignals(True)
                    self.select_all_cb.click()
                    self.select_all_cb.blockSignals(False)
        
        return lvl_cb_func
    
    def _make_cls_cb_func(self, level_id: ID, cls_id: ID):
        def cls_cb_func(state: bool):
            lvl_cb, cls_cbs = self.select_cb_dict[level_id]
            
            if state:
                for cls_cb in cls_cbs.values():
                    if cls_cb != cls_cbs[cls_id] and not cls_cb.isChecked():
                        break
                else:
                    if not lvl_cb.isChecked():
                        lvl_cb.click()
                
                SCHOOL.settings.EXPORT_selected_classes[level_id].insert(list(self.select_cb_dict[level_id][1]).index(cls_id), cls_id)
            else:
                if lvl_cb.isChecked():
                    lvl_cb.blockSignals(True)
                    lvl_cb.click()
                    lvl_cb.blockSignals(False)
                
                if self.select_all_cb.isChecked():
                    self.select_all_cb.blockSignals(True)
                    self.select_all_cb.click()
                    self.select_all_cb.blockSignals(False)
                
                SCHOOL.settings.EXPORT_selected_classes[level_id].remove(cls_id)
            
            self.export_button.setDisabled(next((False for cls_ids in SCHOOL.settings.EXPORT_selected_classes.values() if cls_ids), True))
        
        return cls_cb_func
    
    def _initGeometry(self):
        self.setMinimumSize(800, 550)
        
        screen_geom = self.screen().geometry()
        
        self.setGeometry(int(screen_geom.width() / 2 - self.geometry().width() / 2), int(screen_geom.height() / 2 - self.geometry().height() / 2), self.geometry().width(), self.geometry().height())
    
    def _set_export_mode(self, mode: int):
        SCHOOL.settings.EXPORT_timetable_export_theme.export_mode = mode
    
    def _set_timetable_export_theme(self):
        SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme = self.cls_title_text_theme.text_theme()
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme = self.ttbl_content_text_theme.text_theme()
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme = self.ttbl_heading_text_theme.text_theme()
        
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_bg_color = self.ttbl_bg_color.currentColor()
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_bg_color = self.ttbl_content_bg_color.currentColor()
        SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color = self.ttbl_heading_bg_color.currentColor()
        SCHOOL.settings.EXPORT_timetable_export_theme.break_bg_color = self.break_bg_color.currentColor()
        SCHOOL.settings.EXPORT_timetable_export_theme.border_color = self.border_color.currentColor()
        
        SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness = self.hlt_sb.value()
        SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness = self.vlt_sb.value()
        
        if self.s_rb.isChecked():
            SCHOOL.settings.EXPORT_timetable_export_theme.export_mode = 0
        elif self.l_rb.isChecked():
            SCHOOL.settings.EXPORT_timetable_export_theme.export_mode = 1
        elif self.c_rb.isChecked():
            SCHOOL.settings.EXPORT_timetable_export_theme.export_mode = 2
    
    def get_level_widget(self, cls_level: ClassLevel, index: Optional[int] = None):
        lvl_cb = QCheckBox("All")
        lvl_cb.clicked.connect(self._make_lvl_cb_func(cls_level.id))
        
        if index is None:
            self.select_cb_dict[cls_level.id] = lvl_cb, {}
        else:
            scd_lvl_list = list(self.select_cb_dict.items())
            scd_lvl_list.insert(index, (cls_level.id, (lvl_cb, {})))
            
            self.select_cb_dict.clear()
            self.select_cb_dict.update(dict(scd_lvl_list))
        
        if cls_level.id not in SCHOOL.settings.EXPORT_selected_classes:
            SCHOOL.settings.EXPORT_selected_classes[cls_level.id] = []
        
        cls_widget = BaseWidget()
        
        cls_lvl_widget = WidgetDropdown(cls_level.name.full(), cls_widget)
        cls_lvl_widget.header.addWidget(lvl_cb)
        
        for cls in cls_level.classes.values():
            cls_widget.addWidget(self.get_cls_widget(cls))
        
        return cls_lvl_widget
    
    def get_cls_widget(self, cls: Class, index: Optional[int] = None):
        cls_cb = QCheckBox()
        cls_cb.clicked.connect(self._make_cls_cb_func(cls.level.id, cls.id))
        
        if index is None:
            self.select_cb_dict[cls.level.id][1][cls.id] = cls_cb
        else:
            scd_cls_list = list(self.select_cb_dict[cls.level.id][1].items())
            scd_cls_list.insert(index, (cls.id, cls_cb))
            
            self.select_cb_dict[cls.level.id][1].clear()
            self.select_cb_dict[cls.level.id][1].update(dict(scd_cls_list))
        
        c_widget = BaseWidget(QHBoxLayout)
        
        c_widget.addWidget(QLabel(f"<b>{cls.name}</b>"))
        c_widget.addStretch()
        c_widget.addWidget(cls_cb)
        
        return c_widget
    
    def export_callback(self, path: str, file_type=None, a0=None):
        self._set_timetable_export_theme()
        
        file_type = file_type or SCHOOL.settings.EXPORT_timetable_export_theme.export_file_type
        subject_count = str(max(max(d for d, _ in cls_level.weekdays.values()) for _, cls_level in SCHOOL.class_levels))
        
        html_style_replacements = dict(
            cls_title_font_style=SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme.stylesheet.replace(";", ";\n\t\t"),
            ttbl_content_font_style=SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.stylesheet.replace(";", ";\n\t\t"),
            weekday_text_font_style=SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme.stylesheet.replace(";", ";\n\t\t"),
            
            ttbl_bg_color=SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_bg_color,
            ttbl_content_bg_color=SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_bg_color,
            ttbl_heading_bg_color=SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color,
            break_bg_color=SCHOOL.settings.EXPORT_timetable_export_theme.break_bg_color,
            border_color=SCHOOL.settings.EXPORT_timetable_export_theme.border_color,
            
            border_horizontal_width=str(SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness),
            border_vertical_width=str(SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
        )
        
        if file_type == "JPG":
            for surface, p in self.export_callback(path, "PNG", True):
                data = pygame.image.tostring(surface, "RGB")
                img = PILImage.frombytes("RGB", surface.get_size(), data)
                
                img.save(p.strip().removesuffix(".png") + ".jpg", quality=95)
        else:
            _l: list[tuple[pygame.Surface, str]] = []
            internal = a0 is not None and a0 == True
            
            if SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 0:
                if file_type == "HTML":
                    body = ""
                    
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            body += get_export_html_text(cls)
                        
                    html = HTML_TEXT.format(title="School", body=body, subject_count=subject_count, **html_style_replacements)
                    
                    with open(path, "w") as file:
                        file.write(html)
                elif file_type == "PNG":
                    surfs: list[pygame.Surface] = []
                    
                    width = 0
                    height = 0
                    
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            
                            cls_surf = get_export_surface(cls)
                            
                            width = max(width, cls_surf.get_width())
                            height += cls_surf.get_height()
                            
                            surfs.append(cls_surf)
                    
                    screen = pygame.Surface((width, height))
                    screen.fill("white")
                    
                    y = 0
                    for surf in surfs:
                        screen.blit(surf, ((0, y), surf.get_size()))
                        
                        y += surf.get_height()
                    
                    if internal:
                        _l.append((screen, path))
                    else:
                        pygame.image.save(screen, path)
                elif file_type == "CSV":
                    output = StringIO()
                    writer = csv.writer(output)
                    
                    _first_added = False
                    
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            
                            if cls.id not in SCHOOL.settings.EXPORT_selected_classes:
                                if _first_added:
                                    writer.writerow([])
                                
                                writer.writerow([f"{cls_level.name.full()} {cls.name}"])
                                write_export_csv(writer, cls)
                                
                                _first_added = True
                    
                    with open(path, "w", newline="", encoding="utf-8") as file:
                        file.write(output.getvalue().strip())
            elif SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 1:
                if file_type == "HTML":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        body = ""
                        
                        for cls_id in cls_ids:
                            cls = cls_level.classes[cls_id]
                            body += get_export_html_text(cls)
                        
                        html = HTML_TEXT.format(title=cls_level.name.full(), body=body, subject_count=subject_count, **html_style_replacements)
                        
                        with open(path + f"/{cls_level.name.full()}.html", "w") as file:
                            file.write(html)
                elif file_type == "PNG":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        surfs: list[pygame.Surface] = []
                        
                        width = 0
                        height = 0
                        
                        for cls_id in cls_ids:
                            cls = cls_level.classes[cls_id]
                            
                            cls_surf = get_export_surface(cls)
                            
                            width = max(width, cls_surf.get_width())
                            height += cls_surf.get_height()
                            
                            surfs.append(cls_surf)
                        
                        screen = pygame.Surface((width, height))
                        screen.fill("white")
                        
                        y = 0
                        for surf in surfs:
                            screen.blit(surf, ((0, y), surf.get_size()))
                            
                            y += surf.get_height()
                        
                        p = path + f"/{cls_level.name.full()}.png"
                        
                        if internal:
                            _l.append((screen, p))
                        else:
                            pygame.image.save(screen, p)
                elif file_type == "CSV":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        output = StringIO()
                        writer = csv.writer(output)
                        
                        _first_added = False
                        
                        for cls_id in cls_ids:
                            cls = cls_level.classes[cls_id]
                            
                            if _first_added:
                                writer.writerow([])
                            
                            writer.writerow([f"{cls_level.name.full()} {cls.name}"])
                            write_export_csv(writer, cls)
                            
                            _first_added = True
                        
                        with open(f"{path}/{cls_level.name.full()}.csv", "w", newline="", encoding="utf-8") as file:
                            file.write(output.getvalue().strip())
            elif SCHOOL.settings.EXPORT_timetable_export_theme.export_mode == 2:
                if file_type == "HTML":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            
                            body = get_export_html_text(cls)
                            html = HTML_TEXT.format(title=f"{cls_level.name.full()} {cls.name}", body=body, subject_count=subject_count, **html_style_replacements)
                            
                            with open(path + f"/{cls_level.name.full()} {cls.name}.html", "w") as file:
                                file.write(html)
                elif file_type == "PNG":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            
                            p = path + f"/{cls_level.name.full()} {cls.name}.png"
                            screen = get_export_surface(cls)
                            
                            if internal:
                                _l.append((screen, p))
                            else:
                                pygame.image.save(screen, p)
                elif file_type == "CSV":
                    for cls_level_id, cls_ids in SCHOOL.settings.EXPORT_selected_classes.items():
                        cls_level = SCHOOL.class_levels[cls_level_id]
                        
                        for cls_id in cls_ids:
                            cls = SCHOOL.class_levels[cls_level_id].classes[cls_id]
                            
                            output = StringIO()
                            writer = csv.writer(output)
                            
                            write_export_csv(writer, cls)
                            
                            with open(f"{path}/{cls_level.name.full()} {cls.name}.csv", "w", newline="", encoding="utf-8") as file:
                                file.write(output.getvalue().strip())
            
            if internal:
                return _l
        
        QMessageBox.information(self, "Export", "Export Successful")
    
    def exec(self):
        for lvl_index, (lvl_id, (_, cls_cbs)) in enumerate(self.select_cb_dict.copy().items()):
            if lvl_id in SCHOOL.class_levels.data:
                cls_level = SCHOOL.class_levels[lvl_id]
                lvl_widget: WidgetDropdown = self.sch_subject_selection_widget.indexWidget(lvl_index)
                
                lvl_widget.title_label.setText(cls_level.name.full())
                
                cls_ids_copy = cls_cbs.copy()
                for cls_index, cls_id in enumerate(reversed(cls_ids_copy)):
                    index = len(cls_ids_copy) - cls_index - 1
                    
                    if cls_id not in cls_level.classes:
                        lvl_widget.widget.popWidget(index)
                        
                        cls_cbs.pop(cls_id)
                        
                        if cls_id in SCHOOL.settings.EXPORT_selected_classes[lvl_id]:
                            SCHOOL.settings.EXPORT_selected_classes[lvl_id].pop(cls_id)
                    else:
                        lvl_widget.widget.indexWidget(index).indexWidget(0).setText(f"<b>{cls_level.classes[cls_id].name}</b>")
            else:
                self.select_cb_dict.pop(lvl_id)
                self.sch_subject_selection_widget.popWidget(lvl_index)
                
                SCHOOL.settings.EXPORT_selected_classes.pop(lvl_id)
        
        for cls_level_index, (lvl_id, cls_level) in enumerate(SCHOOL.class_levels):
            if lvl_id in self.select_cb_dict:
                for cls_index, (cls_id, cls) in enumerate(cls_level.classes.items()):
                    if cls_id not in self.select_cb_dict[lvl_id][1]:
                        lvl_widget: WidgetDropdown = self.sch_subject_selection_widget.indexWidget(lvl_index)
                        lvl_widget.widget.insertWidget(cls_index, self.get_cls_widget(cls, cls_index))
            else:
                self.sch_subject_selection_widget.insertWidget(cls_level_index, self.get_level_widget(cls_level, cls_level_index))
        
        return super().exec()
    
    def closeEvent(self, a0):
        self._set_timetable_export_theme()
        
        return super().closeEvent(a0)


FONTS: dict[int, pygame.font.Font] = {}

def _get_text(text_theme: TextTheme, text: str):
    t_t_id = id(text_theme)
    
    if t_t_id not in FONTS:
        FONTS[t_t_id] = pygame.font.SysFont(text_theme.family, text_theme.size, text_theme.bold, text_theme.italic)
    
    font = FONTS[t_t_id]
    
    if text:
        orig_text_surf = font.render(text, True, text_theme.color)
        
        surfs = [font.render(c, True, text_theme.color) for c in text]
        
        width_w_spacing = sum(s.get_width() for s in surfs)
        orig_spacing = (orig_text_surf.get_width() - width_w_spacing) / (len(text) - 1)
        
        width = width_w_spacing + (text_theme.letter_spacing + orig_spacing) * (len(text) - 1)
        height = max(s.get_height() for s in surfs)
        
        text_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        x = 0
        for s in surfs:
            text_surf.blit(s, (x, 0))
            
            x += s.get_width() + text_theme.letter_spacing + orig_spacing
        
        return text_surf
    
    return font.render(text, True, text_theme.color)

TTBL_X_MARGIN = 100
TTBL_Y_MARGIN = 200

TTBL_EXPORT_CELL_X_MARGIN = 10
TTBL_EXPORT_CELL_Y_MARGIN = 5

def get_export_surface(cls: Class):
    timetable, _ = SCHOOL.timetables_data[cls.id]
    
    _time_width = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme, "24:58 - 24:59").get_width()
    _cell_content_width = max(_get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme, s.name.short()).get_width() for _, s in SCHOOL.subjects)
    
    width = max(_cell_content_width, _time_width) + TTBL_EXPORT_CELL_X_MARGIN * 2
    height = max(FONTS[id(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme)].get_height(), FONTS[id(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme)].get_height()) + TTBL_EXPORT_CELL_Y_MARGIN * 2
    title_width = max(_get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme, d).get_width() for d in SCHOOL.settings.TIMETABLE_weekdays) + TTBL_EXPORT_CELL_X_MARGIN * 2
    
    ttbl_width = title_width + width * max(len(p) for p in timetable.values())
    ttbl_height = height * (len(timetable) + len(SCHOOL.settings.TIMETABLE_time_settings[cls.level.id]))
    
    x1 = TTBL_X_MARGIN / 2
    y1 = TTBL_Y_MARGIN / 2
    
    cls_title_surf = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.cls_title_text_theme, f"{cls.level.name.full()} {cls.name}")
    
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
    
    screen = pygame.Surface((ttbl_width + TTBL_X_MARGIN, ttbl_height + TTBL_Y_MARGIN + cls_title_rect.height))
    screen.fill(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_bg_color)
    
    screen.blit(cls_title_surf, cls_title_rect)
    
    _y = y2
    
    for col, (day, periods) in enumerate(timetable.items()):
        ttbl_weekday_text = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme, day)
        ttbl_weekday_rect = pygame.Rect(x1, _y, title_width, height) ; _y += ttbl_weekday_rect.height
        
        if col == 0 and "Everyday" in SCHOOL.settings.TIMETABLE_time_settings[cls.level.id]:
            time_settings = SCHOOL.settings.TIMETABLE_time_settings[cls.level.id]["Everyday"]
            
            start_time = end_time = time_settings.start_time
            ttbl_time_x = ttbl_weekday_rect.right
            
            for row in range(len(periods)):
                if row == -1:
                    ttbl_time_rect = pygame.Rect(ttbl_time_x - ttbl_weekday_rect.width, ttbl_weekday_rect.y, width, height)
                    
                    pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color, ttbl_time_rect)
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                else:
                    end_time = start_time + (time_settings.break_time_duration if row == cls.level.weekdays[day][1] - 1 else time_settings.interval)
                    
                    ttbl_time_surf = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme, f"{start_time} - {end_time}")
                    ttbl_time_rect = pygame.Rect(ttbl_time_x, ttbl_weekday_rect.y, width, height) ; ttbl_time_x += ttbl_time_rect.width
                    
                    ttbl_t_t_y = ttbl_time_rect.centery - ttbl_time_surf.get_height() / 2
                    match SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme.text_alignment:
                        case "Left":
                            ttbl_t_t_x = ttbl_time_rect.left
                        case "Center":
                            ttbl_t_t_x = ttbl_time_rect.centerx - ttbl_time_surf.get_width() / 2
                        case "Right":
                            ttbl_t_t_x = ttbl_time_rect.right - ttbl_time_surf.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
                    
                    ttbl_time_text_rect = pygame.Rect(((ttbl_t_t_x + (SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness if (row != 0 and periods[row - 1].id == BreakPeriod.id) or row == 0 else 0), ttbl_t_t_y), ttbl_time_rect.size))
                    
                    pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color, ttbl_time_rect)
                    screen.blit(ttbl_time_surf, ttbl_time_text_rect)
                    
                    start_time = end_time
                    
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                    if row == len(periods) - 1:
                        pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topright, ttbl_time_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
            
            ttbl_weekday_rect.y = _y
            _y += ttbl_weekday_rect.height
        
        if day in SCHOOL.settings.TIMETABLE_time_settings[cls.level.id]:
            time_settings = SCHOOL.settings.TIMETABLE_time_settings[cls.level.id][day]
            
            start_time = end_time = time_settings.start_time
            ttbl_time_x = ttbl_weekday_rect.right
            
            for row in range(-1, len(periods)):
                if row == -1:
                    ttbl_time_rect = pygame.Rect(ttbl_time_x - ttbl_weekday_rect.width, ttbl_weekday_rect.y, width, height)
                    
                    pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color, ttbl_time_rect)
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                else:
                    end_time = start_time + (time_settings.break_time_duration if row == cls.level.weekdays[day][1] - 1 else time_settings.interval)
                    
                    ttbl_time_surf = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme, f"{start_time.hour}:{start_time.minute} - {end_time.hour}:{end_time.minute}")
                    ttbl_time_rect = pygame.Rect(ttbl_time_x, ttbl_weekday_rect.y, width, height) ; ttbl_time_x += ttbl_time_rect.width
                    
                    ttbl_t_t_y = ttbl_time_rect.centery - ttbl_time_surf.get_height() / 2
                    match SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme.text_alignment:
                        case "Left":
                            ttbl_t_t_x = ttbl_time_rect.left
                        case "Center":
                            ttbl_t_t_x = ttbl_time_rect.centerx - ttbl_time_surf.get_width() / 2
                        case "Right":
                            ttbl_t_t_x = ttbl_time_rect.right - ttbl_time_surf.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
                    
                    ttbl_time_text_rect = pygame.Rect(((ttbl_t_t_x + (SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness if (row != 0 and periods[row - 1].id == BreakPeriod.id) or row == 0 else 0), ttbl_t_t_y), ttbl_time_rect.size))
                    
                    pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color, ttbl_time_rect)
                    screen.blit(ttbl_time_surf, ttbl_time_text_rect)
                    
                    start_time = end_time
                    
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                    
                    if row == len(periods) - 1:
                        pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topright, ttbl_time_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_time_rect.topleft, ttbl_time_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
            
            ttbl_weekday_rect.y = _y
            _y += ttbl_weekday_rect.height
        
        match SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_text_theme.text_alignment:
            case "Left":
                ttbl_t_x = ttbl_weekday_rect.left
            case "Center":
                ttbl_t_x = ttbl_weekday_rect.centerx - ttbl_weekday_text.get_width() / 2
            case "Right":
                ttbl_t_x = ttbl_weekday_rect.right - ttbl_weekday_text.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
        
        ttbl_t_y = ttbl_weekday_rect.centery - ttbl_weekday_text.get_height() / 2
        
        ttbl_title_text_rect = pygame.Rect((ttbl_t_x, ttbl_t_y), ttbl_weekday_rect.size)
        
        pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_heading_bg_color, ttbl_weekday_rect)
        screen.blit(ttbl_weekday_text, ttbl_title_text_rect)
        
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
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topright, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topleft, ttbl_subject_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                
                if col == len(timetable) - 1:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.bottomleft, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
                
                if col != 0 and day in SCHOOL.settings.TIMETABLE_time_settings[cls.level.id]:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topleft, ttbl_subject_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
            else:
                ttbl_subject_text_surf = _get_text(SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme, subject.name.short() if subject.id != FreePeriod.id else "")
                
                match SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_text_theme.text_alignment:
                    case "Left":
                        ttbl_s_x = ttbl_subject_rect.left
                    case "Center":
                        ttbl_s_x = ttbl_subject_rect.centerx - ttbl_subject_text_surf.get_width() / 2
                    case "Right":
                        ttbl_s_x = ttbl_subject_rect.right - ttbl_subject_text_surf.get_width() - SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness
                
                ttbl_s_y = ttbl_subject_rect.centery - ttbl_subject_text_surf.get_height() / 2
                
                ttbl_subject_text_rect = pygame.Rect(((ttbl_s_x + (SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness if (row != 0 and periods[row - 1].id == BreakPeriod.id) or row == 0 else 0), ttbl_s_y), ttbl_subject_rect.size))
                
                pygame.draw.rect(screen, SCHOOL.settings.EXPORT_timetable_export_theme.ttbl_content_bg_color, ttbl_subject_rect)
                screen.blit(ttbl_subject_text_surf, ttbl_subject_text_rect)
                
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topleft, ttbl_subject_rect.topright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
                pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topleft, ttbl_subject_rect.bottomleft, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                if row == len(periods) - 1:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.topright, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.vertical_line_thickness)
                if col == len(timetable) - 1:
                    pygame.draw.line(screen, SCHOOL.settings.EXPORT_timetable_export_theme.border_color, ttbl_subject_rect.bottomleft, ttbl_subject_rect.bottomright, SCHOOL.settings.EXPORT_timetable_export_theme.horizontal_line_thickness)
    
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
        background-color: {ttbl_heading_bg_color};
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




