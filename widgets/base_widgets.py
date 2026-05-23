
from imports import *
from theme import THEME_MANAGER
from utils.data import ID


class BaseWidget(QWidget):
    def __init__(self, layout_type: Optional[type[QVBoxLayout] | type[QHBoxLayout]] = None):
        super().__init__()
        
        self.layout_type = layout_type or QVBoxLayout
        self._init()
    
    def _init(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        self.container = QWidget()
        self.main_layout = self.layout_type(self.container)
        
        layout.addWidget(self.container)
    
    @staticmethod
    def static_clear_layout(layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            
            widget = item.widget()
            layout_item = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            elif layout_item is not None:
                BaseWidget.static_clear_layout(layout_item)
    
    def delete(self):
        parent = self.parent()
        if parent and isinstance(parent, QWidget):
            parent.layout().removeWidget(self)
        
        self.deleteLater()
    
    def clearLayout(self):
        self.static_clear_layout(self.getLayout())
    
    def deleteLater(self):
        self.clearLayout()
        self.setParent(None)
        
        return super().deleteLater()
    
    def styleSheet(self):
        return self.getWidget().styleSheet()
    
    def setSpacing(self, spacing: int):
        self.getLayout().setSpacing(spacing)
    
    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        self.getLayout().setContentsMargins(left, top, right, bottom)
    
    def setStyleSheet(self, stylesheet: str):
        self.getWidget().setStyleSheet(stylesheet)

        for widget in self.getWidgets():
            widget.setStyleSheet(stylesheet)
    
    def setProperty(self, name: str | None, value: str):
        self.getWidget().setProperty(name, value)

        for widget in self.getWidgets():
            widget.setProperty(name, value)
    
    def setFixedWidth(self, width: int):
        self.getWidget().setFixedWidth(width)

        for widget in self.getWidgets():
            widget.setFixedWidth(width)
    
    def setFixedHeight(self, height: int):
        self.getWidget().setFixedHeight(height)

        for widget in self.getWidgets():
            widget.setFixedHeight(height)
    
    def removeWidget(self, a0: Optional[QWidget]):
        self.getLayout().removeWidget(a0)
    
    def addWidget(self, widget: QWidget, stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.main_layout.addWidget(widget, **kwargs)
    
    def insertWidget(self, index: int, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.main_layout.insertWidget(index, widget, **kwargs)
    
    def addStretch(self, stretch: Optional[int] = None):
        args = []
        
        if stretch is not None:
            args.append(stretch)
        
        self.main_layout.addStretch(*args)
    
    def insertStretch(self, index: int, stretch: Optional[int] = None):
        args = [index]
        
        if stretch is not None:
            args.append(stretch)
        
        self.main_layout.insertStretch(*args)
    
    def addSpacing(self, size: int):
        self.getLayout().addSpacing(size)
    
    def insertSpacing(self, index: int, size: int):
        self.getLayout().insertSpacing(index, size)
    
    def getWidget(self):
        return self.container
    
    def getWidgets(self):
        return []
    
    def getLayout(self):
        return self.main_layout

class BaseScrollWidget(BaseWidget):
    def __init__(self, layout_type = None):
        super().__init__(layout_type)
    
    def _init(self):
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        self.container = QWidget()
        self.scroll_widget.setWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        layout.addWidget(self.scroll_widget)
    
    def getWidgets(self):
        return [self.scroll_widget]

    def getScrollWidget(self):
        return self.scroll_widget

class BaseDialogWidget(QDialog):
    def __init__(self, title: str, widget_type: type[BaseWidget | BaseScrollWidget], layout_type = None):
        super().__init__()
        
        self.widget = widget_type(layout_type)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        layout.addWidget(self.widget)
        
        self.setWindowTitle(title)
        
        self.setContentsMargins(0, 0, 0, 0)
    
    def setSpacing(self, spacing: int):
        self.widget.setSpacing(spacing)
    
    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        self.widget.setContentsMargins(left, top, right, bottom)
    
    def setStyleSheet(self, stylesheet: str):
        self.widget.setStyleSheet(stylesheet)
    
    def setProperty(self, name: str | None, value: str):
        self.widget.setProperty(name, value)
    
    def setFixedWidth(self, width: int):
        self.widget.setFixedWidth(width)
    
    def setFixedHeight(self, height: int):
        self.widget.setFixedHeight(height)
    
    def addWidget(self, widget: QWidget, stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        self.widget.addWidget(widget, stretch, alignment)
    
    def insertWidget(self, index: int, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        self.widget.insertWidget(widget, stretch, alignment)
    
    def addStretch(self, stretch: Optional[int] = None):
        self.widget.insertWidget(stretch)
    
    def insertStretch(self, index: int, stretch: Optional[int] = None):
        self.widget.insertStretch(index, stretch)
    
    def getWidget(self):
        return self.widget
    
    def getLayout(self):
        return self.widget.getLayout()


class BaseGridWidget(BaseScrollWidget):
    def __init__(self, row_max: int):
        super().__init__()
        
        self.row_max = row_max
        
        self.widgets: list[BaseWidget] = []
        self.widget_count = 0
    
    def addWidget(self, widget, stretch = None, alignment = None):
        self.widget_count += 1
        
        if len(self.all_widgets) % self.row_max == 0:
            bg_widget = BaseWidget(QHBoxLayout)
            
            super().addWidget(bg_widget)
            
            self.widgets.append(bg_widget)
        
        self.widgets[-1].addWidget(widget, stretch, alignment)
    
    def insertWidget(self, row: int, col: int, widget: QWidget, stretch: int = None, alignment: Qt.AlignmentFlag = None):
        self.widgets[col].insertWidget(row, widget, stretch, alignment)
        
        for i in range(len(self.widgets) - col):
            f_widget = self.widgets[col + i]
            f_child_widgets = f_widget.getLayout().children()
            
            if len(f_child_widgets) >= self.row_max and col + i + 1 < len(self.widgets):
                fin_widg = f_child_widgets[-1]
                
                f_widget.removeWidget(fin_widg)
                
                if col + i + 1 < len(self.widgets):
                    self.widgets[col + i + 1].insertWidget(0, fin_widg)
                    
                    self.widget_count += 1
                else:
                    self.addWidget(fin_widg)
    
    def removeWidget(self, a0):
        coord = None
        
        for col, row_widget in enumerate(self.widgets):
            for row, widget in enumerate(row_widget.getLayout().children()):
                if a0 == widget:
                    row_widget.removeWidget(a0)
                    coord = row, col
                    break
            else: continue
            break
        
        if not coord:
            raise ValueError(f"{a0} is not in widget")
        
        row, col = coord
        
        for i in range(col - len(self.widgets)):
            prev_row_widget = self.widgets[-(i + 2)]
            row_widget = self.widgets[-(i + 1)]
            
            widgets = row_widget.getLayout().children()[0]
            
            row_widget.removeWidget(widgets)
            prev_row_widget.addWidget(widgets)
        
        self.row_max -= 1


class BaseSettingDialog(BaseDialogWidget):
    def __init__(self, title: str):
        super().__init__(title, BaseScrollWidget)
    
    def go_to(self, widget: BaseWidget):
        self.getWidget().getScrollWidget().verticalScrollBar().setValue(widget.y())
        
        widget.setFocus()


class BaseSettingEntry(BaseWidget):
    def __init__(self, simple_placeholder: str, extended_placeholders: list[str], option_dialogs: dict[str, tuple[str, type[BaseSettingDialog]]], entry: Entry):
        super().__init__()
        
        self.entry = entry
        self.option_dialogs = option_dialogs
        
        # ----------------------------------------------------------------------------------------
        menu_area = BaseWidget(QHBoxLayout)
        
        options_button = QPushButton(":")
        
        dialog_buttons_widget = BaseWidget(QHBoxLayout)
        for button in self.get_dialog_buttons():
            dialog_buttons_widget.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        delete_button = QPushButton("x")
        
        menu_area.addWidget(options_button, alignment=Qt.AlignmentFlag.AlignLeft)
        menu_area.addWidget(dialog_buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        menu_area.addWidget(delete_button, alignment=Qt.AlignmentFlag.AlignRight)
                
        # ----------------------------------------------------------------------------------------
        
        edits_area = BaseWidget(QHBoxLayout)
        
        simple_line_edit = QLineEdit()
        simple_line_edit.setPlaceholderText(simple_placeholder)
        
        extended_edits_widget = BaseWidget()
        for placeholder in extended_placeholders:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            
            extended_edits_widget.addWidget(line_edit)
        
        extended_edits_widget.setVisible(False)
        
        self.nominal_info_widget = BaseWidget()
        
        edits_area.addWidget(simple_line_edit)
        edits_area.addWidget(extended_edits_widget)
        edits_area.addWidget(self.nominal_info_widget)
        
        # ----------------------------------------------------------------------------------------
        
        status_widget = QStatusBar()
        
        status_widget.addWidget(QLabel("Test"))
        
        # ----------------------------------------------------------------------------------------
        
        self.addWidget(menu_area)
        self.addWidget(edits_area)
        self.addWidget(status_widget)
    
    def get_dialog_buttons(self):
        for name, (title, cls) in self.option_dialogs.items():
            def open_func():
                dialog_obj = cls(title, self.id)
                dialog_obj.exec()
            
            button = QPushButton(name)
            button.clicked.connect(open_func)
            
            yield button


class BaseSettingWidget(BaseWidget):
    def __init__(self, main_window: QMainWindow, name: str, simple_placeholder: str, extended_placeholders: list[str], option_dialogs: dict[str, tuple[str, type[BaseSettingDialog]]]):
        super().__init__()
        
        self.main_window = main_window
        self.simple_placeholder = simple_placeholder
        self.extended_placeholders = extended_placeholders
        self.option_dialogs = option_dialogs
        
        self.add_button = QPushButton()
        self.add_button.clicked.connect(lambda: self.add())
        self.add_button.setText(f"Add {name}")
        
        self.scroll_widget = BaseScrollWidget()
        
        self.addWidget(self.scroll_widget)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
    
    def get_widget_type(self) -> type[BaseSettingEntry]:
        raise NotImplementedError()
    
    def go_to(self, widget: BaseSettingEntry):
        self.scroll_area.verticalScrollBar().setValue(widget.y())
        widget.setFocus()
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Enter:
            focus_widget = self.focusWidget()
            
            if isinstance(focus_widget, (QLineEdit, QScrollArea)):
                self.add(self.input_placeholders)
        
        return super().keyPressEvent(a0)
    
    def add(self, entry: Optional[Entry] = None, index: Optional[int] = None):
        widget = self.get_widget_type()(self.simple_placeholder, self.extended_placeholders, self.option_dialogs, entry)
        
        self.insertWidget(index or len(self.info) - 1, widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        
        QTimer.singleShot(
            100,
            lambda: self.scroll_widget.verticalScrollBar().setValue(self.scroll_widget.verticalScrollBar().maximum())
        )
        
        return widget.entry
    
    def remove(self, widget: BaseSettingEntry):
        widget.delete()
        
        return widget.entry.id


