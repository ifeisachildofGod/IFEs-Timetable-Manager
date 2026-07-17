
from enum import Enum
import importlib
from imports import *

# for use by other dependant files
from theme import THEME_MANAGER

_T = TypeVar("_T")


class Status(Enum):
    MESSAGE = "MESSAGE"
    WARN = "WARN"
    ERROR = "ERROR"


class BaseWidget(QWidget):
    clicked = pyqtSignal(QMouseEvent)
    key_pressed = pyqtSignal(int)
    
    def __init__(self, layout_type: Optional[type[QVBoxLayout] | type[QHBoxLayout]] = None, parent=None):
        super().__init__(parent)
        
        self.layout_type = layout_type or QVBoxLayout
        self._children: list[QObject] = []
        
        self._init()
    
    def _init(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        self.container = QWidget()
        self.container.setProperty("class", "BaseWidget")
        
        self.container.mousePressEvent = self._mouseClicked
        self.container.keyPressEvent = self._keyPressed
        
        self.main_layout = self.layout_type(self.container)
        
        layout.addWidget(self.container)
    
    def _mouseClicked(self, ev):
        self.clicked.emit(ev)
    
    def _keyPressed(self, ev):
        self.key_pressed.emit(ev.key())
    
    @staticmethod
    def static_clear_layout(layout: QHBoxLayout | QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            
            widget = item.widget()
            layout_item = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            elif layout_item is not None:
                BaseWidget.static_clear_layout(layout_item)
    
    @staticmethod
    def setStyleProperty(obj: QWidget, name: str | tuple[str] | set[str] | list[str], value: str | tuple[str] | set[str] | list[str]):
        assert type(name) == type(value)
        
        if isinstance(name, (tuple, set, list)):
            assert len(name) == len(value)
            
            names = name
            values = value
        elif isinstance(name, str):
            names = [name]
            values = [value]
        else:
            raise TypeError(f"Invalid name type: {type(name)}")
        
        for n, v in zip(names, values):
            assert ";" not in n
            
            stylesheet = obj.styleSheet() + " "
            s_index = stylesheet.find(n)
            start_index = s_index if s_index != -1 else len(stylesheet)
            
            e_index = stylesheet[start_index:].find(";")
            end_index = start_index + e_index + 1 if s_index != -1 and e_index != -1 else len(stylesheet)
            
            stylesheet = list(stylesheet)
            stylesheet[start_index : end_index] = f"{n}: {v.strip().removesuffix(";")};"
            
            new_stylesheet = "".join(stylesheet).removesuffix(" ")
            
            obj.setStyleSheet(new_stylesheet)
    
    @staticmethod
    def getStyleProperty(obj: QWidget, name: str | tuple[str] | set[str] | list[str]):
        if isinstance(name, (tuple, set, list)):
            names = name
        elif isinstance(name, str):
            names = [name]
        else:
            raise TypeError(f"Invalid name type: {type(name)}")
        
        values = []
        
        for n in names:
            assert ";" not in n
            
            stylesheet = obj.styleSheet()
            
            start_index = stylesheet.find(n)
            
            assert start_index != -1
            
            start_index += stylesheet[start_index:].find(":") + 1
            
            e_index = stylesheet[start_index:].find(";")
            end_index = start_index + e_index if e_index != -1 else len(stylesheet)
            
            values.append(stylesheet[start_index : end_index].strip())
        
        return values[0] if isinstance(name, str) else values
    
    def delete(self):
        parent = self.parent()
        
        if parent:
            if isinstance(parent, (BaseWidget, BaseScrollWidget)):
                parent.removeWidget(self)
            elif isinstance(parent, QWidget):
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
    
    def indexWidget(self, index: int):
        return self.getChildren()[index]
    
    def removeWidget(self, a0: Optional[QWidget]):
        self.getLayout().removeWidget(a0)
        
        if a0 is not None:
            self._children.remove(a0)
    
    def popWidget(self, index: int):
        widget = self.getChildren()[index]
        
        widget.deleteLater()
        self.getLayout().removeWidget(widget)
        
        self._children.pop(index)
    
    def addWidget(self, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.getLayout().addWidget(widget, **kwargs)
        
        if widget is not None:
            self._children.append(widget)
    
    def insertWidget(self, index: int, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        kwargs = {}
        
        if stretch is not None:
            kwargs["stretch"] = stretch
        if alignment is not None:
            kwargs["alignment"] = alignment
        
        self.getLayout().insertWidget(index, widget, **kwargs)
        
        if widget is not None:
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
    
    def indexOf(self, a0: Optional[QWidget]):
        return self.getLayout().indexOf(a0)
    
    def getWidget(self):
        return self.container
    
    def getWidgets(self):
        return []
    
    def getLayout(self):
        return self.main_layout
    
    def getChildren(self, a0: Optional[type[_T] | tuple[type[_T]]] = None):
        return list(c for c in self._children if isinstance(c, (a0 if a0 is not None else QWidget)))

class BaseScrollWidget(BaseWidget):
    def __init__(self, layout_type = None):
        super().__init__(layout_type)
    
    def _init(self):
        self.scroll_widget = QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        
        self.container = QWidget()
        self.container.setProperty("class", "BaseWidget")
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
    def __init__(self, title: str, widget_type: type[BaseWidget | BaseScrollWidget], layout_type: type[QHBoxLayout | QVBoxLayout] = None):
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

class BaseFlowGridWidget(BaseScrollWidget):
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
            else:
                continue
            
            break
        
        if not coord:
            raise ValueError(f"{a0} is not in widget")
        
        row, col = coord
        
        for i in range(len(self.widgets) - col - 1):
            prev_row_widget = self.widgets[col + i]
            row_widget = self.widgets[col + i + 1]
            
            widget = row_widget.indexWidget(0)
            
            row_widget.removeWidget(widget)
            prev_row_widget.insertWidget(len(prev_row_widget.getChildren(QWidget)), widget)
            
            if not row_widget.getChildren(QWidget):
                row_widget.delete()
                self.widgets.remove(row_widget)


class StatusBar(BaseWidget):
    def __init__(self):
        super().__init__(QHBoxLayout)
        
        self.setSpacing(10)
        self.setContentsMargins(0, 0, 0, 0)
        
        self.statuses: dict[str, BaseWidget] = {}
        
        self.addStretch()
    
    def _insertMessage(self, index: int, key: str, message: str, color: str):
        assert key not in self.statuses
        
        msg_widget = BaseWidget(QHBoxLayout)
        msg_widget.setSpacing(10)
        msg_widget.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(message)
        label.setStyleSheet(f"color: {color}")
        
        msg_widget.addWidget(label)
        
        if index != len(self.statuses):
            msg_widget.addWidget(QLabel("●"))
        elif index != 0:
            list(self.statuses.values())[index - 1].addWidget(QLabel("●"))
        
        self.insertWidget(index + 1, msg_widget)
        
        statuses = list(self.statuses.items())
        statuses.insert(index, (key, msg_widget))
        
        self.statuses.clear()
        self.statuses.update(dict(statuses))
    
    def remove(self, key: str):
        l_statuses = list(self.statuses)
        index = l_statuses.index(key)
        
        widget = self.statuses.pop(key)
        
        if index != 0 and index == len(l_statuses) - 1:
            list(self.statuses.values())[-1].popWidget(1)
        
        self.removeWidget(widget)
        widget.deleteLater()
    
    def removeLinient(self, key: str):
        if key in self.statuses:
            self.remove(key)
    
    def addMessage(self, msg_type: Status, key: str, message: str):
        self.insertMessage(msg_type, len(self.statuses), key, message)
    
    def insertMessage(self, msg_type: Status, index: int, key: str, message: str):
        match msg_type:
            case Status.MESSAGE:
                self._insertMessage(index, key, message, "white")
            case Status.WARN:
                self._insertMessage(index, key, f"<i>{message}</i>", "yellow")
            case Status.ERROR:
                self._insertMessage(index, key, f"<b>{message}</b>", "#ff3030")



class BaseSettingDialog(BaseDialogWidget):
    def __init__(self, title: str, widget_type: Optional[type[BaseWidget | BaseScrollWidget]] = None):
        super().__init__(title, widget_type or BaseScrollWidget)
    
    def go_to(self, widget: BaseWidget):
        self.getScrollWidget().verticalScrollBar().setValue(widget.y())
        
        widget.setFocus()
    
    def getScrollWidget(self):
        return self.getWidget().getScrollWidget()

class BaseSettingEntry(BaseWidget):
    IconToolBarOption = importlib.import_module("widgets.user_interface").IconToolBarOption
    
    def __init__(self, i_parent: "BaseSettingWidget", general_entry_name: str, extended_placeholders: list[str], option_dialogs: dict[str, tuple[str, type[BaseSettingDialog]] | tuple[str, type[BaseSettingDialog], tuple]], entry: Entry):
        super().__init__()
        
        self.__init = True
        
        self.setProperty("class", "SettingEntry")
        
        self.entry = entry
        self.i_parent = i_parent
        self.option_dialogs = option_dialogs
        self.general_entry_name = general_entry_name
        
        simple_placeholder = f"Enter {self.general_entry_name} Name"
        
        self.dialog_widget_funcs = []
        
        # ----------------------------------------------------------------------------------------
        menu_area = BaseWidget(QHBoxLayout)
        menu_area.setContentsMargins(0, 0, 0, 0)
        
        options_widget = BaseWidget()
        
        options_option = self.IconToolBarOption(options_widget, "☰")
        
        dialog_buttons_widget = BaseWidget(QHBoxLayout)
        for button in self.get_dialog_buttons():
            dialog_buttons_widget.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        delete_button = QPushButton("×")
        delete_button.setProperty("class", "SettingEntryClose")
        delete_button.clicked.connect(self.remove)
        
        menu_area.addWidget(options_option, alignment=Qt.AlignmentFlag.AlignLeft)
        menu_area.addWidget(dialog_buttons_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        menu_area.addWidget(delete_button, alignment=Qt.AlignmentFlag.AlignRight)
                
        # ----------------------------------------------------------------------------------------
        
        simple, extended = self.get_init_text()
        
        edits_area = BaseWidget(QHBoxLayout)
        edits_area.setContentsMargins(0, 0, 0, 0)
        
        self.simple_line_edit = QLineEdit()
        self.simple_line_edit.setText(simple)
        self.simple_line_edit.setPlaceholderText(simple_placeholder)
        
        self.extended_line_edits: list[QLineEdit] = []
        
        self.extended_edits_widget = BaseWidget()
        self.extended_edits_widget.setContentsMargins(0, 0, 0, 0)
        self.extended_edits_widget.setVisible(False)
        
        if extended_placeholders:
            for i, placeholder in enumerate(extended_placeholders):
                line_edit = QLineEdit()
                line_edit.textChanged.connect(self._make_ext_name_changed(i, self.simple_line_edit))
                line_edit.returnPressed.connect(self._make_extended_return_pressed_func(i))
                line_edit.setPlaceholderText(placeholder)
                
                self.extended_edits_widget.addWidget(line_edit)
                self.extended_line_edits.append(line_edit)
            
            edits_area.addWidget(self.extended_edits_widget)
        
        edits_area.addWidget(self.simple_line_edit)
        
        self.nominal_info_widget = BaseWidget()
        
        edits_area.addWidget(self.nominal_info_widget)
        
        # ----------------------------------------------------------------------------------------
        
        self.status_widget = StatusBar()
        
        self.simple_line_edit.textChanged.connect(self.simple_name_empty)
        self.simple_line_edit.textChanged.connect(self._simple_name_changed)
        self.simple_line_edit.returnPressed.connect(lambda: self.i_parent.enter_pressed(Qt.Key.Key_Return, self.entry.id))
        
        # ----------------------------------------------------------------------------------------
        
        if self.extended_line_edits:
            def rb_clicked(s: bool):
                self.simple_line_edit.setVisible(s)
                self.extended_edits_widget.setVisible(not s)
                
                options_option.disappear()
                
                if s:
                    self.simple_line_edit.setFocus()
                    
                    for i in range(len(self.extended_line_edits)):
                        self.status_widget.removeLinient(f"E{i}EmptyNameWarning")
                    
                    self.simple_line_edit.setText(self.simple_line_edit.text())
                    self._simple_name_changed(self.simple_line_edit.text())
                elif self.extended_line_edits:
                    self.extended_line_edits[0].setFocus()
                    
                    for i, le in enumerate(self.extended_line_edits):
                        le.setText(le.text())
                        self.extended_name_empty(i, le.text())
            
            sn_rb = QRadioButton("Short Name")
            ln_rb = QRadioButton("Long Name")
            
            options_widget.addWidget(sn_rb)
            options_widget.addWidget(ln_rb)
            
            sn_rb.setChecked(True)
            
            sn_rb.clicked.connect(lambda s: rb_clicked(s))
            ln_rb.clicked.connect(lambda s: rb_clicked(not s))
            
            for i, line_edit in enumerate(self.extended_line_edits):
                line_edit.textChanged.connect(self._make_ext_name_empty(i))
                line_edit.setText(extended[i])
        else:
            options_option.setDisabled(True)
        
        self.addWidget(menu_area)
        self.addWidget(edits_area)
        self.addWidget(self.status_widget)
        
        self.simple_name_empty(self.simple_line_edit.text())
        
        self.__init = False
    
    def _focusInput(self):
        if self.simple_line_edit.isVisible():
            self.simple_line_edit.setFocus()
        else:
            self.extended_line_edits[0].setFocus()
    
    def _simple_name_changed(self, text: str):
        if not self.__init:
            self.window().saved_state_changed.emit(True)
        
        self.simple_name_changed(text, self.extended_line_edits)
    
    def _make_ext_name_changed(self, index: int, simple_line_edit: QLineEdit):
        def func(text: str):
            if not self.__init:
                self.window().saved_state_changed.emit(True)
            
            self.extended_name_changed(index, text, simple_line_edit)
        
        return func
    
    def _make_ext_name_empty(self, index: int):
        def func(text: str):
            self.extended_name_empty(index, text)
        
        return func
    
    def _make_extended_return_pressed_func(self, index):
        def func():
            if index + 1 < len(self.extended_line_edits):
                self.extended_line_edits[index + 1].setFocus()
            else:
                self.i_parent.enter_pressed(Qt.Key.Key_Return, self.entry.id)
        
        return func
    
    def focusInput(self):
        QTimer.singleShot(100, self._focusInput)
    
    def remove(self):
        self.window().saved_state_changed.emit(True)
        
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
    
    def make_open_dialogs_func(self, title: str, cls: type[BaseSettingDialog], *args):
        def make_dialog():
            return cls(self.i_parent, self.entry.id, title.format(name=self.entry.name.full()), *args)
        
        self.dialog_widget_funcs.append(make_dialog)
        
        return lambda: make_dialog().exec()
    
    def get_init_text(self):
        raise NotImplementedError()
    
    def simple_name_empty(self, text: str):
        if text:
            self.status_widget.removeLinient("EmptyNameWarning")
        else:
            self.status_widget.insertMessage(Status.WARN, 0, "EmptyNameWarning", f"{self.general_entry_name} has no name")
    
    def simple_name_changed(self, text: str, extended_line_edits: tuple[QLineEdit, ...]):
        raise NotImplementedError()
    
    def extended_name_changed(self, index: int, text: str, simple_line_edit: QLineEdit):
        raise NotImplementedError()
    
    def extended_name_empty(self, index: int, text: str):
        raise NotImplementedError()

class BaseSettingWidget(BaseWidget):
    def __init__(self, name: str):
        super().__init__()
        
        self.widgets = {}
        
        self.add_button = QPushButton()
        self.add_button.setText(f"Add {name}")
        self.add_button.clicked.connect(lambda: self.add(focus=True))
        
        self.scroll_widget = BaseScrollWidget()
        self.scroll_widget.setSpacing(20)
        self.scroll_widget.addStretch()
        
        self.addWidget(self.scroll_widget)
        self.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.key_pressed.connect(self.enter_pressed)
        
        for entry in self.get_global().values():
            self.add(entry)
    
    def get_global(self) -> Global:
        raise NotImplementedError()
    
    def get_widget_type(self) -> type[BaseSettingEntry]:
        raise NotImplementedError()
    
    def go_to(self, widget_entry: Entry):
        widget: BaseSettingEntry = next(w for w in self.scroll_widget.getChildren() if w.entry.id == widget_entry.id)
        
        self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(widget.y())
        widget.setFocus()
        
        return widget
    
    def enter_pressed(self, key: int, id: Optional[ID] = None):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.add(focus=True, index=list(self.widgets).index(id) + 1 if id is not None else None)
    
    def add(self, entry: Optional[Entry] = None, index: Optional[int] = None, focus: Optional[bool] = None):
        if focus or index is not None:
            self.window().saved_state_changed.emit(True)
        
        widget_data = self.get_widget_type()
        
        if isinstance(widget_data, tuple):
            widget_type, variables = widget_data
        else:
            widget_type = widget_data
            variables = []
        
        widget = widget_type(self, entry, *variables)
        
        if index is None:
            self.scroll_widget.insertWidget(len(self.widgets), widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
            self.widgets[widget.entry.id] = widget
        else:
            widgets_items = list(self.widgets.items())
            widgets_items.insert(index, (widget.entry.id, widget))
            
            self.widgets.clear()
            self.widgets.update(dict(widgets_items))
            
            self.scroll_widget.insertWidget(index, widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignVCenter)
        
        if focus is not None and focus:
            widget.focusInput()
        
        if entry is None:
            QTimer.singleShot(
                100,
                lambda: self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(widget.y())
            )
        
        return widget.entry
    
    def remove(self, widget: BaseSettingEntry):
        self.scroll_widget.removeWidget(widget)
        widget.deleteLater()
        
        self.widgets.pop(widget.entry.id)
        self.get_global().remove(widget.entry.id)
        
        return widget.entry.id



