
from imports import *

from enum import Enum
import xml.etree.ElementTree as ET
from typing import Literal, TypeVar

# for use by other dependant files
from theme import THEME_MANAGER


_T = TypeVar("_T")


def wrapify_text(text: str, length: int):
    if len(text) > length:
        index = length
        
        if " " in text and (_temp_index := text[:length].rfind(" ")) != -1:
            index = _temp_index
        
        return [text[:index]] + wrapify_text(text[index + (text[index] == " "):], length)
    else:
        return [text]


class Image(QLabel):
    def __init__(self, path: str, parent=None, width: int | None = None, height: int | None = None):
        super().__init__(parent)

        self.setImage(path, width, height)

    def setImage(self, path: str, width: int | None = None, height: int | None = None):
        pixmap = QPixmap(path)
        
        size = pixmap.size()
        
        if width is not None or height is not None:
            if height is not None and width is None and size.height():
                self.setFixedSize(int(height * size.width() / size.height()), height)
            elif width is not None and height is None and size.width():
                self.setFixedSize(width, int(width * size.height() / size.width()))
            else:
                self.setFixedSize(width, height)
        
        self.setScaledContents(True)  # Optional: scale image to fit self
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

class SvgWidget(QWidget):
    """Display an SVG and dynamically edit its element colors."""

    def __init__(self, svg_file, parent=None):
        super().__init__(parent)

        self.svg_file = svg_file

        # Parse and retain the original SVG structure.
        self.tree = ET.parse(svg_file)
        self.root = self.tree.getroot()

        # Keep a pristine copy for resetting colors.
        self.original_xml = ET.tostring(
            self.root, encoding="utf-8"
        )

        self.renderer = QSvgRenderer(self)
        self._load_svg()

        self.setMinimumSize(20, 20)

    def _load_svg(self):
        """Serialize the current SVG and reload the renderer."""
        svg_bytes = ET.tostring(
            self.root, encoding="utf-8",
            xml_declaration=True
        )

        if not self.renderer.load(QByteArray(svg_bytes)):
            raise ValueError("Could not render the SVG file.")

        self.update()

    def element_ids(self):
        """Return IDs of SVG elements."""
        return [
            element.get("id")
            for element in self.root.iter()
            if element.get("id")
        ]

    def set_element_color(
        self, element_id, color, attribute="fill"
    ):
        """Change fill or stroke for one element."""
        if attribute not in ("fill", "stroke"):
            raise ValueError(
                "Attribute must be 'fill' or 'stroke'."
            )

        color = QColor(color)

        if not color.isValid():
            return

        for element in self.root.iter():
            if element.get("id") == element_id:
                element.set(
                    attribute, color.name(QColor.NameFormat.HexArgb)
                    if color.alpha() < 255 else color.name()
                )

                self._load_svg()
                return

        raise ValueError(f"SVG element not found: {element_id}")

    def set_all_colors(self, color):
        """Recolor existing fills and strokes throughout the SVG."""
        color = QColor(color)

        if not color.isValid():
            print("ife")
            return

        color_value = (
            color.name(QColor.NameFormat.HexArgb)
            if color.alpha() < 255 else color.name()
        )

        for element in self.root.iter():
            for attribute in ("fill", "stroke"):
                existing = element.get(attribute)

                # Preserve explicitly transparent components.
                if existing and existing.strip().lower() != "none":
                    element.set(attribute, color_value)

        self._load_svg()

    def reset(self):
        """Restore the original SVG."""
        self.root = ET.fromstring(self.original_xml)
        self._load_svg()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        # Preserve the SVG aspect ratio and center it.
        size = self.renderer.defaultSize()

        if size.width() <= 0 or size.height() <= 0:
            return

        scale = min(
            self.width() / size.width(),
            self.height() / size.height()
        )

        width = size.width() * scale
        height = size.height() * scale

        x = (self.width() - width) / 2
        y = (self.height() - height) / 2

        self.renderer.render(
            painter, QRectF(x, y, width, height)
        )


class Status(Enum):
    MESSAGE = "MESSAGE"
    WARN = "WARN"
    ERROR = "ERROR"


class BaseWidget(QWidget):
    clicked = pySignal(QMouseEvent)
    key_pressed = pySignal(int)
    
    def __init__(self, layout_type: Optional[type[QVBoxLayout] | type[QHBoxLayout]] = None, parent=None):
        super().__init__(parent)
        
        self.layout_type = layout_type or QVBoxLayout
        self._children: list[QObject] = []
        self._property: dict[str, list[str]] = {}
        
        self._init()
    
    def _init(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        self.container = QWidget()
        self.container.setProperty("class", "BaseWidget")
        
        self.container.mousePressEvent = self._mousePressed
        self.container.mouseReleaseEvent = self._mouseRelesed
        self.container.keyPressEvent = self._keyPressed
        
        self.main_layout = self.layout_type(self.container)
        
        layout.addWidget(self.container)
    
    def _mousePressed(self, ev):
        self.container.setProperty("pressed", True)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        
        self.clicked.emit(ev)
    
    def _mouseRelesed(self, ev):
        self.container.setProperty("pressed", False)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
    
    def _keyPressed(self, ev):
        self.key_pressed.emit(ev.key())
    
    @staticmethod
    def static_clearLayout(layout: QHBoxLayout | QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            
            widget = item.widget()
            layout_item = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            elif layout_item is not None:
                BaseWidget.static_clearLayout(layout_item)
    
    @staticmethod
    def static_setStyleProperty(obj: QWidget, name: str | tuple[str] | set[str] | list[str], value: str | tuple[str] | set[str] | list[str]):
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
    def static_getStyleProperty(obj: QWidget, name: str | tuple[str] | set[str] | list[str]):
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
        self.static_clearLayout(self.getLayout())
    
    def deleteLater(self):
        self.clearLayout()
        self.setParent(None)
        
        return super().deleteLater()
    
    def styleSheet(self):
        return self.getWidget().styleSheet()
    
    def setFocus(self):
        self.container.setFocus()
    
    def setSpacing(self, spacing: int):
        self.getLayout().setSpacing(spacing)
    
    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        self.getLayout().setContentsMargins(left, top, right, bottom)
    
    def setStyleSheet(self, stylesheet: str):
        self.getWidget().setStyleSheet(stylesheet)

        for widget in self.getWidgets():
            widget.setStyleSheet(stylesheet)
    
    def setFixedWidth(self, width: int):
        self.getWidget().setFixedWidth(width)

        for widget in self.getWidgets():
            widget.setFixedWidth(width)
    
    def setFixedHeight(self, height: int):
        self.getWidget().setFixedHeight(height)

        for widget in self.getWidgets():
            widget.setFixedHeight(height)

    def setStyleProperty(self, name: str | tuple[str] | set[str] | list[str], value: str | tuple[str] | set[str] | list[str]):
        self.static_setStyleProperty(self, name, value)
    
    def getStyleProperty(self, name: str | tuple[str] | set[str] | list[str]):
        self.static_getStyleProperty(self, name)
    
    def setProperty(self, name: str | None, value: str):
        self.getWidget().setProperty(name, value)

        self._property[name] = value.split()

        for widget in self.getWidgets():
            widget.setProperty(name, value)
    
    def addProperty(self, name: str, value: str):
        if name not in self._property:
            self._property[name] = []
        
        self.setProperty(name, " ".join(self._property[name] + value.split()))
    
    def removeProperty(self, name: str, value: str):
        assert name in self._property
        
        for sub_value in value.split():
            self._property[name].remove(sub_value)
        
        self.setProperty(name, " ".join(self._property[name]))

    def indexWidget(self, index: int):
        return self.getChildren()[index]
    
    def removeWidget(self, a0: Optional[QWidget]):
        self.getLayout().removeWidget(a0)
        
        if a0 is not None:
            self._children.remove(a0)
    
    def popWidget(self, index: int):
        widget = self.getChildren()[index]
        
        self.getLayout().removeWidget(widget)
        widget.deleteLater()
        
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
        self.main_layout = self.layout_type(self.container)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        layout.addWidget(self.scroll_widget)
    
        self._scroll_delay = 0
        self._target_y = 0
        self._scroll_start = None
        self._focus_widget = None
        self._scroll_delta = None
        
        self.scroll_delay = 10
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._scrolling)
    
    def _scrolling(self):
        self._scroll_start += self._scroll_delta
        self.scroll_widget.verticalScrollBar().setValue(int(self._scroll_start))
        
        self.update()
        
        self._scroll_delay += 1
        if (self._target_y <= self._scroll_start - 100 and self._scroll_delta > 0) or (self._target_y >= self._scroll_start - 150 and self._scroll_delta < 0) or self._scroll_start - 50 <= self._target_y <= self._scroll_start + 50:
            self._scroll_delay = 0
            self.scroll_delay = 10
            self.scroll_timer.stop()
            
            self._focus_widget = None
            self._scroll_delta = None    
    
    def _scroll_to(self, widget: QWidget, is_first: bool):
        widget.ensurePolished()
        
        self._focus_widget = widget
        self._scroll_start = self.scroll_widget.verticalScrollBar().value()
        self._target_y = widget.y()
        
        if is_first:
            self.scroll_delay = 1
        
        self._scroll_delta = (widget.y() - self.scroll_widget.verticalScrollBar().value()) / self.scroll_delay
        
        self.scroll_timer.stop()
        self.scroll_timer.start(1)
    
    def scroll_to(self, widget: QWidget, msec: Optional[int] = None):
        QTimer.singleShot(
            msec or 0,
            lambda: self._scroll_to(widget, self.indexOf(widget) == 0)
        )
    
    def setAlignment(self, alignment: Qt.AlignmentFlag):
        self.getLayout().setAlignment(alignment)
    
    def setFixedWidth(self, width):
        self.getScrollWidget().setFixedWidth(width)
    
    def setFixedHeight(self, height):
        self.getScrollWidget().setFixedHeight(height)
    
    def getWidgets(self):
        return [self.scroll_widget]

    def getScrollWidget(self):
        return self.scroll_widget

class BaseDialogWidget(QDialog):
    def __init__(self, title: str, widget_type: type[BaseWidget | BaseScrollWidget], layout_type: type[QHBoxLayout | QVBoxLayout] = None, parent=None):
        super().__init__(parent=parent)
        
        self.widget = widget_type(layout_type)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setLayout(layout)
        
        layout.addWidget(self.widget)
        
        self.setWindowTitle(title)
        self.setContentsMargins(0, 0, 0, 0)
    
    def scroll_to(self, widget: QWidget | BaseWidget, msec: int):
        if isinstance(self.widget, BaseScrollWidget):
            self.widget.scroll_to(widget, msec)
    
    def setSpacing(self, spacing: int):
        self.widget.setSpacing(spacing)
    
    def setContentsMargins(self, left: int, top: int, right: int, bottom: int):
        self.widget.setContentsMargins(left, top, right, bottom)
    
    def setStyleSheet(self, stylesheet: str):
        self.widget.setStyleSheet(stylesheet)
    
    def setProperty(self, name: str | None, value: str):
        self.widget.setProperty(name, value)
    
    def setFixedWidth(self, width: int):
        super().setFixedWidth(width)
        
        self.widget.setFixedWidth(width)
    
    def setFixedHeight(self, height: int):
        super().setFixedHeight(height)
        
        self.widget.setFixedHeight(height)
    
    def addWidget(self, widget: QWidget, stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        self.widget.addWidget(widget, stretch, alignment)
    
    def insertWidget(self, index: int, widget: Optional[QWidget], stretch: Optional[int] = None, alignment: Optional[Qt.AlignmentFlag] = None):
        self.widget.insertWidget(index, widget, stretch, alignment)
    
    def removeWidget(self, widget: QWidget):
        self.widget.removeWidget(widget)
    
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
    
    def setAlignment(self, alignment):
        for widget in self.widgets:
            widget.setAlignment(alignment)
        
        return super().setAlignment(alignment)
    
    def setHorizontalSpacing(self, spacing: int):
        for widget in self.widgets:
            widget.setSpacing(spacing)
    
    def setVerticalSpacing(self, spacing: int):
        self.setSpacing(spacing)
    
    def addSpacing(self, a0: int):
        self.widgets[-1].addSpacing(a0)
    
    def addStretch(self, stretch: Optional[int] = None):
        self.widgets[-1].addStretch(stretch)
    
    def addWidget(self, widget, stretch = None, alignment = None):
        if self.widget_count % self.row_max == 0:
            bg_widget = BaseWidget(QHBoxLayout)
            bg_widget.setContentsMargins(0, 0, 0, 0)
            
            super().addWidget(bg_widget)
            
            self.widgets.append(bg_widget)
        
        self.widgets[-1].insertWidget(len(self.widgets[-1].getChildren()), widget, stretch, alignment)
        self.widget_count += 1
    
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

class LabeledField(BaseWidget):
    def __init__(
        self,
        title: str,
        inner_widget: BaseWidget,
        width_policy: QSizePolicy.Policy | None = None,
        height_policy: QSizePolicy.Policy | None = None,
    ):
        super().__init__()
        
        self.inner_widget = inner_widget

        if width_policy or height_policy:
            self.setSizePolicy(
                width_policy or QSizePolicy.Policy.Preferred,
                height_policy or QSizePolicy.Policy.Preferred,
            )
        
        self.label = QLabel(title, self)
        self.label.setProperty("class", "LabeledContainerTitle")
        
        self.title_area = BaseWidget(QHBoxLayout)
        self.title_area.setContentsMargins(0, 0, 0, 0)
        
        self.title_area.addWidget(self.label)
        self.title_area.addStretch()
        
        self.setProperty("class", "LabeledContainer")
        self.setContentsMargins(8, 3, 8, 8)
        self.setSpacing(6)
        
        self.addWidget(self.title_area)
        self.addWidget(self.inner_widget)
    
    def setTitle(self, title: str):
        self.label.setText(title)

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

class SearchEdit(QFrame):
    class SearchEditOption(BaseWidget):
        def __init__(self, se: "SearchEdit", data_point: _T, style: str | list | tuple, info: tuple[Optional[str], Optional[str], Optional[str], Optional[str]]):
            super().__init__(QHBoxLayout)
            
            self.setProperty("class", "SearchOptions")
            self.setContentsMargins(10, 10, 10, 10)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            
            self.se = se
            self.data_point = data_point
            self.main_text, self.right_text, self.bottom_text, self.end_text = info
            
            if isinstance(style, str):
                self.m_style = self.b_style = self.r_style = self.e_style = style
            elif isinstance(style, (list, tuple)):
                for i, (x, s_name) in enumerate(((self.main_text, "m_style"), (self.bottom_text, "b_style"), (self.right_text, "r_style"), (self.end_text, "e_style"))):
                    if x is not None:
                        setattr(self, s_name, style[i])
            else:
                raise TypeError("Style is of type:", type(style))
            
            assert self.m_style is not None
            
            self.main_label = QLabel() ; self.main_label.setMinimumHeight(25)
            self.bottom_label = QLabel() ; self.main_label.setMinimumHeight(17)
            self.right_label = QLabel() ; self.main_label.setMinimumHeight(19)
            self.end_label = QLabel() ; self.main_label.setMinimumHeight(15)
            
            self.metrics = QFontMetrics(self.main_label.font())
            
            w1 = BaseWidget()
            w1.setContentsMargins(0, 0, 0, 0)
            w1.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
            
            main_right_widget = BaseWidget(QHBoxLayout)
            main_right_widget.setSpacing(10)
            main_right_widget.setContentsMargins(0, 0, 0, 0)
            
            main_right_widget.addWidget(self.main_label)
            main_right_widget.addWidget(self.right_label)
            
            w1.addWidget(main_right_widget)
            w1.addWidget(self.bottom_label, alignment=Qt.AlignmentFlag.AlignBottom)
            
            self.addWidget(w1)
            self.addWidget(self.end_label, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.clicked.connect(self.selected)
        
        def update_highlights(self, score_highlight_data: tuple[float | Literal[-1], tuple[list[int], list[int], list[int], list[int]]]):
            score, (main_hi, right_hi, bottom_hi, end_hi) = score_highlight_data
            
            if score != -1:
                if not self.isVisible():
                    self.setVisible(True)
                
                self.main_label.setText("".join([(f"<span style='font-size: 27px; font-weight: 500; {f"{self.m_style}" if i in main_hi else ""}'>{c}</span>" if c != "■" else "<br>") for i, c in enumerate("■".join(wrapify_text(self.main_text, 30)))]))
                self.right_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-black-0.588__minimum}")}; font-size: 19px; font-weight: 300; {f"{self.r_style}" if i in right_hi else ""}'>{c}</span>" for i, c in enumerate(self.right_text)]) if self.right_text else "")
                self.bottom_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-black-0.588__minimum}")}; font-size: 15px; font-weight: 500; {f"{self.b_style}" if i in bottom_hi else ""}'>{c}</span>" for i, c in enumerate(self.bottom_text)]) if self.bottom_text else "")
                self.end_label.setText("".join([f"<span style='color: {THEME_MANAGER.process_stylesheet("{interpolate-black-0.392__minimum}")}; font-size: 13px; font-weight: 300; {f"{self.e_style}" if i in end_hi else ""}'>{c}</span>" for i, c in enumerate(self.end_text)]) if self.end_text else "")
            else:
                self.setVisible(False)
        
        def selected(self):
            self.se.hide()
            
            self.se.search_le.blockSignals(True)
            self.se.search_le.clear()
            self.se.search_le.blockSignals(False)
            
            if self.se.goto_search_callback:
                self.se.goto_search_callback(self.data_point)

    DEBOUNCE_MS = 120
    MAX_RESULTS = math.inf

    def __init__(
            self,
            get_search_scope_callback: Callable[
                [], list[tuple[_T, str, tuple[Optional[str], Optional[str], Optional[str]], list[Optional[str]]]]
            ],
            goto_search_callback: Optional[Callable[[_T], None]] = None
        ):
        super().__init__(None)

        self.get_search_scope_callback = get_search_scope_callback
        self.goto_search_callback = goto_search_callback

        self.setWindowFlags(Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.Box)
        self.setProperty("class", "SearchEdit")
        self.setFixedWidth(500)

        self.ref_data = {}
        self._updating = False

        # ---------- Layout ----------
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("Search")
        self.search_le.setFixedWidth(496)
        self.search_le.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        
        self.main_layout.addWidget(self.search_le, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.options_widget_wrapper = BaseScrollWidget()
        
        self.options_widget = BaseWidget()
        self.options_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        self.options_widget_wrapper.addWidget(self.options_widget)
        self.options_widget_wrapper.addStretch()
        
        self.options_widget_wrapper.setFixedWidth(496)
        self.options_widget_wrapper.setFixedHeight(220)
        self.options_widget_wrapper.setVisible(False)

        self.main_layout.addWidget(self.options_widget_wrapper, alignment=Qt.AlignmentFlag.AlignTop)

        # ---------- Debounce ----------
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._run_search)
        
        self.search_le.textEdited.connect(self._on_text_edited)
    
    def show(self):
        self.search_le.blockSignals(True)
        self.search_le.clear()
        self.search_le.blockSignals(False)

        self._run_search()
        super().show()
        self.search_le.setFocus()
        
    def _on_text_edited(self, _):
        self._search_timer.start(self.DEBOUNCE_MS)

    def _run_search(self):
        if self._updating:
            return
        
        self._updating = True
        text = self.search_le.text().strip()
        
        if not text:
            self.options_widget_wrapper.setVisible(False)
            self._updating = False
            
            return
        
        score_data = sorted(
            [
                (
                    data_point,
                    (name, right, bottom, end),
                    self._score(text, name, (right, bottom, end), bg)
                )
                for data_point, name, (right, bottom, end), bg
                in self.get_search_scope_callback()
            ],
            key=lambda x: x[2][0],
            reverse=True
        )
        
        ref_data_copy = self.ref_data.copy()
        l_ref_data = list(ref_data_copy)
        
        self.ref_data.clear()
        
        added = 0
        for index, (data_point, info, score_highlight_data) in enumerate(score_data):
            added += 1
            
            if data_point not in ref_data_copy:
                widget = self.SearchEditOption(self, data_point, f"color: {THEME_MANAGER.pallete_get("fg1")}; font-weight: 900;", info)
                
                self.options_widget.addWidget(widget)
            else:
                widget = ref_data_copy[data_point]
                
                if index != l_ref_data.index(data_point):
                    self.options_widget.insertWidget(index, widget)
            
            widget.update_highlights(score_highlight_data)
            self.ref_data[data_point] = widget
            
            if added >= self.MAX_RESULTS:
                break
        
        for dp, widg in ref_data_copy.items():
            if dp not in self.ref_data:
                self.options_widget.removeWidget(widg)
        
        # added = 0
        # for data_point, (name, right, bottom, end), (score, indices) in score_data:
        #     if score == -1 or added >= self.MAX_RESULTS:
        #         continue
            
        #     label = QLabel(
        #         self._stylize_text_indices(
        #             name,
        #             f"color: {THEME_MANAGER.pallete_get("fg1")}; font-weight: bold;",
        #             right,
        #             bottom,
        #             end,
        #             indices
        #         )
        #     )
        #     label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        #     label.setProperty("class", "SearchOptions")
        #     label.mousePressEvent = self._make_option_clicked_func(data_point)
            
        #     self.options_widget.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)
        #     added += 1
        
        self.options_widget_wrapper.setVisible(added > 0)
        
        self._updating = False
    
    def _score(
        self,
        text: str,
        potential_match: str,
        extra_text_data: Optional[tuple[Optional[str], Optional[str], Optional[str]]] = None,
        backgrounds_texts: Optional[list[Optional[str]]] = None
    ) -> tuple[float | Literal[-1], tuple[list[int], list[int], list[int], list[int]]]:
        l_text = text.lower()
        l_target = potential_match.lower()
        
        space_amt = 0
        additions = 0
        
        text_len = len(l_text)
        target_len = len(l_target)
        
        index = 0
        
        bg_data = []
        
        score_indices = []
        right_indices = []
        bottom_indices = []
        end_indices = []
        
        right_score = -1
        bottom_score = -1
        end_score = -1
        
        if extra_text_data:
            right_text, bottom_text, end_text = extra_text_data
            
            if right_text:
                right_score, right_indices = self._score(text, right_text)
                right_indices = right_indices[0]
            if bottom_text:
                bottom_score, bottom_indices = self._score(text, bottom_text)
                bottom_indices = bottom_indices[0]
            if end_text:
                end_score, end_indices = self._score(text, end_text)
                end_indices = end_indices[0]
        
        if backgrounds_texts:
            bg_data = [self._score(text, bg_text)[0] for bg_text in backgrounds_texts if bg_text is not None]
        
        for i, c in enumerate(l_text):
            f_index = l_target[index:].find(c)
            
            if f_index != -1 and text_len <= target_len:
                space_amt += f_index
                index += f_index + 1
                
                additions += text[i] == potential_match[index - 1]
                additions += f_index == 0
                
                score_indices.append(index - 1)
                
                continue
            break
        else:
            return (text_len / (target_len + space_amt)) + additions, (score_indices, [], [], [])
        
        if bottom_score == -1 and right_score != -1:
            return right_score / 20, ([], right_indices, [], [])
        elif right_score == -1 and bottom_score != -1:
            return bottom_score / 20, ([], [], bottom_indices, [])
        elif right_score != -1 and bottom_score != -1:
            return (right_score + bottom_score) / 20, ([], right_indices, bottom_indices, [])
        elif end_score != -1:
            return end_score / 20, ([], [], [], end_indices)
        elif bg_data:
            for bg_score in bg_data:
                if bg_score != -1:
                    return bg_score / 20, ([], [], [], [])
        
        return -1, ([], [], [], [])


class SearchBar(BaseWidget):
    def __init__(self, get_search_scope_func: Callable, goto_search_func: Callable):
        super().__init__()
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.search_edit = SearchEdit(get_search_scope_func, goto_search_func)
        
        self.search_pb = QPushButton()
        self.search_pb.setFixedWidth(self.search_edit.width())
        self.search_pb.setProperty("class", "SearchPB")
        self.search_pb.clicked.connect(self._open_search_edit)
        
        self.addWidget(self.search_pb)
    
    def setPrompt(self, text: str):
        self.search_pb.setText(text)
    
    def _open_search_edit(self):
        self.search_edit.move(self.mapToGlobal(QPoint(self.search_pb.x(), self.search_pb.y())))
        self.search_edit.search_le.setFocus()
        
        self.search_edit.show()


class SettingsScreen[_T](BaseWidget):
    def __init__(
            self,
            entry: _T,
            stack: QStackedWidget,
            parent_entry: BaseSettingEntry,
            i_parent: BaseSettingWidget[_T]
        ):
        super().__init__()

        self.__init = True
        
        self.entry = entry
        self.stack = stack
        self._parent = parent_entry
        self.i_parent = i_parent

        # Heading section
        go_back_button = BaseWidget()
        go_back_button.clicked.connect(lambda _: self.go_back())
        go_back_button.setProperty("class", "SpecialBG2Hover BorderRadiused")
        go_back_button.setContentsMargins(10, 10, 10, 10)
        go_back_button.addWidget(svg := SvgWidget("src/images/svg/direction.svg")) ; svg.set_all_colors(THEME_MANAGER.process_stylesheet("{text}"))

        top_widget = BaseWidget(QHBoxLayout)
        top_widget.addWidget(go_back_button)

        # Name Inputs
        simple, extended = self._parent.get_init_text()
        
        edits_area = BaseWidget(QHBoxLayout)
        edits_area.setProperty("class", "NoBackground")
        edits_area.setContentsMargins(0, 0, 0, 0)
        
        validator = QRegularExpressionValidator(QRegularExpression("[^■]+"))
        
        self.simple_line_edit = QLineEdit()
        self.simple_line_edit.setProperty("class", "SettingEntryNameEdit")
        self.simple_line_edit.setText(simple)
        self.simple_line_edit.setValidator(validator)
        self.simple_line_edit.setPlaceholderText(self._parent.simple_placeholder)
        
        self.extended_line_edits: list[QLineEdit] = []
        
        self.extended_edits_widget = BaseWidget()
        self.extended_edits_widget.setContentsMargins(0, 0, 0, 0)
        self.extended_edits_widget.setVisible(False)
        
        edits_area.addWidget(self.simple_line_edit)
        
        # ----------------------------------------------------------------------------------------
        
        self.status_widget = StatusBar()
        
        self.simple_line_edit.textChanged.connect(self._parent.simple_name_empty)
        self.simple_line_edit.textChanged.connect(self.simple_name_changed)
        self.simple_line_edit.returnPressed.connect(lambda: self.i_parent.enter_pressed(Qt.Key.Key_Return, self.entry.id))
        
        # ----------------------------------------------------------------------------------------
        self.edit_fmt_state = False
        self.simple_display_widget = None
        self.extended_display_widget = None
        self.toogle_name_format_button_widget = None
        
        if self._parent.extended_placeholders:
            for i, placeholder in enumerate(self._parent.extended_placeholders):
                line_edit = QLineEdit()
                line_edit.setProperty("class", "SettingEntryNameEdit")
                line_edit.setValidator(validator)
                line_edit.textChanged.connect(self._make_ext_name_changed(i, self.simple_line_edit))
                line_edit.returnPressed.connect(self._make_extended_return_pressed_func(i))
                line_edit.setPlaceholderText(placeholder)
                
                self.extended_edits_widget.addWidget(line_edit)
                self.extended_line_edits.append(line_edit)
            
            edits_area.addWidget(self.extended_edits_widget)
            
            self.toogle_name_format_button_widget = BaseWidget()
            self.toogle_name_format_button_widget.setProperty("class", "SpecialBG2Hover BorderRadiused")
            self.toogle_name_format_button_widget.setContentsMargins(10, 10, 10, 10)
            
            self.simple_display_widget = SvgWidget("src/images/svg/text-cursor-input.svg")
            self.extended_display_widget = SvgWidget("src/images/svg/list.svg")
            
            self.simple_display_widget.set_all_colors(THEME_MANAGER.process_stylesheet("{text}"))
            self.extended_display_widget.set_all_colors(THEME_MANAGER.process_stylesheet("{text}"))
            
            self.toogle_name_format_button_widget.addWidget(self.simple_display_widget)
            self.toogle_name_format_button_widget.addWidget(self.extended_display_widget)
            
            self.toogle_name_format_button_widget.clicked.connect(lambda _: self.toogle_name_format())

            for i, line_edit in enumerate(self.extended_line_edits):
                line_edit.textChanged.connect(self._make_ext_name_empty(i))
                line_edit.setText(extended[i])
        
        name_widget = BaseWidget()
        name_widget.setProperty("class", "BG1 BorderRadiused")
        name_widget.setContentsMargins(15, 15, 15, 15)
        
        info_area_widget = BaseWidget(QHBoxLayout)
        info_area_widget.setProperty("class", "NoBackground")

        info_area_widget.addWidget(QLabel(f"<b>Edit {self._parent.general_entry_name} Name</b>"), alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        info_area_widget.addWidget(self.status_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        if self.toogle_name_format_button_widget:
            info_area_widget.addWidget(self.toogle_name_format_button_widget, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)

        name_widget.addWidget(info_area_widget)
        name_widget.addWidget(edits_area)

        # Custom Settings
        custom_settings_widget = BaseWidget()
        custom_settings_widget.setSpacing(10)
        custom_settings_widget.setContentsMargins(0, 0, 0, 0)

        custom_settings_data = list(self.get_custom_settings_data())
        
        for name, widget, alignment in custom_settings_data:
            widg = BaseWidget() ; widg.addWidget(widget, alignment=alignment)
            custom_settings_widget.addWidget(LabeledField(name, widg, width_policy=QSizePolicy.Policy.Minimum))
        
        _body_widget = BaseWidget()
        _body_widget.setSpacing(10)
        _body_widget.setContentsMargins(0, 0, 0, 0)
        
        _body_widget.addWidget(name_widget)
        _body_widget.addWidget(custom_settings_widget)
        _body_widget.addStretch()
        
        body_widget = BaseScrollWidget() ; body_widget.addWidget(_body_widget)
        body_widget.setContentsMargins(0, 0, 15, 0)
        body_widget.setProperty("class", "Borderless")
        
        self.i_parent.add_buttons_widget.setVisible(False)
        
        self.focusInput()

        self.custom_settings_widgets = {n: w for n, w, _ in custom_settings_data}
        
        self.addWidget(top_widget, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.addWidget(body_widget)
        
        self.toogle_name_format()
        
        self._parent.on_settings_open(self)
        
        self.__init = False
        
        shortcut = QShortcut(QKeySequence("Esc"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.go_back)
    
    def _make_ext_name_changed(self, index: int, simple_line_edit: QLineEdit):
        def func(text: str):
            self._parent.extended_name_changed(index, text, simple_line_edit)
            self._parent.set_name_text()

            if not self.__init:
                self.window().saved_state_changed.emit(True)

        return func

    def _make_ext_name_empty(self, index: int):
        def func(text: str):
            self._parent.extended_name_empty(index, text)

        return func

    def _make_extended_return_pressed_func(self, index):
        def func():
            self.extended_line_edits[(index + 1) % len(self.extended_line_edits)].setFocus()

        return func
    
    def _focusInput(self):
        if self.simple_line_edit.isVisible():
            self.simple_line_edit.setFocus()
        else:
            self.extended_line_edits[0].setFocus()
    
    def simple_name_changed(self, text: str):
        self._parent.simple_name_changed(text, self.extended_line_edits)
        self._parent.set_name_text()

        if not self.__init:
            self.i_parent.window().saved_state_changed.emit(True)
    
    def simple_name_empty(self, text: str):
        self._parent.simple_name_empty(text)
    
    def focusInput(self):
        QTimer.singleShot(100, self._focusInput)
    
    def toogle_name_format(self, update: bool = True):
        if self.extended_line_edits:
            self.edit_fmt_state = not self.edit_fmt_state
            
            self.simple_line_edit.setVisible(self.edit_fmt_state)
            self.simple_display_widget.setVisible(not self.edit_fmt_state)
            self.extended_edits_widget.setVisible(not self.edit_fmt_state)
            self.extended_display_widget.setVisible(self.edit_fmt_state)
            
            if not self.__init:
                if self.edit_fmt_state:
                    self.simple_line_edit.setFocus()
                    
                    for i in range(len(self.extended_line_edits)):
                        self.status_widget.removeLinient(f"E{i}EmptyNameWarning")
                    
                    self.simple_line_edit.setText(self.simple_line_edit.text())
                    self.simple_name_changed(self.simple_line_edit.text())
                else:
                    self.extended_line_edits[0].setFocus()
                    
                    for i, le in enumerate(self.extended_line_edits):
                        le.setText(le.text())
                        self._parent.extended_name_empty(i, le.text())
    
    def get_custom_settings_data(self):
        for name, option_data in self._parent.custom_settings_format:
            if len(option_data) == 2:
                widget_info, alignment = option_data

                widget = widget_info()
            else:
                *widget_info, alignment = option_data

                if len(widget_info) == 2:
                    cls, variables = widget_info
                else:
                    raise TypeError(f"Expected dialog info of length 2 but got length: {len(widget_info)}")
                
                widget = cls(self._parent, self.entry.id, *variables)
            
            yield (name.format(name=self.entry.name.full()), widget, alignment)
    
    def get_setting_widget(self, widget_type: type):
        return next(w for w in self.custom_settings_widgets.values() if isinstance(w, widget_type))
    
    def go_back(self):
        self.i_parent.add_buttons_widget.setVisible(True)

        self.stack.setCurrentWidget(self.i_parent.scroll_widget)
        self.stack.removeWidget(self)
        self.deleteLater()

        self._parent.settings_screen = None

class BaseSettingEntry[_T](BaseWidget):
    def __init__(
            self,
            i_parent: "BaseSettingWidget[_T]",
            general_entry_name: str,
            extended_placeholders: list[str],
            custom_settings_format: list[tuple[str, tuple[type[BaseWidget], tuple, Qt.AlignmentFlag] | tuple[QWidget, Qt.AlignmentFlag]]],
            entry: Optional[_T],
            stack: QStackedWidget
        ):
        super().__init__()
        
        self.__init = True
        
        self.setProperty("class", "SettingEntry")
        self.setContentsMargins(10, 10, 10, 10)
        
        self.entry = entry or self.new()
        self.id = self.entry.id
        self.i_parent = i_parent
        self.stack = stack

        self.settings_screen = None

        # These variables are not referenced in this class but are used in the settings screen
        self.general_entry_name = general_entry_name
        self.extended_placeholders = extended_placeholders
        self.custom_settings_format = custom_settings_format
        self.simple_placeholder = f"Enter {self.general_entry_name} Name"

        # ----------------------------------------------------------------------------------------
        
        delete_button = QPushButton("×")
        delete_button.setProperty("class", "SettingEntryClose")
        delete_button.clicked.connect(self.remove)
        
        # ----------------------------------------------------------------------------------------
        
        info_area = BaseWidget(QHBoxLayout)
        info_area.setSpacing(15)
        info_area.setContentsMargins(0, 0, 0, 0)
        info_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        info_area.setProperty("class", "NoBackground")

        self.name_label = QLabel()

        name_widget = BaseWidget() ; name_widget.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        name_widget.setProperty("class", "NoBackground")

        info_widget = BaseWidget()
        info_widget.setProperty("class", "NoBackground")

        info_area.addWidget(name_widget, stretch=55)
        info_area.addWidget(info_widget, stretch=45)
        
        # ----------------------------------------------------------------------------------------
        
        self.status_bar = StatusBar()
        self.status_bar.setProperty("class", "NoBackground")

        # ----------------------------------------------------------------------------------------
        
        self.setFixedHeight(200)
        self.addWidget(delete_button, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.addWidget(info_area, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.addWidget(self.status_bar, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        info_area.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        self.clicked.connect(lambda _: self.open_settings())
        
        self.set_name_text()

        self.__init = False
    
    def _focusInput(self):
        if self.simple_line_edit.isVisible():
            self.simple_line_edit.setFocus()
        else:
            self.extended_line_edits[0].setFocus()
    
    def _simple_name_changed(self, text: str):
        if self.settings_screen:
            self.settings_screen.simple_name_changed(text)
    
    def _make_ext_name_changed(self, index: int, simple_line_edit: QLineEdit):
        def func(text: str):
            self.extended_name_changed(index, text, simple_line_edit)
            
            if not self.__init:
                self.window().saved_state_changed.emit(True)
        
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
    
    def on_settings_open(self, settings_screen: SettingsScreen):
        pass
    
    def set_name_text(self):
        self.name_label.setText(
            f"<span style='font-weight: bold; font-size: 55px;'>{"<br>".join(wrapify_text(self.get_repr_text(), 50))}</span>"
            if self.get_repr_text() else
            "<i style='font-size: 55px'>NO NAME</i>"
        )
    
    def new(self) -> _T:
        raise NotImplementedError()
    
    def focusInput(self):
        QTimer.singleShot(100, self._focusInput)

    def open_settings(self):
        self.settings_screen = SettingsScreen(self.entry, self.stack, self, self.i_parent)
        
        self.stack.addWidget(self.settings_screen)
        self.stack.setCurrentWidget(self.settings_screen)
        
        return self.settings_screen
    
    def remove(self):
        self.i_parent.remove(self)
        self.i_parent.window().saved_state_changed.emit(True)
    
    def get_init_text(self) -> tuple[str, list[str]]:
        raise NotImplementedError()

    def get_repr_text(self) -> str:
        raise NotImplementedError()

    def toogle_name_format(self):
        if self.extended_line_edits:
            for c in self.toogle_name_format_button_widget.getChildren() + [self.simple_line_edit, self.extended_edits_widget]:
                c.setVisible(not c.isVisible())
            
            is_simple = self.simple_line_edit.isVisible()
            
            if is_simple:
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
    
    def simple_name_empty(self, text: str):
        if self.settings_screen:
            if text:
                self.settings_screen.status_widget.removeLinient("EmptyNameWarning")
            else:
                self.settings_screen.status_widget.insertMessage(Status.WARN, 0, "EmptyNameWarning", f"{self.general_entry_name} has no name")
    
    def simple_name_changed(self, text: str, extended_line_edits: tuple[QLineEdit, ...]):
        raise NotImplementedError()
    
    def extended_name_changed(self, index: int, text: str, simple_line_edit: QLineEdit):
        raise NotImplementedError()
    
    def extended_name_empty(self, index: int, text: str):
        raise NotImplementedError()

class BaseSettingWidget[_T](BaseWidget):
    def __init__(self, names: list[str]):
        super().__init__()

        self.names = names

        self.widgets: dict[ID, BaseSettingEntry[_T]] = {}

        self.stack = QStackedWidget()
        
        self.scroll_widget = BaseScrollWidget()
        self.scroll_widget.setSpacing(20)
        self.scroll_widget.addStretch()

        self.stack.addWidget(self.scroll_widget)
        
        self.add_buttons_widget = BaseWidget(QHBoxLayout)
        self.add_buttons_widget.addStretch()
        
        self.addWidget(self.stack)
        self.addWidget(self.add_buttons_widget)
        
        def _make_add_button_func(index: int):
            def func():
                self.add(button_index=index, focus=True)
            
            return func
        
        for i, name in enumerate(names):
            add_button = QPushButton()
            add_button.setText(f"Add {name}")
            add_button.clicked.connect(_make_add_button_func(i))
            
            self.add_buttons_widget.addWidget(add_button)
        
        self.key_pressed.connect(self.enter_pressed)
        
        self.init_saved_variables()
    
    def init_saved_variables(self):
        global_variables = self.get_global()
        
        if isinstance(global_variables, Global):
            for entry in global_variables.values():
                self.add(entry)
        elif isinstance(global_variables, tuple):
            for i, gv in enumerate(global_variables):
                for entry in gv.values():
                    self.add(entry, button_index=i)
    
    def get_global(self) -> Global | tuple[Global, ...]:
        raise NotImplementedError()
    
    def get_widget_type(self, *args) -> type[BaseSettingEntry[_T]]:  # It's variable is *args because in implementation it has a variable amount of arguments (one or None)
        raise NotImplementedError()
    
    def go_to(self, widget_entry: _T):
        widget: BaseSettingEntry[_T] = next(w for w in self.scroll_widget.getChildren() if w.entry.id == widget_entry.id)
        
        self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(widget.y())
        widget.setFocus()
        
        return widget
    
    def enter_pressed(self, key: int, id: Optional[ID] = None):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.add(focus=True, index=list(self.widgets).index(id) + 1 if id is not None else None)
    
    def add(self, entry: Optional[_T] = None, index: Optional[int] = None, focus: Optional[bool] = None, button_index: Optional[int] = None):
        if button_index is not None:
            widget_data = self.get_widget_type(button_index)
        else:
            widget_data = self.get_widget_type()
        
        if isinstance(widget_data, tuple):
            widget_type, variables = widget_data
        else:
            widget_type = widget_data
            variables = []
        
        widget = widget_type(self, entry, *variables, stack=self.stack)
        
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
            widget.setFocus()
        
        elif entry is None:
            QTimer.singleShot(
                100,
                lambda: self.scroll_widget.getScrollWidget().verticalScrollBar().setValue(widget.y())
            )
        
        return widget.entry
    
    def remove(self, widget: BaseSettingEntry[_T]):
        self.scroll_widget.removeWidget(widget)
        widget.deleteLater()
        
        self.widgets.pop(widget.entry.id)
        
        global_variables = self.get_global()
        
        if isinstance(global_variables, Global):
            global_variables.remove(widget.entry.id)
        elif isinstance(global_variables, tuple):
            for gv in global_variables:
                if widget.entry.id in gv:
                    gv.remove(widget.entry.id)
                    break
        
        return widget.entry.id


class BaseSelectionList[_T](BaseScrollWidget):
    def __init__(self, parent: BaseSettingEntry, id: ID, selected_items: list[tuple[ID, _T | tuple[_T, int]]], content_scope: dict[ID, _T | tuple[_T, int]]):
        super().__init__()
        
        self.id = id
        self._parent = parent
        self.setFixedHeight(400)
        
        self.widgets: dict[ID, _BaseSelectObjectWidget] = {}
        
        selected_ids = []
        
        # Add selected items
        for item_id, item_data in selected_items:
            if isinstance(item_data, tuple):
                item, index = item_data
            else:
                item = item_data
                index = None
            
            selected_ids.append(item_id)
            self.addWidget(SL_SelectedWidget(self, item_id, item.name.full(), self.item_removed, self.item_selected, self._parent.window(), index))
        
        # Add unselected items
        for item_id, item_data in content_scope.items():
            if isinstance(item_data, tuple):
                item, index = item_data
            else:
                item = item_data
                index = None
            
            if item_id not in selected_ids:
                self.addWidget(SL_UnSelectedWidget(self, item_id, item.name.full(), self.item_selected, self.item_removed, self._parent.window(), index))
        
        self.addStretch()
    
    def addWidget(self, widget, stretch = None, alignment = None):
        self.widgets[widget.id] = widget
        
        return super().addWidget(widget, stretch, alignment)
    
    def insertWidget(self, index, widget, stretch = None, alignment = None):
        self.widgets[widget.id] = widget
        
        return super().insertWidget(index, widget, stretch, alignment)
    
    def removeWidget(self, widget: _BaseSelectObjectWidget):
        self.widgets.pop(widget.id)
        
        r = super().removeWidget(widget)
        widget.deleteLater()
        
        return r
    
    def item_removed(self, id: ID, index: int):
        raise NotImplementedError()
    
    def item_selected(self, id: ID, index: int):
        raise NotImplementedError()
    
    def go_to(self, widget: "SL_SelectedWidget"):
        def func():
            self.scroll_to(widget, 100)
            
            widget.setFocus()
        
        QTimer.singleShot(200, func)


class _BaseSelectObjectWidget(BaseWidget):
    def __init__(self, parent: BaseSelectionList, id: ID, text: str, on_remove: Callable[[ID, int], None], on_opp_remove: Callable[[ID], None], window: QMainWindow, index: int = None):
        super().__init__(QHBoxLayout)
        
        self.id = id
        self.text = text
        self._parent = parent
        self._window = window
        self.index = index
        
        self.on_remove = on_remove
        self.on_opp_remove = on_opp_remove
        
        metrics = QFontMetrics(self.font())
        label = QLabel(metrics.elidedText(self.text, Qt.TextElideMode.ElideRight, 200))
        label.setFont(self.font())
        label.setToolTip(self.text)
        
        self.addWidget(label)
        self.addStretch()
        
        self.clicked.connect(self.sl_clicked)
    
    def sl_clicked(self, a0):
        self._parent.removeWidget(self)
        
        insert_index, widget = self.get_new_widget_index()
        
        self._parent.insertWidget(insert_index, widget)
        
        self.on_remove(self.id, insert_index)
        
        self._window.window().saved_state_changed.emit(True)
    
    def get_new_widget_index(self) -> tuple[int, "_BaseSelectObjectWidget"]:
        raise NotImplementedError()

class SL_SelectedWidget(_BaseSelectObjectWidget):
    def __init__(self, parent, id, text, on_remove, on_opp_remove, window, index = None):
        super().__init__(parent, id, text, on_remove, on_opp_remove, window, index)
        
        self.setProperty("class", "SelectedSelectionListEntry")
    
    def get_new_widget_index(self):
        selected_widget_amt = sum(1 for widget in self._parent.widgets.values() if isinstance(widget, SL_SelectedWidget))
        unselected_widget_amt_index = len(self._parent.widgets)
        sl_unselected_widget = SL_UnSelectedWidget(self._parent, self.id, self.text, self.on_opp_remove, self.on_remove, self._window, self.index)
        
        if self.index is not None:
            index_count = 0
            
            for widget in sorted(list(self._parent.widgets.values()), key=lambda w: int(w.index)):
                if isinstance(widget, SL_UnSelectedWidget):
                    if widget.index is not None and widget.index > self.index:
                        return selected_widget_amt + index_count, sl_unselected_widget
                    
                    index_count += 1
        
        return unselected_widget_amt_index, sl_unselected_widget

class SL_UnSelectedWidget(_BaseSelectObjectWidget):
    def __init__(self, parent, id, text, on_remove, on_opp_remove, window, index = None):
        super().__init__(parent, id, text, on_remove, on_opp_remove, window, index)
        
        self.setProperty("class", "UnselectedSelectionListEntry")
    
    def get_new_widget_index(self):
        selected_widget_amt = sum(1 for widget in self._parent.widgets.values() if isinstance(widget, SL_SelectedWidget))
        sl_selected_widget = SL_SelectedWidget(self._parent, self.id, self.text, self.on_opp_remove, self.on_remove, self._window, self.index)
        
        if self.index is not None:
            index_count = 0
            
            for widget in sorted(list(self._parent.widgets.values()), key=lambda w: int(w.index)):
                if isinstance(widget, SL_SelectedWidget):
                    if widget.index is not None and widget.index > self.index:
                        return index_count, sl_selected_widget
                    
                    index_count += 1
        
        return selected_widget_amt, sl_selected_widget



class BaseDayOfTheWeekEditor(BaseSettingDialog):
    def __init__(self, parent: BaseWidget, title: str, weekdays: list[str], selected_scope: Optional[list[tuple[str, tuple[Entry, int]]]] = None):
        self.weekdays = weekdays
        
        self.full_scope = self._get_sl_tokens(DAYS_OF_THE_WEEK)
        self.selected_scope = selected_scope or self._get_sl_tokens(self.weekdays)
        
        super().__init__(title)

        self.addWidget(central_widget := BaseSelectionList(parent, None, self.selected_scope, dict(self.full_scope)))
    
    def _get_sl_tokens(self, weekdays: list[str]):
        return [(day, (Entry(day, Name(day)), i)) for i, day in enumerate(weekdays)]
    
    def _item_removed(self, prev_weekdays: list[str], day: str):
        days_of_the_week = self._get_sl_tokens(prev_weekdays)
        
        day_index = next(
            index
            for index, (d_day, _) in
            enumerate(days_of_the_week)
            if day == d_day
        )
        
        days_of_the_week.pop(day_index)
        
        return dict(days_of_the_week)
    
    def _item_selected(self, prev_weekdays: list[str], day: str, index: int):
        days_of_the_week = self._get_sl_tokens(prev_weekdays)
        
        day_data = next(v for v in self.full_scope if v[0] == day)
        days_of_the_week.insert(index, day_data)
        
        return dict(days_of_the_week)



