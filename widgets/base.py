
from imports import *
from theme import THEME_MANAGER


class BaseWidget(QWidget):
    def __init__(self, layout_type: Optional[type[QVBoxLayout] | type[QHBoxLayout]] = None):
        super().__init__()
        
        self.layout_type = layout_type or QVBoxLayout
        self._children: list[QObject] = []
        
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
        
        self._children.remove(a0)
    
    def popWidget(self, index: int):
        self.getLayout().removeWidget(self.getChildren()[index])
        
        self._children.pop(index)
    
    def addWidget(self, widget: QWidget, stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.getLayout().addWidget(widget, **kwargs)
        self._children.append(widget)
    
    def insertWidget(self, index: int, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.getLayout().insertWidget(index, widget, **kwargs)
        self._children.insert(index, widget)
    
    def addStretch(self, stretch: Optional[int] = None):
        args = []
        
        if stretch is not None:
            args.append(stretch)
        
        self.getLayout().addStretch(*args)
        
        self._children.append({"stretch": stretch})
    
    def insertStretch(self, index: int, stretch: Optional[int] = None):
        args = [index]
        
        if stretch is not None:
            args.append(stretch)
        
        self.getLayout().insertStretch(*args)
        
        self._children.insert(index, {"stretch": stretch})
    
    def addSpacing(self, size: int):
        self.getLayout().addSpacing(size)
        
        self._children.append({"space": size})
    
    def insertSpacing(self, index: int, size: int):
        self.getLayout().insertSpacing(index, size)
        
        self._children.insert(index, {"space": size})
    
    def indexOf(self, a0: QWidget | None):
        return self.getLayout().indexOf(a0)
    
    def getWidget(self):
        return self.container
    
    def getWidgets(self):
        return []
    
    def getLayout(self):
        return self.main_layout
    
    def getChildren(self):
        return self._children

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
        self.widget.insertWidget(index, widget, stretch, alignment)
    
    def addStretch(self, stretch: Optional[int] = None):
        self.widget.addStretch(stretch)
    
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
        if self.widget_count % self.row_max == 0:
            bg_widget = BaseWidget(QHBoxLayout)
            bg_widget.setSpacing(2)
            bg_widget.setContentsMargins(0, 0, 0, 0)
            bg_widget.addStretch()
            
            super().addWidget(bg_widget)
            
            self.widgets.append(bg_widget)
        
        self.widget_count += 1
        
        self.widgets[-1].insertWidget((self.widget_count - 1) % self.row_max, widget, stretch, alignment)
    
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
            for row, widget in enumerate(row_widget.getChildren()):
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
        self.getScrollWidget().verticalScrollBar().setValue(widget.y())
        
        widget.setFocus()
    
    def getScrollWidget(self):
        return self.getWidget().getScrollWidget()

class BaseSettingEntry(BaseWidget):
    def __init__(self, i_parent: "BaseSettingWidget", simple_placeholder: str, extended_placeholders: list[str], option_dialogs: dict[str, tuple[str, type[BaseSettingDialog]] | tuple[str, type[BaseSettingDialog], tuple]], entry: Entry):
        super().__init__()
        
        self.entry = entry
        self.i_parent = i_parent
        self.option_dialogs = option_dialogs
        
        self.dialog_widget_funcs = []
        
        # ----------------------------------------------------------------------------------------
        menu_area = BaseWidget(QHBoxLayout)
        
        options_button = QPushButton("☰")
        
        dialog_buttons_widget = BaseWidget(QHBoxLayout)
        for button in self.get_dialog_buttons():
            dialog_buttons_widget.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        delete_button = QPushButton("×")
        delete_button.clicked.connect(self.remove)
        
        menu_area.addWidget(options_button, alignment=Qt.AlignmentFlag.AlignLeft)
        menu_area.addWidget(dialog_buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        menu_area.addWidget(delete_button, alignment=Qt.AlignmentFlag.AlignRight)
                
        # ----------------------------------------------------------------------------------------
        
        simple, extended = self.get_init_text()
        
        edits_area = BaseWidget(QHBoxLayout)
        
        simple_line_edit = QLineEdit()
        simple_line_edit.textChanged.connect(self.simple_name_changed)
        simple_line_edit.setText(simple)
        simple_line_edit.setPlaceholderText(simple_placeholder)
        
        if extended_placeholders:
            extended_edits_widget = BaseWidget()
            for i, placeholder in enumerate(extended_placeholders):
                def ext(t: str):
                    self.extended_name_changed(t, i)
                
                line_edit = QLineEdit()
                line_edit.textChanged.connect(ext)
                line_edit.setText(extended[i])
                line_edit.setPlaceholderText(placeholder)
                
                extended_edits_widget.addWidget(line_edit)
            
            extended_edits_widget.setVisible(False)
            
            edits_area.addWidget(extended_edits_widget)
        
        edits_area.addWidget(simple_line_edit)
        
        self.nominal_info_widget = BaseWidget()
        
        edits_area.addWidget(self.nominal_info_widget)
        
        # ----------------------------------------------------------------------------------------
        
        status_widget = QStatusBar()
        
        # ----------------------------------------------------------------------------------------
        
        self.addWidget(menu_area)
        self.addWidget(edits_area)
        self.addWidget(status_widget)
    
    def remove(self):
        self.i_parent.remove(self)
    
    def get_dialog_buttons(self):
        for name, dialog_info in self.option_dialogs.items():
            if len(dialog_info) == 2:
                title, cls = dialog_info
                variables = ()
            elif len(dialog_info) == 3:
                title, cls, variables = dialog_info
            else:
                raise TypeError(f"Expected dialog info of length 2 or 3 but got length: {len(dialog_info)}")
            
            button = QPushButton(name)
            button.clicked.connect(self.make_open_dialogs_func(title, cls, *variables))
            
            yield button
    
    def make_open_dialogs_func(self, title, cls: type[BaseSettingDialog], *args):
        def make_dialog():
            return cls(self.i_parent, self.entry.id, title, *args)
        
        self.dialog_widget_funcs.append(make_dialog)
        
        return lambda: make_dialog().exec()
    
    def get_init_text(self):
        raise NotImplementedError()
    
    def simple_name_changed(self, text: str):
        raise NotImplementedError()
    
    def extended_name_changed(self, text: str, index: int):
        raise NotImplementedError()

class BaseSettingWidget(BaseWidget):
    def __init__(self, name: str):
        super().__init__()
        
        self.widgets = {}
        
        self.add_button = QPushButton()
        self.add_button.clicked.connect(lambda: self.add())
        self.add_button.setText(f"Add {name}")
        
        self.scroll_widget = BaseScrollWidget()
        
        self.addWidget(self.scroll_widget)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        for _, entry in self.get_global():
            self.add(entry)
        
        QTimer.singleShot(
            150,
            lambda: self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(0)
        )
    
    def get_global(self) -> Global:
        raise NotImplementedError()
    
    def get_widget_type(self) -> type[BaseSettingEntry]:
        raise NotImplementedError()
    
    def go_to(self, widget_entry: Entry):
        widget: BaseSettingEntry = next(w for w in self.scroll_widget.getChildren() if w.entry.id == widget_entry.id)
        
        self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(widget.y())
        widget.setFocus()
        
        return widget
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Enter:
            focus_widget = self.focusWidget()
            
            if isinstance(focus_widget, (QLineEdit, QScrollArea)):
                self.add(self.input_placeholders)
        
        return super().keyPressEvent(a0)
    
    def add(self, entry: Optional[Entry] = None, index: Optional[int] = None):
        widget_data = self.get_widget_type()
        
        if isinstance(widget_data, tuple):
            widget_type, variables = widget_data
        else:
            widget_type = widget_data
            variables = []
        
        widget = widget_type(self, entry, *variables)
        
        if index is None:
            self.scroll_widget.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        else:
            self.scroll_widget.insertWidget(index, widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        
        self.widgets[entry.id] = widget
        
        QTimer.singleShot(
            100,
            lambda: self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(self.scroll_widget.getScrollWidget().verticalScrollBar().maximum())
        )
        
        return widget.entry
    
    def remove(self, widget: BaseSettingEntry):
        widget.delete()
        self.widgets.pop(widget.entry.id)
        self.get_global().remove(widget.entry.id)
        
        return widget.entry.id


