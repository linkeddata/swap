# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import DOM
import pygwt
from DeferredCommand import DeferredCommand
import pyjslib
from History import History

class Event:
    FOCUSEVENTS   = 0x01800
    KEYEVENTS     = 0x00380
    MOUSEEVENTS   = 0x0007C
    ONBLUR        = 0x01000
    ONCHANGE      = 0x00400
    ONCLICK       = 0x00001
    ONDBLCLICK    = 0x00002
    ONERROR       = 0x10000
    ONFOCUS       = 0x00800
    ONKEYDOWN     = 0x00080
    ONKEYPRESS    = 0x00100
    ONKEYUP       = 0x00200
    ONLOAD        = 0x08000
    ONLOSECAPTURE = 0x02000
    ONMOUSEDOWN   = 0x00004
    ONMOUSEMOVE   = 0x00040
    ONMOUSEOUT    = 0x00020
    ONMOUSEOVER   = 0x00010
    ONMOUSEUP     = 0x00008
    ONSCROLL      = 0x04000


# FocusListenerCollection
class FocusListener:
    def fireFocusEvent(self, listeners, sender, event):
        type = DOM.eventGetType(event)
        if type == "focus":
            for listener in listeners:
                listener.onFocus(sender, DOM.eventGetKeyCode(event), modifiers)
        elif type == "blur":
            for listener in listeners:
                listener.onLostFocus(sender, DOM.eventGetKeyCode(event), modifiers)


# KeyboardListener + KeyboardListenerCollection
class KeyboardListener:
    KEY_ALT = 18
    KEY_BACKSPACE = 8
    KEY_CTRL = 17
    KEY_DELETE = 46
    KEY_DOWN = 40
    KEY_END = 35
    KEY_ENTER = 13
    KEY_ESCAPE = 27
    KEY_HOME = 36
    KEY_LEFT = 37
    KEY_PAGEDOWN = 34
    KEY_PAGEUP = 33
    KEY_RIGHT = 39
    KEY_SHIFT = 16
    KEY_TAB = 9
    KEY_UP = 38
    
    MODIFIER_ALT = 4
    MODIFIER_CTRL = 2
    MODIFIER_SHIFT = 1

    def getKeyboardModifiers(self, event):
        shift = 0
        ctrl = 0
        alt = 0
        
        if DOM.eventGetShiftKey(event):
            shift = KeyboardListener.MODIFIER_SHIFT
    
        if DOM.eventGetCtrlKey(event):
            ctrl = KeyboardListener.MODIFIER_CTRL
            
        if DOM.eventGetAltKey(event):
            alt = KeyboardListener.MODIFIER_ALT
    
        return shift | ctrl | alt


    def fireKeyboardEvent(self, listeners, sender, event):
        modifiers = KeyboardListener.getKeyboardModifiers(self, event)
    
        type = DOM.eventGetType(event)
        if type == "keydown":
            for listener in listeners:
                listener.onKeyDown(sender, DOM.eventGetKeyCode(event), modifiers)
        elif type == "keyup":
            for listener in listeners:
                listener.onKeyUp(sender, DOM.eventGetKeyCode(event), modifiers)
        elif type == "keypress":
            for listener in listeners:
                listener.onKeyPress(sender, DOM.eventGetKeyCode(event), modifiers)


# MouseListenerCollection
class MouseListener:
    def fireMouseEvent(self, listeners, sender, event):
        x = DOM.eventGetClientX(event) - DOM.getAbsoluteLeft(sender.getElement())
        y = DOM.eventGetClientY(event) - DOM.getAbsoluteTop(sender.getElement())
    
        type = DOM.eventGetType(event)
        if type == "mousedown":
            for listener in listeners:
                listener.onMouseDown(sender, x, y)
        elif type == "mouseup":
            for listener in listeners:
                listener.onMouseUp(sender, x, y)
        elif type == "mousemove":
            for listener in listeners:
                listener.onMouseMove(sender, x, y)
        elif type == "mouseover":
            from_element = DOM.eventGetFromElement(event)
            if not DOM.isOrHasChild(sender.getElement(), from_element):
                for listener in listeners:
                    listener.onMouseEnter(sender)
        elif type == "mouseout":
            to_element = DOM.eventGetToElement(event)
            if not DOM.isOrHasChild(sender.getElement(), to_element):
                for listener in listeners:
                    listener.onMouseLeave(sender)


class UIObject:

    def getAbsoluteLeft(self):
        return DOM.getAbsoluteLeft(self.getElement())

    def getAbsoluteTop(self):
        return DOM.getAbsoluteTop(self.getElement())

    def getElement(self):
        return self.element

    def getOffsetHeight(self):
        return DOM.getIntAttribute(self.element, "offsetHeight")
    
    def getOffsetWidth(self):
        return DOM.getIntAttribute(self.element, "offsetWidth")

    def getStyleName(self):
        return DOM.getAttribute(self.element, "className")

    def setElement(self, element):
        self.element = element

    def setHeight(self, height):
        DOM.setStyleAttribute(self.element, "height", height)

    def setPixelSize(self, width, height):
        if width >= 0:
            DOM.setIntStyleAttribute(self.element, "width", width)
        if height >= 0:
            DOM.setIntStyleAttribute(self.element, "height", height)

    def setSize(self, width, height):
        self.setWidth(width)
        self.setHeight(height)

    def addStyleName(self, style):
        self.setStyleName(self.element, style, True)

    def removeStyleName(self, style):
        self.setStyleName(self.element, style, False)

    # also callable as: setStyleName(self, style)
    def setStyleName(self, element, style=None, add=True):
        # emulate setStyleName(self, style)
        if style == None:
            style = element
            element = self.element
        
        oldStyle = DOM.getAttribute(element, "className")
        if oldStyle == None:
            oldStyle = ""

        idx = oldStyle.find(style)
        if add:
            if idx == -1:
                DOM.setAttribute(element, "className", oldStyle + " " + style)
        else:
            if idx != -1:
                begin = oldStyle[:idx]
                end = oldStyle[idx + len(style):]
                DOM.setAttribute(element, "className", begin + end)

    def setWidth(self, width):
        DOM.setStyleAttribute(self.element, "width", width)

    def sinkEvents(self, eventBitsToAdd):
        if self.element:
            DOM.sinkEvents(self.getElement(), eventBitsToAdd | DOM.getEventsSunk(self.getElement()))

    def isVisible(self, element=None):
        if not element:
            element = self.element
        return element.style.display != "none"

    # also callable as: setVisible(visible)
    def setVisible(self, element, visible=None):
        if visible==None:
            visible = element
            element = self.element

        if visible:
            element.style.display = ""
        else:
            element.style.display = "none"

    def unsinkEvents(self, eventBitsToRemove):
        DOM.sinkEvents(self.getElement(), ~eventBitsToRemove & DOM.getEventsSunk(self.getElement()))


class Widget(UIObject):

    def __init__(self):
        self.attached = False
        self.parent = None
        self.layoutData = None

    def getLayoutData(self):
        return self.layoutData
    
    def getParent(self):
        return self.parent

    def isAttached(self):
        return self.attached

    def onBrowserEvent(self, event):
        pass

    def onLoad(self):
        pass

    def onAttach(self):
        if self.attached:
            return
        self.attached = True
        DOM.setEventListener(self.getElement(), self)
        self.onLoad()
        
    def onDetach(self):
        if not self.attached:
            return
        self.attached = False
        DOM.setEventListener(self.getElement(), None)

    def setLayoutData(self, layoutData):
        self.layoutData = layoutData

    def setParent(self, parent):
        self.parent = parent
        if parent == None:
            self.onDetach()
        elif parent.attached:
            self.onAttach()


class FocusWidget(Widget):

    def __init__(self, element):
        Widget.__init__(self)
        self.clickListeners = []
        self.focusListeners = []
        self.keyboardListeners = []

        self.setElement(element)
        self.sinkEvents(Event.FOCUSEVENTS | Event.KEYEVENTS)

    def addClickListener(self, listener):
        self.clickListeners.append(listener)
        
    def addFocusListener(self, listener):
        self.focusListeners.append(listener)

    def addKeyboardListener(self, listener):
        self.keyboardListeners.append(listener)

    def getTabIndex(self):
        return Focus.getTabIndex(self, self.getElement())

    def isEnabled(self):
        return (DOM.getAttribute(self.getElement(), "disabled") != "true")
    
    def onBrowserEvent(self, event):
        type = DOM.eventGetType(event)
        if type == "click":
            for listener in self.clickListeners:
                if listener.onClick: listener.onClick(self)
                else: listener(self)
        elif type == "blur" or type == "focus":
            FocusListener.fireFocusEvent(self, self.focusListeners, self, event)
        elif type == "keydown" or type == "keypress" or type == "keyup":
            KeyboardListener.fireKeyboardEvent(self, self.keyboardListeners, self, event)

    def removeClickListener(self, listener):
        self.clickListeners.remove(listener)

    def removeFocusListener(self, listener):
        self.focusListeners.remove(listener)

    def removeKeyboardListener(self, listener):
        self.keyboardListeners.remove(listener)

    def setAccessKey(self, key):
        DOM.setAttribute(self.getElement(), "accessKey", "" + key)
        
    def setEnabled(self, enabled):
        if enabled:
            value = ""
        else:
            value = "true"
        DOM.setAttribute(self.getElement(), "disabled", value)

    def setFocus(self, focused):
        if (focused):
            Focus.focus(self, self.getElement())
        else:
            Focus.blur(self, self.getElement())

    def setTabIndex(self, index):
        Focus.setTabIndex(self, self.getElement(), index)


class ButtonBase(FocusWidget):

    def __init__(self, element):
        FocusWidget.__init__(self, element)
        self.sinkEvents(Event.ONCLICK)

    def getHTML(self):
        return DOM.getInnerHTML(self.getElement())

    def getText(self):
        return DOM.getInnerText(self.getElement())

    def setHTML(self, html):
        DOM.setInnerHTML(self.getElement(), html)

    def setText(self, text):
        DOM.setInnerText(self.getElement(), text)


class Button(ButtonBase):

    def __init__(self, html=None, listener=None):
        ButtonBase.__init__(self, DOM.createButton())
        self.setStyleName("gwt-Button")
        if html:
            self.setHTML(html)
        if listener:
            self.addClickListener(listener)

    def click(self):
        self.getElement().click()


class CheckBox(ButtonBase):
    
    def __init__(self, label=None, asHTML=False):
        self.initElement(DOM.createInputCheck())
        
        self.setStyleName("gwt-CheckBox")
        if label:
            if asHTML:
                self.setHTML(label)
            else:
                self.setText(label)

    def initElement(self, element):
        ButtonBase.__init__(self, DOM.createSpan())
        self.inputElem = element
        self.labelElem = DOM.createLabel()
        
        DOM.appendChild(self.getElement(), self.inputElem)
        DOM.appendChild(self.getElement(), self.labelElem)
        
        uid = "check" + self.getUniqueID()
        DOM.setAttribute(self.inputElem, "id", uid)
        DOM.setAttribute(self.labelElem, "htmlFor", uid)

    # emulate static
    def getUniqueID(self):
        """
        _CheckBox_unique_id++;
        return _CheckBox_unique_id;
        };
        var _CheckBox_unique_id=0;
        {
        """

    def getHTML(self):
        return DOM.getInnerHTML(self.labelElem)

    def getText(self):
        return DOM.getInnerText(self.labelElem)

    def setChecked(self, checked):
        if checked:
            value = "true"
        else:
            value = ""
        
        DOM.setAttribute(self.inputElem, "checked", value)
        DOM.setAttribute(self.inputElem, "defaultChecked", value)

    def isChecked(self):
        if self.attached:
            propName = "checked"
        else:
            propName = "defaultChecked"
            
        value = DOM.getAttribute(self.inputElem, propName)
        
        return value == "true" or value == "-1"

    def isEnabled(self):
        return (DOM.getAttribute(self.inputElem, "disabled") != "true")

    def setEnabled(self, enabled):
        if enabled:
            value = ""
        else:
            value = "true"
        DOM.setAttribute(self.inputElem, "disabled", value)

    def setHTML(self, html):
        DOM.setInnerHTML(self.labelElem, html)

    def setText(self, text):
        DOM.setInnerText(self.labelElem, text)


class RadioButton(CheckBox):
    def __init__(self, group, label=None, asHTML=False):
        self.initElement(DOM.createInputRadio(group))

        self.setStyleName("gwt-RadioButton")
        if label:
            if asHTML:
                self.setHTML(label)
            else:
                self.setText(label)


class Composite(Widget):
    def __init__(self):
        Widget.__init__(self)

    def onAttach(self):
        Widget.onAttach(self)
        self.widget.onAttach()
        
    def onDetach(self):
        Widget.onDetach(self)
        self.widget.onDetach()
        
    def setWidget(self, widget):
        self.widget = widget
        self.setElement(widget.getElement())

    def setParent(self, parent):
        Widget.setParent(self, parent)
        self.widget.setParent(parent)


class Panel(Widget):
    def __init__(self):
        Widget.__init__(self)
        self.children = []

    def clear(self):
        pass

    def disown(self, widget):
        widget.setParent(None)

    def adopt(self, widget):
        widget.setParent(self)

    def remove(self, widget):
        pass

    def onAttach(self):
        Widget.onAttach(self)
        for child in self:
            child.onAttach()

    def onDetach(self):
        Widget.onDetach(self)
        for child in self:
            child.onDetach()

    def __iter__(self):
        return self.children.__iter__()


class CellFormatter:
    
    def __init__(self, outer):
        self.outer = outer
    
    def addStyleName(self, row, column, styleName):
        self.outer.prepareCell(row, column)
        self.outer.setStyleName(self.getElement(row, column), styleName, True)

    def getElement(self, row, column):
        self.outer.checkCellBounds(row, column)
        return DOM.getChild(self.outer.rowFormatter.getElement(row), column)

    def getStyleName(self, row, column):
        return DOM.getAttribute(self.getElement(row, column), "className")

    def removeStyleName(self, row, column, styleName):
        self.checkCellBounds(row, column)
        self.outer.setStyleName(self.getElement(row, column), styleName, False)

    def setAlignment(self, row, column, hAlign, vAlign):
        self.outer.prepareCell(row, column)
        self.setHorizontalAlignment(row, column, hAlign)
        self.setVerticalAlignment(row, column, vAlign)

    def setHeight(self, row, column, height):
        self.outer.prepareCell(row, column)
        DOM.setAttribute(self.getCellElement(self.outer.tableElem, row, column), "height", height)

    def setHorizontalAlignment(self, row, column, align):
        self.outer.prepareCell(row, column)
        DOM.setStyleAttribute(self.getCellElement(self.outer.tableElem, row, column), "textAlign", align)
    
    def setStyleName(self, row, column, styleName):
        self.outer.prepareCell(row, column)
        self.setAttr(row, column, "className", styleName)

    def setVerticalAlignment(self, row, column, align):
        self.outer.prepareCell(row, column)
        DOM.setStyleAttribute(self.getCellElement(self.tableElem, row, column), "verticalAlign", align)

    def setWidth(self, row, column, width):
        self.outer.prepareCell(row, column)
        DOM.setAttribute(self.getCellElement(self.outer.tableElem, row, column), "width", width)

    def setWordWrap(self, row, column, wrap):
        self.outer.prepareCell(row, column)
        if wrap:
            wrap_str = ""
        else:
            wrap_str = "nowrap"
        
        DOM.setStyleAttribute(self.getElement(row, column), "whiteSpace", wrap_str)

    def ensureElement(self, row, column):
        self.outer.prepareCell(row, column)
        return DOM.getChild(self.outer.rowFormatter.ensureElement(row), column)

    def getAttr(self, row, column, attr):
        elem = self.getElement(row, column)
        return DOM.getAttribute(elem, attr)

    def setAttr(self, row, column, attrName, value):
        elem = self.getElement(row, column)
        DOM.setAttribute(elem, attrName, value)

    def getCellElement(self, table, row, col):
        """
        return table.rows[row].cells[col];
        """

    def getRawElement(self, row, column):
        return self.getCellElement(self.outer.tableElem, row, column)

class RowFormatter:

    def __init__(self, outer):
        self.outer = outer

    def addStyleName(self, row, styleName):
        self.outer.setStyleName(self.ensureElement(row), styleName, True)

    def getElement(self, row):
        self.outer.checkRowBounds(row)
        return DOM.getChild(self.outer.bodyElem, row)
        
    def getStyleName(self, row):
        return DOM.getAttribute(self.getElement(row), "className")
        
    def removeStyleName(self, row, styleName):
        self.outer.setStyleName(self.getElement(row), styleName, False)

    def setStyleName(self, row, styleName):
        elem = self.ensureElement(row)
        DOM.setAttribute(elem, "className", styleName)
        
    def setVerticalAlign(self, row, align):
        DOM.setStyleAttribute(self.ensureElement(row), "verticalAlign", align)
    
    def ensureElement(self, row):
        self.outer.prepareRow(row)
        return DOM.getChild(self.outer.bodyElem, row)


class HTMLTable(Panel):
    
    def __init__(self):
        Panel.__init__(self)
        self.cellFormatter = CellFormatter()
        self.rowFormatter = RowFormatter()
        self.tableListeners = []
        self.widgetMap = {}

        self.tableElem = DOM.createTable()
        self.bodyElem = DOM.createTBody()
        DOM.appendChild(self.tableElem, self.bodyElem)
        self.setElement(self.tableElem)
        self.sinkEvents(Event.ONCLICK)

    def add(self, widget):
        return False

    def addTableListener(self, listener):
        self.tableListeners.append(listener)

    def clear(self):
        for row in range(self.getRowCount()):
            for col in self.getCellCount(row):
                child = self.getWidget(row, col)
                if child != None:
                    self.removeWidget(row, col, child)

    def clearCell(self, row, column):
        td = self.cellFormatter.getElement(row, column)
        return self.internalClearCell(row, column, td)

    def getCellCount(self, row):
        return 0

    def getCellFormatter(self):
        return self.cellFormatter
    
    def getCellPadding(self):
        return DOM.getIntAttribute(self.tableElem, "cellPadding")
    
    def getCellSpacing(self):
        return DOM.getIntAttribute(self.tableElem, "cellSpacing")

    def getHTML(self, row, column):
        element = self.cellFormatter.getElement(row, column)
        return DOM.getInnerHTML(element)

    def getRowCount(self):
        return 0
        
    def getRowFormatter(self):
        return self.rowFormatter
        
    def getText(self, row, column):
        self.checkCellBounds(row, column)
        element = self.cellFormatter.getElement(row, column)
        return DOM.getInnerText(element)

    def getWidget(self, row, column):
        self.checkCellBounds(row, column)
        key = self.computeKey(row, column)
        return self.widgetMap[key]

    def isCellPresent(self, row, column):
        # GWT uses "and", possibly a bug
        if row >= self.getRowCount() or row < 0:
            return False
        
        if column < 0 or column >= self.getCellCount(row):
            return False
        
        return True

    def __iter__(self):
        return self.widgetMap.itervalues()


    def onBrowserEvent(self, event):
        if DOM.eventGetType(event) == "click":
            td = self.getEventTargetCell(event)
            if not td:
                return

            tr = DOM.getParent(td)
            body = DOM.getParent(tr)
            row = DOM.getChildIndex(body, tr)
            column = DOM.getChildIndex(tr, td)
        
            for listener in self.tableListeners:
                if listener.onCellClicked:
                    listener.onCellClicked(self, row, column)
                else:
                    listener(self)

    def remove(self, widget):
        if widget.getParent() != self:
            return False
        
        td = DOM.getParent(widget.getElement())
        tr = DOM.getParent(td)
        row = DOM.getChildIndex(self.bodyElem, tr)
        column = DOM.getChildIndex(tr, td)
        
        self.removeWidget(row, column, widget)
        return True

    def removeTableListener(self, listener):
        self.tableListeners.remove(listener)

    def setBorderWidth(self, width):
        DOM.setAttribute(self.tableElem, "border", width)

    def setCellPadding(self, padding):
        DOM.setIntAttribute(self.tableElem, "cellPadding", padding)

    def setCellSpacing(self, spacing):
        DOM.setIntAttribute(self.tableElem, "cellSpacing", spacing)

    def setHTML(self, row, column, html):
        self.prepareCell(row, column)
        td = self.cleanCell(row, column)
        DOM.setInnerHTML(td, html)

    def setText(self, row, column, text):
        self.prepareCell(row, column)
        td = self.cleanCell(row, column)
        DOM.setInnerText(td, text)

    def setWidget(self, row, column, widget):
        self.prepareCell(row, column)

        td = self.cleanCell(row, column)
        DOM.appendChild(td, widget.getElement())
        
        self.widgetMap[self.computeKey(row, column)] = widget
        self.adopt(widget)

    def checkCellBounds(self, row, column):
        self.checkRowBounds(row)
        #if column<0: raise IndexError, "Column " + column + " must be non-negative: " + column

        cellSize = self.getCellCount(row)
        #if cellSize<column: raise IndexError, "Column " + column + " does not exist, col at row " + row + " size is " + self.getCellCount(row) + "cell(s)"

    def checkRowBounds(self, row):
        rowSize = self.getRowCount()
        #if row >= rowSize or row < 0: raise IndexError, "Row " + row + " does not exist, row size is " + self.getRowCount()

    def computeKey(self, row, column):
        return row + "-" + column

    def createCell(self):
        return DOM.createTD()
        
    def getBodyElement(self):
        return self.bodyElem

    def getDOMCellCount(self, row):
        return DOM.getChildCount(DOM.getChild(self.bodyElem, row))

    def getDOMRowCount(self):
        return DOM.getChildCount(self.bodyElem)

    def insertCell(self, row, column):
        tr = DOM.getChild(self.bodyElem, row)
        td = self.createCell()
        DOM.insertChild(tr, td, column)

    def insertCells(self, row, column, count):
        tr = DOM.getChild(self.bodyElem, row)
        for i in range(column, column + count):
            td = self.createCell()
            DOM.insertChild(tr, td, i)

    def insertRow(self, beforeRow):
        if beforeRow != self.getRowCount():
            self.checkRowBounds(beforeRow)
        
        tr = DOM.createTR()
        DOM.insertChild(self.bodyElem, tr, beforeRow)
        return beforeRow

    def internalClearCell(self, row, column, td):
        widget = self.widgetMap[self.computeKey(row, column)]
        if widget != None:
            self.removeWidget(row, column, widget)
            return True

        DOM.setInnerHTML(td, "")
        return False

    def prepareCell(self, row, column):
        pass

    def prepareRow(self, row):
        pass

    def removeCell(self, row, column):
        self.checkCellBounds(row, column)
        td = self.cleanCell(row, column)
        tr = DOM.getChild(self.bodyElem, row)
        DOM.removeChild(tr, td)

    def removeRow(self, row):
        for column in range(self.getCellCount(row)):
            self.cleanCell(row, column)
        DOM.removeChild(self.bodyElem, DOM.getChild(self.bodyElem, row))

    def setCellFormatter(self, cellFormatter):
        self.cellFormatter = cellFormatter

    def setRowFormatter(self, rowFormatter):
        self.rowFormatter = rowFormatter
    
    def cleanCell(self, row, column):
        td = self.cellFormatter.getRawElement(row, column)
        self.internalClearCell(row, column, td)
        return td

    def getEventTargetCell(self, event):
        td = DOM.eventGetTarget(event)
        # what happens when getAttribute returns null?
        while DOM.getAttribute(td, "tagName").lower() != "td":
            if td == None or DOM.compare(td, self.getElement()):
                return None
            td = DOM.getParent(td)

        return td

    def removeWidget(self, row, column, widget):
        self.disown(widget)

        key = self.computeKey(row, column)
        del self.widgetMap[key]

        td = self.cellFormatter.getRawElement(row, column)
        child = widget.getElement()
        DOM.removeChild(td, child)
        return True


class Grid(HTMLTable):
    
    def __init__(self, rows=0, columns=0):
        HTMLTable.__init__(self)
        self.cellFormatter = CellFormatter(self)
        self.rowFormatter = RowFormatter(self)
        self.numColumns = 0
        self.numRows = 0
        if rows > 0 or columns > 0:
            self.resize(rows, columns)

    def resize(self, rows, columns):
        self.resizeColumns(columns)
        self.resizeRows(rows)

    def resizeColumns(self, columns):
        if self.numColumns == columns:
            return
        
        if self.numColumns > columns:
            for i in range(0, self.numRows):
                for j in range(self.numColumns - 1, columns - 1, -1):
                    self.removeCell(i, j)
        else:
            for i in range(self.numRows):
                for j in range(self.numColumns, columns):
                    self.insertCell(i, j)
        self.numColumns = columns

    def resizeRows(self, rows):
        if self.numRows == rows:
            return
            
        if self.numRows > rows:
            i = self.numRows - 1
            while i >= rows:
                self.removeRow(i)
                i -= 1
        else:
            i = self.numRows
            while i < rows:
                self.insertRow(i)
                self.insertCells(i, 0, self.numColumns)
                i += 1
        self.numRows = rows

    def createCell(self):
        td = HTMLTable.createCell(self)
        DOM.setInnerHTML(td, "&nbsp;")
        return td

    def clearCell(self, row, column):
        ret = HTMLTable.clearCell(self, row, column)
        DOM.setInnerHTML(self.cellFormatter.getElement(row, column), "&nbsp;")
        return ret

    def prepareCell(self, row, column):
        pass

    def prepareRow(self, row):
        pass

    def getCellCount(self, row):
        return self.numColumns
    
    def getColumnCount(self):
        return self.numColumns
    
    def getRowCount(self):
        return self.numRows


class FlexCellFormatter(CellFormatter):
    def __init__(self, outer):
        CellFormatter.__init__(self, outer)
    
    def getColSpan(self, row, column):
        return DOM.getIntAttribute(self.getElement(row, column), "colSpan")

    def getRowSpan(self, row, column):
        return DOM.getIntAttribute(self.getElement(row, column), "rowSpan")
        
    def setColSpan(self, row, column, colSpan):
        DOM.setIntAttribute(self.ensureElement(row, column), "colSpan", colSpan)

    def setRowSpan(self, row, column, rowSpan):
        DOM.setIntAttribute(self.ensureElement(row, column), "rowSpan", rowSpan)


class FlexTable(HTMLTable):
    def __init__(self):
        HTMLTable.__init__(self)
        self.cellFormatter = FlexCellFormatter(self)
        self.rowFormatter = RowFormatter(self)

    def addCell(self, row):
        self.insertCell(row, self.getCellCount(row))

    def getCellCount(self, row):
        self.checkRowBounds(row)
        return self.getDOMCellCount(row)

    def getFlexCellFormatter(self):
        return self.getCellFormatter()

    def getRowCount(self):
        return self.getDOMRowCount()

    def removeCells(self, row, column, num):
        for i in range(i):
            self.removeCell(row, column)

    def prepareCell(self, row, column):
        self.prepareRow(row)
        #if column < 0: throw new IndexOutOfBoundsException("Cannot create a column with a negative index: " + column);
        
        cellCount = self.getCellCount(row)
        for i in range(cellCount, column + 1):
            self.addCell(row)
        
    def prepareRow(self, row):
        #if row < 0: throw new IndexOutOfBoundsException("Cannot create a row with a negative index: " + row);

        rowCount = self.getRowCount()
        for i in range(rowCount, row + 1):
            self.insertRow(i)


class ComplexPanel(Panel):

    def __init__(self):
        Panel.__init__(self)
        self.children = []
    
    def add(self, widget):
        self.children.append(widget)
        widget.setParent(self)
        return True

    def clear(self):
        for widget in self.children:
            self.remove(widget)
            
    def getWidget(self, index):
        return self.children[index]
        
    def getWidgetCount(self):
        return len(self.children)

    def getWidgets(self):
        return self.children

    def getWidgetIndex(self, child):
        return children.index(child)
    
    def insert(self, widget, beforeIndex):
        if beforeIndex > len(self.children):
            return False

        self.children.insert(beforeIndex, widget)
        widget.setParent(self)
        return True

    def remove(self, widget):
        widget.setParent(None)
        return self.children.remove(widget)


class AbsolutePanel(ComplexPanel):

    def __init__(self):
        ComplexPanel.__init__(self)
        self.setElement(DOM.createDiv())
        DOM.setStyleAttribute(self.getElement(), "overflow", "hidden")
    
    def add(self, widget, left=None, top=None):
        ComplexPanel.add(self, widget)
        DOM.appendChild(self.getElement(), widget.getElement())
        
        if left != None:
            self.setWidgetPosition(widget, left, top)
        
        return True

    def remove(self, widget):
        if ComplexPanel.remove(self, widget):
            DOM.removeChild(self.getElement(), widget.getElement())
        return True

    def setWidgetPosition(self, widget, left, top):
        h = widget.getElement()
        if (left == -1) and (top == -1):
            DOM.setStyleAttribute(h, "left", "")
            DOM.setStyleAttribute(h, "top", "")
            DOM.setStyleAttribute(h, "position", "static")
        else:
            DOM.setStyleAttribute(h, "position", "absolute")
            DOM.setStyleAttribute(h, "left", left)
            DOM.setStyleAttribute(h, "top", top)


class Label(Widget):

    def __init__(self, text=None, wordWrap=True):
        Widget.__init__(self)
        self.horzAlign = ""
        self.clickListeners = []
        self.mouseListeners = []
        
        self.setElement(DOM.createDiv())
        self.sinkEvents(Event.ONCLICK | Event.MOUSEEVENTS)
        self.setStyleName("gwt-Label")
        if text:
            self.setText(text)

        # TODO: super
        self.setWordWrap(wordWrap)
            
    def addClickListener(self, listener):
        self.clickListeners.append(listener)

    def addMouseListener(self, listener):
        self.mouseListeners.append(listener)

    def getHorizontalAlignment(self):
        return self.horzAlign

    def getText(self):
        return DOM.getInnerText(self.getElement())

    def getWordWrap(self):
        return not (DOM.getStyleAttribute(self.getElement(), "whiteSpace") == "nowrap")

    def onBrowserEvent(self, event):
        type = DOM.eventGetType(event)
        if type == "click":
            for listener in self.clickListeners:
                if listener.onClick: listener.onClick(self)
                else: listener(self)
        elif type == "mousedown" or type == "mouseup" or type == "mousemove" or type == "mouseover" or type == "mouseout":
            MouseListener.fireMouseEvent(self, self.mouseListeners, self, event)

    def removeClickListener(self, listener):
        self.clickListeners.remove(listener)

    def removeMouseListener(self, listener):
        self.mouseListeners.remove(listener)

    def setHorizontalAlignment(self, align):
        self.horzAlign = align
        DOM.setStyleAttribute(self.getElement(), "textAlign", align)

    def setText(self, text):
        DOM.setInnerText(self.getElement(), text)

    def setWordWrap(self, wrap):
        if wrap:
            style = "normal"
        else:
            style = "nowrap"
        DOM.setStyleAttribute(self.getElement(), "whiteSpace", style)


class HTML(Label):
    
    def __init__(self, html=None, wordWrap=True):
        Label.__init__(self)
        self.horzAlign = ""
        self.clickListeners = []
        self.mouseListeners = []
        
        self.setElement(DOM.createDiv())
        self.sinkEvents(Event.ONCLICK | Event.MOUSEEVENTS)
        self.setStyleName("gwt-HTML")
        if html:
            self.setHTML(html)
            
        self.setWordWrap(wordWrap)
            
    def setHTML(self, html):
        DOM.setInnerHTML(self.getElement(), html)


class HasHorizontalAlignment:
    ALIGN_LEFT = "left"
    ALIGN_CENTER = "center"
    ALIGN_RIGHT = "right"


class HasVerticalAlignment:
    ALIGN_TOP = "top"
    ALIGN_MIDDLE = "middle"
    ALIGN_BOTTOM = "bottom"


class HasAlignment:
    ALIGN_BOTTOM = "bottom"
    ALIGN_MIDDLE = "middle"
    ALIGN_TOP = "top"
    ALIGN_CENTER = "center"
    ALIGN_LEFT = "left"
    ALIGN_RIGHT = "right"


class CellPanel(ComplexPanel):
    
    def __init__(self):
        ComplexPanel.__init__(self)
        
        self.table = DOM.createTable()
        self.setElement(self.table)

    def getTable(self):
        return self.table

    def setBorderWidth(self, width):
        DOM.setAttribute(self.table, "border", "" + width)

    def getSpacing(self):
        return self.spacing

    def setSpacing(self, spacing):
        self.spacing = spacing
        DOM.setIntAttribute(self.table, "cellSpacing", spacing)


class HorizontalPanel(CellPanel):
    
    def __init__(self):
        CellPanel.__init__(self)

        self.horzAlign = HasHorizontalAlignment.ALIGN_LEFT
        self.vertAlign = HasVerticalAlignment.ALIGN_TOP
        
        body = DOM.createTBody()
        self.tableRow = DOM.createTR()
        DOM.appendChild(self.getTable(), body)
        DOM.appendChild(body, self.tableRow)
        
        DOM.setAttribute(self.getTable(), "cellSpacing", "0")
        DOM.setAttribute(self.getTable(), "cellPadding", "0")
        
        self.setElement(self.getTable())

    def add(self, widget):
        return self.insert(widget, self.getWidgetCount())

    def getHorizontalAlignment(self):
        return self.horzAlign
    
    def getVerticalAlignment(self):
        return self.vertAlign

    def insert(self, widget, beforeIndex):
        if not CellPanel.insert(self, widget, beforeIndex):
            return False
        
        td = DOM.createTD()
        
        DOM.insertChild(self.tableRow, td, beforeIndex)
        DOM.appendChild(td, widget.getElement())
        
        DOM.setStyleAttribute(widget.getElement(), "position", "static")
        self.setCellHorizontalAlignment(widget, self.horzAlign)
        self.setCellVerticalAlignment(widget, self.vertAlign)
        return True

    def remove(self, widget):
        if widget.getParent() != self:
            return False

        td = DOM.getParent(widget.getElement())
        DOM.removeChild(tableRow, td)

        CellPanel.remove(widget)
        return True

    def setHorizontalAlignment(self, align):
        self.horzAlign = align

    def setVerticalAlignment(self, align):
        self.vertAlign = align

    def setCellHorizontalAlignment(self, widget, align):
        td = self.getWidgetTd(widget)
        if td:
            DOM.setAttribute(td, "align", align)

    def setCellVerticalAlignment(self, widget, align):
        td = self.getWidgetTd(widget)
        if td:
            DOM.setStyleAttribute(td, "verticalAlign", align)

    def setCellHeight(self, widget, height):
        td = DOM.getParent(widget.getElement())
        DOM.setAttribute(td, "height", height)

    def setCellWidth(self, widget, width):
        td = DOM.getParent(widget.getElement())
        DOM.setAttribute(td, "width", width)

    def getWidgetTd(self, widget):
        if widget.parent != self:
            return None
        return DOM.getParent(widget.getElement())


class VerticalPanel(CellPanel):
    
    def __init__(self):
        CellPanel.__init__(self)

        self.horzAlign = HasHorizontalAlignment.ALIGN_LEFT
        self.vertAlign = HasVerticalAlignment.ALIGN_TOP
        
        self.body = DOM.createTBody()
        DOM.appendChild(self.getTable(), self.body)
        DOM.setAttribute(self.getTable(), "cellSpacing", "0")
        DOM.setAttribute(self.getTable(), "cellPadding", "0")
        
        self.setElement(self.getTable())

    def add(self, widget):
        return self.insert(widget, self.getWidgetCount())
    
    def getHorizontalAlignment(self):
        return self.horzAlign
    
    def getVerticalAlignment(self):
        return self.vertAlign

    def insert(self, widget, beforeIndex):
        if not CellPanel.insert(self, widget, beforeIndex):
            return False
        
        tr = DOM.createTR()
        td = DOM.createTD()
        
        DOM.insertChild(self.body, tr, beforeIndex)
        DOM.appendChild(tr, td)
        DOM.appendChild(td, widget.getElement())
        
        DOM.setStyleAttribute(widget.getElement(), "position", "static")
        self.setCellHorizontalAlignment(widget, self.horzAlign)
        self.setCellVerticalAlignment(widget, self.vertAlign)
        return True

    def remove(self, widget):
        if widget.getParent() != self:
            return False

        td = DOM.getParent(widget.getElement())
        tr = DOM.getParent(td)
        DOM.removeChild(self.body, tr)
        
        CellPanel.remove(self, widget)
        return True

    def setHorizontalAlignment(self, align):
        self.horzAlign = align

    def setVerticalAlignment(self, align):
        self.vertAlign = align
        
    def setCellHorizontalAlignment(self, widget, align):
        td = self.getWidgetTd(widget)
        if td:
            DOM.setAttribute(td, "align", align)

    def setCellVerticalAlignment(self, widget, align):
        td = self.getWidgetTd(widget)
        if td:
            DOM.setStyleAttribute(td, "verticalAlign", align)

    def setCellHeight(self, widget, height):
        td = DOM.getParent(widget.getElement())
        DOM.setAttribute(td, "height", height)

    def setCellWidth(self, widget, width):
        td = DOM.getParent(widget.getElement())
        DOM.setAttribute(td, "width", width)

    def getWidgetTd(self, widget):
        if widget.parent != self:
            return None
        return DOM.getParent(widget.getElement())


class LayoutData:
    def __init__(self, direction):
        self.direction = direction
        self.hAlign = "left"
        self.height = ""
        self.td = None
        self.vAlign = "top"
        self.width = ""


class DockPanel(CellPanel):
    
    CENTER = "center"
    EAST = "east"
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    
    def __init__(self):
        CellPanel.__init__(self)

        self.horzAlign = HasHorizontalAlignment.ALIGN_LEFT
        self.vertAlign = HasVerticalAlignment.ALIGN_TOP

        self.dirty = True
        
        self.bodyElement = DOM.createTBody()
        
        DOM.appendChild(self.getElement(), self.bodyElement)
        DOM.setIntAttribute(self.getElement(), "cellSpacing", 0)
        DOM.setIntAttribute(self.getElement(), "cellPadding", 0)
        
        self.setElement(self.getElement())

    def add(self, widget, direction="north"):
        if self.getWidgetCount() > 0:
            last = self.getWidget(self.getWidgetCount() - 1)
            data = last.getLayoutData()
            if data.direction == self.CENTER:
                return False
        CellPanel.add(self, widget)
        widget.setLayoutData(LayoutData(direction))
        self.setCellHorizontalAlignment(widget, self.horzAlign)
        self.setCellVerticalAlignment(widget, self.vertAlign)
        self.deferRealize()
        return True

    def getHorizontalAlignment(self):
        return self.horzAlign
    
    def getVerticalAlignment(self):
        return self.vertAlign
        
    def remove(self, widget):
        ret = CellPanel.remove(self, widget)
        if ret:
            self.deferRealize()
        return ret

    def setHorizontalAlignment(self, align):
        self.horzAlign = align

    def setVerticalAlignment(self, align):
        self.vertAlign = align

    def setCellHeight(self, widget, height):
        data = widget.getLayoutData()
        data.height = height
        if data.td:
            DOM.setStyleAttribute(data.td, "height", data.height)

    def setCellHorizontalAlignment(self, widget, align):
        data = widget.getLayoutData()
        data.hAlign = align
        if data.td:
            DOM.setAttribute(data.td, "align", data.hAlign)

    def setCellVerticalAlignment(self, widget, align):
        data = widget.getLayoutData()
        data.vAlign = align
        if data.td:
            DOM.setStyleAttribute(data.td, "verticalAlign", data.vAlign)

    def setCellWidth(self, widget, width):
        data = widget.getLayoutData()
        data.width = width
        if data.td:
            DOM.setStyleAttribute(data.td, "width", data.width)
            
    def onLoad(self):
        self.realizeTable()

    def deferRealize(self):
        if self.dirty:
            return
        self.dirty = True
        
        # should be deferred
        #DeferredCommand().add(self)
        self.realizeTable()
        
    def execute(self):
        self.realizeTable()

    def realizeTable(self):
        if not self.dirty:
            return
        self.dirty = False

        while DOM.getChildCount(self.bodyElement) > 0:
            DOM.removeChild(self.bodyElement, DOM.getChild(self.bodyElement, 0))

        rowCount = 1
        colCount = 1
        for i in range(self.getWidgetCount()):
            data = self.getWidget(i).getLayoutData()
            dir = data.direction
            if dir == self.NORTH or dir == self.SOUTH:
                rowCount += 1
            elif dir == self.EAST or dir == self.WEST:
                colCount += 1

        rows = []
        for i in range(rowCount):
            rows[i] = DockPanelTmpRow()
            rows[i].tr = DOM.createTR()
            DOM.appendChild(self.bodyElement, rows[i].tr)

        
        westCol = 0
        eastCol = colCount - 1
        northRow = 0
        southRow = rowCount - 1
        
        for i in range(self.getWidgetCount()):
            child = self.getWidget(i)
            layout = child.getLayoutData()
            
            td = DOM.createTD()
            DOM.appendChild(td, child.getElement())
            layout.td = td
            DOM.setAttribute(layout.td, "align", layout.hAlign)
            DOM.setStyleAttribute(layout.td, "verticalAlign", layout.vAlign)
            DOM.setAttribute(layout.td, "width", layout.width)
            DOM.setAttribute(layout.td, "height", layout.height)
            
            if layout.direction == self.NORTH:
                DOM.insertChild(rows[northRow].tr, td, rows[northRow].center)
                DOM.setIntAttribute(td, "colSpan", eastCol - westCol + 1)
                northRow += 1
            elif layout.direction == self.SOUTH:
                DOM.insertChild(rows[southRow].tr, td, rows[southRow].center)
                DOM.setIntAttribute(td, "colSpan", eastCol - westCol + 1)
                southRow -= 1
            elif layout.direction == self.WEST:
                row = rows[northRow]
                DOM.insertChild(row.tr, td, row.center)
                row.center += 1
                DOM.setIntAttribute(td, "rowSpan", southRow - northRow + 1)
                westCol += 1
            elif layout.direction == self.EAST:
                row = rows[northRow]
                DOM.insertChild(row.tr, td, row.center)
                DOM.setIntAttribute(td, "rowSpan", southRow - northRow + 1)
                eastCol -= 1
            elif layout.direction == self.CENTER:
                row = rows[northRow]
                DOM.insertChild(row.tr, td, row.center)


class DockPanelTmpRow:
    center = 0
    tr = None


rootPanels = {}

class RootPanel(AbsolutePanel):
    def __init__(self, element=None):
        if pyjslib.isString(element):
            return self.get(element)

        AbsolutePanel.__init__(self)
        if element:
            while (DOM.getChildCount(element) > 0):
                DOM.removeChild(element, DOM.getChild(element, 0))
        else:
            element = self.getBodyElement()
        
        self.setElement(element)
        self.onAttach()

    def getBodyElement(self):
        """
        return $doc.body;
        """

    def get(self, id=None):
        global rootPanels
        
        if rootPanels.has_key(id):
            return rootPanels[id]
        
        element = None
        if id:
            element = DOM.getElementById(id)
            if not element:
                return None

        if len(rootPanels) < 1:
            self.hookWindowClosing()
        
        panel = RootPanel(element)
        rootPanels[id] = panel
        return panel

    # TODO
    def hookWindowClosing(self):
        pass


class Hyperlink(Widget):

    def __init__(self, text="", asHTML=False, targetHistoryToken=""):
        Widget.__init__(self)
        self.clickListeners = []
        self.targetHistoryToken = ""

        self.setElement(DOM.createDiv())
        self.anchorElem = DOM.createAnchor()
        DOM.appendChild(self.getElement(), self.anchorElem)
        self.sinkEvents(Event.ONCLICK)

        if asHTML:
            self.setHTML(text)
        else:
            self.setText(text)
        
        if targetHistoryToken:
            self.setTargetHistoryToken(targetHistoryToken)

    def addClickListener(self, listener):
        self.clickListeners.append(listener)

    def getHTML(self):
        return DOM.getInnerHTML(self.anchorElem)

    def getTargetHistoryToken(self):
        return self.targetHistoryToken

    def getText(self):
        return DOM.getInnerText(self.anchorElem)

    def onBrowserEvent(self, event):
        if DOM.eventGetType(event) == "click":
            for listener in self.clickListeners:
                if listener.onClick: listener.onClick(self)
                else: listener(self)
            History().newItem(self.targetHistoryToken)
            DOM.eventPreventDefault(event)

    def removeClickListener(self, listener):
        self.clickListeners.remove(listener)

    def setHTML(self, html):
        DOM.setInnerHTML(self.anchorElem, html)

    def setTargetHistoryToken(self, targetHistoryToken):
        self.targetHistoryToken = targetHistoryToken
        DOM.setAttribute(self.anchorElem, "href", "#" + targetHistoryToken)

    def setText(self, text):
        DOM.setInnerText(self.anchorElem, text)


class Image(Widget):
    def __init__(self, url=""):
        Widget.__init__(self)
        self.clickListeners = []
        self.loadListeners = []
        self.mouseListeners = []
        
        self.setElement(DOM.createImg())
        self.sinkEvents(Event.ONCLICK | Event.MOUSEEVENTS | Event.ONLOAD | Event.ONERROR)
        
        if url:
            self.setUrl(url)

    # emulate static
    def setPrefetchImages(self, key, value):
        """
        _Image_prefetchImages[key]=value;
        };
        var _Image_prefetchImages=new Object();
        {
        """

    def addClickListener(self, listener):
        self.clickListeners.append(listener)

    def addLoadListener(self, listener):
        self.loadListeners.append(listener)

    def addMouseListener(self, listener):
        self.mouseListeners.append(listener)

    def getUrl(self):
        return DOM.getAttribute(self.getElement(), "src")

    def onBrowserEvent(self, event):
        type = DOM.eventGetType(event)
        if type == "click":
            for listener in self.clickListeners:
                if listener.onClick: listener.onClick(self)
                else: listener(self)
        elif type == "mousedown" or type == "mouseup" or type == "mousemove" or type == "mouseover" or type == "mouseout":
            MouseListener.fireMouseEvent(self, self.mouseListeners, self, event)
        elif type == "load":
            for listener in self.loadListeners:
                listener.onLoad(self)
        elif type == "error":
            for listener in self.loadListeners:
                listener.onError(self)

    def prefetch(self, url):
        img = DOM.createImg()
        DOM.setAttribute(img, "src", url)
        self.setPrefetchImages(url, img)

    def setUrl(self, url):
        DOM.setAttribute(self.getElement(), "src", url)


class FlowPanel(ComplexPanel):
    def __init__(self):
        ComplexPanel.__init__(self)
        self.setElement(DOM.createDiv())
    
    def add(self, w):
        ComplexPanel.add(self, w)
        DOM.appendChild(self.getElement(), w.getElement())
        DOM.setStyleAttribute(w.getElement(), "display", "inline")
        return True

    def remove(self, w):
        if not ComplexPanel.remove(w):
            return False
        
        DOM.removeChild(self.getElement(), w.getElement())
        return True


class HTMLPanel(ComplexPanel):
    def __init__(self, html):
        ComplexPanel.__init__(self)
        self.setElement(DOM.createDiv())
        DOM.setInnerHTML(self.getElement(), html)

    def add(self, widget, id=None):
        if id == None:
            return False
        
        element = self.getElementById(self.getElement(), id)
        if element == None:
            return False
        DOM.appendChild(element, widget.getElement())

        ComplexPanel.add(self, widget)
        return True

    # emulate static
    def createUniqueId(self):
        """
        _HTMLPanel_sUid++;
        return "HTMLPanel_" + _HTMLPanel_sUid;
        };
        var _HTMLPanel_sUid=0;
        {
        """
    
    def remove(self, widget):
        if not ComplexPanel.remove(widget):
            return False
        
        DOM.removeChild(DOM.getParent(widget.getElement()), widget.getElement())
        return True

    def getElementById(self, element, id):
        element_id = DOM.getAttribute(element, "id")
        if element_id != None and element_id == id:
            return element
        
        child = DOM.getFirstChild(element)
        while child != None:
            ret = self.getElementById(child, id)
            if ret != None:
                return ret
            child = DOM.getNextSibling(child)
        
        return None


class DeckPanel(ComplexPanel):
    def __init__(self):
        ComplexPanel.__init__(self)
        self.visibleWidget = -1
        self.setElement(DOM.createDiv())

    def add(self, widget):
        return self.insert(widget, self.getWidgetCount())

    def getVisibleWidget(self):
        return self.visibleWidget

    def insert(self, widget, beforeIndex):
        ComplexPanel.add(self, widget)
        DOM.appendChild(self.getElement(), widget.getElement())

        DOM.setStyleAttribute(widget.getElement(), "width", "100%")
        DOM.setStyleAttribute(widget.getElement(), "height", "100%")
        self.setVisible(widget.getElement(), False)
        return True

    def remove(self, widget):
        if not ComplexPanel.remove(self, w):
            return False
        DOM.removeChild(self.getElement(), w.getElement())
        return True

    def showWidget(self, index):
        if self.visibleWidget != -1:
            oldWidget = self.getWidget(self.visibleWidget)
            self.setVisible(oldWidget.getElement(), False)

        self.visibleWidget = index

        newWidget = self.getWidget(self.visibleWidget)
        self.setVisible(newWidget.getElement(), True)



class SimplePanel(Panel):
    def __init__(self, element=None):
        Panel.__init__(self)
        if element == None:
            element = DOM.createDiv()
        self.setElement(element)

    def add(self, w):
        if len(self.children) > 0:
            return False
        
        DOM.appendChild(self.getContainerElement(), w.getElement())
        self.setWidget(w)
        return True

    def clear(self):
        self.children = []

    def getWidget(self, index):
        #return self.children(index)
        return self.children[index]

    def getWidgetCount(self):
        return len(self.children)

    def getWidgetIndex(self, child):
        widget = self.children[0]
        if child == widget:
            return 0
        return -1

    def remove(self, w):
        widget = self.children[0]
        if w == widget:
            self.children = [w]
            DOM.removeChild(self.getContainerElement(), w.getElement())
            w.setParent(None)
            return True

        return False
    
    def getContainerElement(self):
        return self.getElement()

    def setWidget(self, w):
        self.children = [w]
        w.setParent(self)
        

class ScrollPanel(SimplePanel):
    def __init__(self, child=None):
        SimplePanel.__init__(self)
        self.setAlwaysShowScrollBars(False)
        
        if child != None:
            self.add(child)

    def ensureVisible(self, item):
        scroll = self.getElement()
        element = item.getElement()
        self.ensureVisibleImpl(scroll, element)

    def setScrollPosition(self, position):
        DOM.setIntAttribute(self.getElement(), "scrollTop", position)

    def getScrollPosition(self):
        return DOM.getIntAttribute(self.getElement(), "scrollTop")

    def setAlwaysShowScrollBars(self, alwaysShow):
        if alwaysShow:
            style = "scroll"
        else:
            style = "auto"
        DOM.setStyleAttribute(self.getElement(), "overflow", style)

    def ensureVisibleImpl(self, scroll, e):
        """
        if (!e) return;

        var item = e;
        var realOffset = 0;
        while (item && (item != scroll)) {
            realOffset += item.offsetTop;
            item = item.offsetParent;
            }

        scroll.scrollTop = realOffset - scroll.offsetHeight / 2;
        """


class PopupPanel(SimplePanel):
    def __init__(self, autoHide=False):
        self.popupListeners = []
        self.showing = False
        self.autoHide = False
        
        SimplePanel.__init__(self, self.createElement())
        if autoHide:
            self.autoHide = autoHide

    def add(self, widget):
        if self.getWidgetCount() > 0:
            return False
        
        self.setChild(self.getElement(), widget.getElement())
        self.setWidget(widget)
        return True

    def addPopupListener(self, listener):
        self.popupListeners.append(listener)

    # UIObject.addStyleName calls PopupPanel.setStyleName with incorrect parameters
    def addStyleName(self, style):
        self.setStyleName(style)
        
    # PopupImpl.createElement
    def createElement(self):
        return DOM.createDiv()
    
    # PopupImpl.fixup
    def fixup(self, popup):
        pass

    def hide(self, autoClosed=False):
        if not self.showing:
            return
        self.showing = False
        DOM.removeEventPreview(self)
        
        RootPanel().get().remove(self)
        for listener in self.popupListeners:
            if listener.onPopupClosed: listener.onPopupClosed(self, autoClosed)
            else: listener(self, autoClosed)

    def onEventPreview(self, event):
        type = DOM.eventGetType(event)
        if type == "keydown":
            return self.onKeyDownPreview(DOM.eventGetKeyCode(event), KeyboardListener.getKeyboardModifiers(self, event))
        elif type == "keyup":
            return self.onKeyUpPreview(DOM.eventGetKeyCode(event), KeyboardListener.getKeyboardModifiers(self, event))
        elif type == "keypress":
            return self.onKeyPressPreview(DOM.eventGetKeyCode(event), KeyboardListener.getKeyboardModifiers(self, event))
        elif type == "mousedown" or type == "mouseup" or type == "mousemove" or type == "click" or type == "dblclick":
            if DOM.getCaptureElement() == None:
                target = DOM.eventGetTarget(event)
                if not DOM.isOrHasChild(self.getElement(), target):
                    if self.autoHide and (type == "click"):
                        self.hide(True)
                        return True
                    return False

        return True

    def onKeyDownPreview(self, key, modifiers):
        return True

    def onKeyPressPreview(self, key, modifiers):
        return True

    def onKeyUpPreview(self, key, modifiers):
        return True

    def removePopupListener(self, listener):
        self.popupListeners.remove(listener)

    # PopupImpl.setChild
    def setChild(self, popup, child):
        DOM.appendChild(popup, child)

    # PopupImpl.setClassName
    def setClassName(self, popup, className):
        DOM.setAttribute(popup, "className", className)

    # PopupImpl.setHeight
    def setHeight(self, height):
        DOM.setStyleAttribute(self.getElement(), "height", height)

    def setPixelSize(self, width, height):
        if width >= 0:
            self.setWidth("" + width)
        if height >= 0:
            self.setHeight("" + height)

    def setPopupPosition(self, left, top):
        RootPanel().setWidgetPosition(self, left, top)
        self.fixup(self.getElement())

    def setStyleName(self, style):
        self.setClassName(self.getElement(), style)

    # PopupImpl.setWidth
    def setWidth(self, width):
        DOM.setStyleAttribute(self.getElement(), "width", width)

    def show(self):
        if self.showing:
            return
        
        self.showing = True
        DOM.addEventPreview(self)

        RootPanel().get().add(self)
        self.fixup(self.getElement())


class MenuItem(UIObject):
    def __init__(self, text, asHTML=False, cmd=None, subMenu=None):
        self.command = None
        self.parentMenu = None
        self.subMenu = None
        
        self.setElement(DOM.createTD())
        self.sinkEvents(Event.ONCLICK | Event.ONMOUSEOVER | Event.ONMOUSEOUT)
        self.setSelectionStyle(False)
        
        if asHTML:
            self.setHTML(text)
        else:
            self.setText(text)
        
        self.setStyleName("gwt-MenuItem")
        
        if cmd<>None:
            self.setCommand(cmd)
        elif subMenu<>None:
            self.setSubMenu(subMenu)

    def getCommand(self):
        return self.command

    def getParentMenu(self):
        return self.parentMenu
    
    def getSubMenu(self):
        return self.subMenu
    
    def getText(self):
        return DOM.getInnerText(self.getElement())

    def setCommand(self, cmd):
        self.command = cmd

    def setHTML(self, html):
        DOM.setInnerHTML(self.getElement(), html)
        
    def setSubMenu(self, subMenu):
        self.subMenu = subMenu
    
    def setText(self, text):
        DOM.setInnerText(self.getElement(), text)

    def setParentMenu(self, parentMenu):
        self.parentMenu = parentMenu

    def setSelectionStyle(self, selected):
        if selected:
            self.addStyleName("gwt-MenuItem-selected")
        else:
            self.removeStyleName("gwt-MenuItem-selected")


class MenuBar(Widget):
    def __init__(self, vertical=False):
        Widget.__init__(self)
        self.body = None
        self.items = []
        self.parentMenu = None
        self.popup = None
        self.selectedItem = None
        self.shownChildMenu = None
        self.vertical = False
        self.autoOpen = False

        Widget.__init__(self)
        
        table = DOM.createTable()
        self.body = DOM.createTBody()
        DOM.appendChild(table, self.body)

        if not vertical:
            tr = DOM.createTR()
            DOM.appendChild(self.body, tr)

        self.vertical = vertical
        
        outer = DOM.createDiv()
        DOM.appendChild(outer, table)
        self.setElement(outer)
        self.setStyleName("gwt-MenuBar")

    def addNewItem(self, text="", asHTML=False, cmd=None, subMenu=None):
        item = MenuItem(text, asHTML, cmd, subMenu)
        self.addItem(item)
        return item
        
    def addItem(self, item):
        if self.vertical:
            tr = DOM.createTR()
            DOM.appendChild(self.body, tr)
        else:
            tr = DOM.getChild(self.body, 0)

        DOM.appendChild(tr, item.getElement())
        
        item.setParentMenu(self)
        item.setSelectionStyle(False)
        self.items.append(item)
    
    def clearItems(self):
        container = self.getItemContainerElement()
        while DOM.getChildCount(container) > 0:
            DOM.removeChild(container, DOM.getChild(container, 0))
        self.items = []

    def getAutoOpen(self):
        return self.autoOpen

    def onBrowserEvent(self, event):
        Widget.onBrowserEvent(self, event)
        
        item = self.findItem(DOM.eventGetTarget(event))
        if item == None:
            return
        
        type = DOM.eventGetType(event)
        if type == "click":
            self.doItemAction(item, True)
        elif type == "mouseover":
            self.itemOver(item)
        elif type == "mouseout":
            self.itemOver(None)

    def onPopupClosed(self, sender, autoClosed):
        if autoClosed:
            self.closeAllParents()

        self.onHide()
        self.shownChildMenu = None
        self.popup = None

    def removeItem(self, item):
        idx = self.items.index(item)
        if idx == -1:
            return
        
        container = self.getItemContainerElement()
        DOM.removeChild(container, DOM.getChild(container, idx))
        del self.items[idx]

    def setAutoOpen(self, autoOpen):
        self.autoOpen = autoOpen

    def closeAllParents(self):
        curMenu = self
        while curMenu != None:
            curMenu.close()
        
            if (curMenu.parentMenu == None) and (curMenu.selectedItem != None):
                curMenu.selectedItem.setSelectionStyle(False)
                curMenu.selectedItem = None

            curMenu = curMenu.parentMenu

    def doItemAction(self, item, fireCommand):
        if (self.shownChildMenu != None) and (item.getSubMenu() == self.shownChildMenu):
            return

        if (self.shownChildMenu != None):
            self.shownChildMenu.onHide()
            self.popup.hide()

        if item.getSubMenu() == None:
            if fireCommand:
                self.closeAllParents()
    
            cmd = item.getCommand()
            # TODO
            #if cmd <> None:
            #   DeferredCommand.add(cmd)
            return

        self.selectItem(item)
        self.popup = MenuBarPopupPanel(item)
        self.popup.addPopupListener(self)

        if self.vertical:
            self.popup.setPopupPosition(item.getAbsoluteLeft() + item.getOffsetWidth(), item.getAbsoluteTop())
        else:
            self.popup.setPopupPosition(item.getAbsoluteLeft(), item.getAbsoluteTop() + item.getOffsetHeight())

        self.shownChildMenu = item.getSubMenu()
        sub_menu = item.getSubMenu()
        sub_menu.parentMenu = self
        
        self.popup.show()

    def onDetach(self):
        if self.popup != None:
            self.popup.hide()

        Widget.onDetach(self)

    def itemOver(self, item):
        if item == None:
            if (self.selectedItem != None) and (self.shownChildMenu == self.selectedItem.getSubMenu()):
                return

        self.selectItem(item)
        
        if item != None:
            if (self.shownChildMenu != None) or (self.parentMenu != None) or self.autoOpen:
                self.doItemAction(item, False)

    def close(self):
        if self.parentMenu != None:
            self.parentMenu.popup.hide()

    def findItem(self, hItem):
        for item in self.items:
            if DOM.isOrHasChild(item.getElement(), hItem):
                return item
            
        return None

    def getItemContainerElement(self):
        if self.vertical:
            return self.body
        else:
            return DOM.getChild(self.body, 0)

    def onHide(self):
        if self.shownChildMenu != None:
            self.shownChildMenu.onHide()
            self.popup.hide()

    def onShow(self):
        if len(self.items) > 0:
            self.selectItem(self.items[0])

    def selectItem(self, item):
        if item == self.selectedItem:
            return

        if self.selectedItem != None:
            self.selectedItem.setSelectionStyle(False)
        
        if item != None:
            item.setSelectionStyle(True)

        self.selectedItem = item


class MenuBarPopupPanel(PopupPanel):
    def __init__(self, item):
        self.item = item
        PopupPanel.__init__(self, True)
        
        self.add(item.getSubMenu())
        item.getSubMenu().onShow()

    def onEventPreview(self, event):
        type = DOM.eventGetType(event)
        if type == "click":
            target = DOM.eventGetTarget(event)
            parentMenuElement = self.item.getParentMenu().getElement()
            if DOM.isOrHasChild(parentMenuElement, target):
                return false
        return PopupPanel.onEventPreview(self, event)


class ListBox(FocusWidget):
    def __init__(self):
        self.changeListeners = []
        FocusWidget.__init__(self, DOM.createSelect())
        self.sinkEvents(Event.ONCHANGE)

    def addChangeListener(self, listener):
        self.changeListeners.append(listener)

    def addItem(self, item):
        self.insertItem(item, self.getItemCount())

    def clear(self):
        h = self.getElement()
        while DOM.getChildCount(h) > 0:
            DOM.removeChild(h, DOM.getChild(h, 0))

    def getItemCount(self):
        return DOM.getChildCount(self.getElement())

    def getItemText(self, index):
        child = DOM.getChild(self.getElement(), index)
        return DOM.getInnerText(child)

    def getSelectedIndex(self):
        return DOM.getIntAttribute(self.getElement(), "selectedIndex")

    def isItemSelected(self, itemIndex):
        select = DOM.getChild(self.getElement(), itemIndex)
        #if select == None:
        #   throw new IndexOutOfBoundsException();
        return (DOM.getAttribute(select, "selected") == "true")

    def getVisibleItemCount(self):
        return DOM.getIntAttribute(self.getElement(), "size")

    def insertItem(self, item, idx):
        option = DOM.createElement("OPTION")
        DOM.setInnerText(option, item)
        DOM.insertChild(self.getElement(), option, idx)
    
    def isMultipleSelect(self):
        return DOM.getAttribute(self.getElement(), "multiple") == "true"

    def onBrowserEvent(self, event):
        if DOM.eventGetType(event) == "change":
            for listener in self.changeListeners:
                if listener.onChange:
                    listener.onChange(self)
                else:
                    listener(self)
    
    def removeChangeListener(self, listener):
        self.changeListeners.remove(listener)
    
    def removeItem(self, idx):
        child = DOM.getChild(self.getElement(), idx)
        DOM.removeChild(self.getElement(), child)
    
    def setMultipleSelect(self, multiple):
        if multiple:
            attrib = "true"
        else:
            attrib = "false"
        DOM.setAttribute(self.getElement(), "multiple", attrib)
            
    def setSelectedIndex(self, index):
        DOM.setIntAttribute(self.getElement(), "selectedIndex", index)
    
    def setVisibleItemCount(self, visibleItems):
        DOM.setIntAttribute(self.getElement(), "size", visibleItems)


class DialogBox(PopupPanel):
    def __init__(self):
        PopupPanel.__init__(self)
        self.caption = HTML()
        self.child = None
        self.dragging = False
        self.dragStartX = 0
        self.dragStartY = 0
        
        self.panel = DockPanel()
        self.panel.add(self.caption, DockPanel.NORTH)
        PopupPanel.add(self, self.panel)
        
        self.setStyleName("gwt-DialogBox")
        self.caption.setStyleName("Caption")
        self.caption.addMouseListener(self)

    def add(self, widget):
        if self.child != None:
            return False

        self.panel.add(widget, DockPanel.CENTER)
        return True

    def getHTML(self):
        return self.caption.getHTML()

    def getText(self):
        return self.caption.getText()

    def onMouseDown(self, sender, x, y):
        self.dragging = True
        DOM.setCapture(self.caption.getElement())
        self.dragStartX = x
        self.dragStartY = y

    def onMouseEnter(self, sender):
        pass

    def onMouseLeave(self, sender):
        pass

    def onMouseMove(self, sender, x, y):
        if self.dragging:
            absX = x + self.getAbsoluteLeft()
            absY = y + self.getAbsoluteTop()
            self.setPopupPosition(absX - self.dragStartX, absY - self.dragStartY)

    def onMouseUp(self, sender, x, y):
        self.dragging = False
        DOM.releaseCapture(self.caption.getElement())

    def remove(self, widget):
        if self.child != widget:
            return False

        self.panel.remove(widget)
        return True

    def setHTML(self, html):
        self.caption.setHTML(html)

    def setText(self, text):
        self.caption.setText(text)


class Frame(FocusWidget):
    def __init__(self, url=""):
        FocusWidget.__init__(self, DOM.createIFrame())

        if url:
            self.setUrl(url)

    def getUrl(self):
        return DOM.getAttribute(self.getElement(), "src")

    def setUrl(self, url):
        return DOM.setAttribute(self.getElement(), "src", url)


class TabBar(Composite):
    def __init__(self):
        Composite.__init__(self)
        self.panel = HorizontalPanel()
        self.selectedTab = -1
        self.tabListeners = []
        
        self.setWidget(self.panel)
        self.sinkEvents(Event.ONCLICK)
        self.setStyleName("gwt-TabBar")
        
        self.panel.setVerticalAlignment(HasAlignment.ALIGN_BOTTOM)
        
        first = HTML("&nbsp;", True)
        rest = HTML("&nbsp;", True)
        first.setStyleName("gwt-TabBarFirst")
        rest.setStyleName("gwt-TabBarRest")
        first.setHeight("100%")
        rest.setHeight("100%")
        
        self.panel.add(first)
        self.panel.add(rest)
        first.setHeight("100%")
        self.panel.setCellHeight(first, "100%")
        self.panel.setCellWidth(rest, "100%")

    def addTab(self, text, asHTML=False):
        self.insertTab(text, asHTML, self.getTabCount())

    def addTabListener(self, listener):
        self.tabListeners.append(listener)

    def getSelectedTab(self):
        return self.selectedTab

    def getTabCount(self):
        return self.panel.getWidgetCount() - 2

    def getTabHTML(self, index):
        if index >= self.getTabCount():
            return None
        return self.panel.getWidget(index - 1).getHTML()

    def insertTab(self, text, asHTML, beforeIndex=None):
        if beforeIndex == None:
            beforeIndex = asHTML
            asHTML = False
        
        if asHTML:
            item = HTML(text)
        else:
            item = Label(text)

        item.addClickListener(self)
        item.setStyleName("gwt-TabBarItem")
        self.panel.insert(item, beforeIndex + 1)

    def onClick(self, sender):
        for i in range(1, self.panel.getWidgetCount() - 1):
            if self.panel.getWidget(i) == sender:
                self.selectTab(i - 1)
                return

    def removeTab(self, index):
        self.panel.remove(self.panel.getWidget(index + 1))

    def removeTabListener(self, listener):
        self.tabListeners.remove(listener)

    def selectTab(self, index):
        for listener in self.tabListeners:
            if not listener.onBeforeTabSelected(self, index):
                return False
        
        self.setSelectionStyle(self.selectedTab, False)
        self.selectedTab = index
        self.setSelectionStyle(self.selectedTab, True)

        for listener in self.tabListeners:
            listener.onTabSelected(self, index)

        return True

    def getItem(self, index):
        if (index < 0) or (index >= self.panel.getWidgetCount() - 2):
            return None
        return self.panel.getWidget(index + 1)

    def setSelectionStyle(self, tabIndex, selected):
        item = self.getItem(tabIndex)
        if item != None:
            if selected:
                item.addStyleName("gwt-TabBarItem-selected")
            else:
                item.removeStyleName("gwt-TabBarItem-selected")


class TabPanel(Composite):
    def __init__(self):
        Composite.__init__(self)
        self.deck = DeckPanel()
        self.tabBar = TabBar()
        self.tabListeners = []

        panel = VerticalPanel()
        panel.add(self.tabBar)
        panel.add(self.deck)
        
        self.tabBar.setWidth("100%")
        self.tabBar.addTabListener(self)
        self.setWidget(panel)
        self.setStyleName("gwt-TabPanel")
        self.deck.setStyleName("gwt-TabPanelBottom")
        
    def add(self, w, tabText, asHTML=False):
        self.insert(w, tabText, asHTML, self.getWidgetCount())
        
    def addTabListener(self, listener):
        self.tabListeners.append(listener)

    def getDeckPanel(self):
        return self.deck

    def getTabBar(self):
        return self.tabBar

    def getWidget(self, index):
        return self.deck.getWidget(index)

    def getWidgetCount(self):
        return self.deck.getWidgetCount()

    def getWidgetIndex(self, child):
        return self.deck.getWidgetIndex(child)

    def insert(self, widget, tabText, asHTML, beforeIndex=None):
        if beforeIndex == None:
            beforeIndex = asHTML
            asHTML = False
        
        self.tabBar.insertTab(tabText, asHTML, beforeIndex)
        self.deck.insert(widget, beforeIndex)

    def __iter__(self):
        alert("TODO: TabPanel.__iter__")
    
    def onBeforeTabSelected(self, sender, tabIndex):
        for listener in self.tabListeners:
            if not listener.onBeforeTabSelected(sender, tabIndex):
                return False
        return True

    def onTabSelected(self, sender, tabIndex):
        self.deck.showWidget(tabIndex)
        for listener in self.tabListeners:
            listener.onTabSelected(sender, tabIndex)

    def remove(self, widget):
        for i in range(self.deck.getWidgetCount()):
            if self.deck.getWidget(i) == widget:
                self.tabBar.removeTab(i)
                self.deck.remove(widget)

    def removeTabListener(self, listener):
        self.tabListeners.remove(listener)

    def selectTab(self, index):
        self.tabBar.selectTab(index)


class StackPanel(ComplexPanel):

    def __init__(self):
        ComplexPanel.__init__(self)
        self.body = None
        self.visibleStack = -1
        
        table = DOM.createTable()
        self.setElement(table)
        
        self.body = DOM.createTBody()
        DOM.appendChild(table, self.body)
        DOM.setIntAttribute(table, "cellSpacing", 0)
        DOM.setIntAttribute(table, "cellPadding", 0)
        
        DOM.sinkEvents(table, Event.ONCLICK)
        self.setStyleName("gwt-StackPanel")
        
    def add(self, widget, stackText="", asHTML=False):
        ComplexPanel.add(self, widget)
        index = self.getWidgetCount() - 1
        
        tr = DOM.createTR()
        td = DOM.createTD()
        DOM.appendChild(self.body, tr)
        DOM.appendChild(tr, td)
        self.setStyleName(td, "gwt-StackPanelItem", True)
        DOM.setIntAttribute(td, "__index", index)
        DOM.setAttribute(td, "height", "1px")
        
        tr = DOM.createTR()
        td = DOM.createTD()
        DOM.appendChild(self.body, tr)
        DOM.appendChild(tr, td)
        DOM.appendChild(td, widget.getElement())
        DOM.setAttribute(td, "height", "100%")
        DOM.setAttribute(td, "vAlign", "top")
        
        self.setStackVisible(index, False)
        if self.visibleStack == -1:
            self.showStack(0)
            
        if stackText != "":
            self.setStackText(self.getWidgetCount() - 1, stackText, asHTML)
        
        return True

    def onBrowserEvent(self, event):
        if DOM.eventGetType(event) == "click":
            index = self.getDividerIndex(DOM.eventGetTarget(event))
            if index != -1:
                self.showStack(index)

    def remove(self, child):
        if child.getParent() != self:
            return False

        index = self.getWidgetIndex(child)
        tr = DOM.getChild(self.body, index)
        DOM.removeChild(self.body, tr)

        return ComplexPanel.remove(self, child)
    
    def setStackText(self, index, text, asHTML=False):
        if index >= self.getWidgetCount():
            return

        td = DOM.getChild(DOM.getChild(self.body, index * 2), 0)
        if asHTML:
            DOM.setInnerHTML(td, text)
        else:
            DOM.setInnerText(td, text)
    
    def showStack(self, index):
        if (index >= self.getWidgetCount()) or (index == self.visibleStack):
            return

        if self.visibleStack >= 0:
            self.setStackVisible(self.visibleStack, False)
        
        self.visibleStack = index
        self.setStackVisible(self.visibleStack, True)

    def getDividerIndex(self, elem):
        while (elem != None) and not DOM.compare(elem, self.getElement()):
            expando = DOM.getAttribute(elem, "__index")
            if expando != None:
                return int(expando)
            
            elem = DOM.getParent(elem)
        
        return -1

    def setStackVisible(self, index, visible):
        tr = DOM.getChild(self.body, (index * 2))
        if tr == None:
            return

        td = DOM.getFirstChild(tr)
        self.setStyleName(td, "gwt-StackPanelItem-selected", visible)
        
        tr = DOM.getChild(self.body, (index * 2) + 1)
        self.setVisible(tr, visible)
        self.getWidget(index).setVisible(visible)


class TextBoxBase(FocusWidget):
    ALIGN_CENTER = "center"
    ALIGN_JUSTIFY = "justify"
    ALIGN_LEFT = "left"
    ALIGN_RIGHT = "right"
    
    def __init__(self, element):
        self.changeListeners = []
        self.clickListeners = []
        self.currentEvent = None
        self.keyboardListeners = []
        
        FocusWidget.__init__(self, element)
        self.sinkEvents(Event.ONCHANGE | Event.KEYEVENTS | Event.ONCLICK)

    def addChangeListener(self, listener):
        self.changeListeners.append(listener)
    
    def addClickListener(self, listener):
        self.clickListeners.append(listener)
        
    def addKeyboardListener(self, listener):
        self.keyboardListeners.append(listener)
        
    def cancelKey(self):
        if self.currentEvent != None:
            DOM.eventPreventDefault(self.currentEvent)
    
    def getCursorPos(self):
        element = self.getElement()
        return element.selectionStart
    
    def getSelectedText(self):
        start = self.getCursorPos()
        length = self.getSelectionLength()
        text = self.getText()
        return text[start:start + length]
    
    def getSelectionLength(self):
        element = self.getElement()
        return element.selectionEnd - element.selectionStart
    
    def getText(self):
        return DOM.getAttribute(self.getElement(), "value")
    
    # BUG: keyboard & click events already fired in FocusWidget.onBrowserEvent
    def onBrowserEvent(self, event):
        FocusWidget.onBrowserEvent(self, event)

        type = DOM.eventGetType(event)
        #if DOM.eventGetTypeInt(event) & Event.KEYEVENTS:
            #self.currentEvent = event
            #KeyboardListener.fireKeyboardEvent(self, self.keyboardListeners, self, event)
            #self.currentEvent = None
        #elif type == "click":
            #for listener in self.clickListeners:
                #if listener.onClick: listener.onClick(self)
                #else: listener(self)
        #elif type == "change":
            #for listener in self.changeListeners:
                #if listener.onChange: listener.onChange(self)
                #else: listener(self)
        if type == "change":
            for listener in self.changeListeners:
                if listener.onChange: listener.onChange(self)
                else: listener(self)

    def removeChangeListener(self, listener):
        self.changeListeners.remove(listener)
    
    def removeClickListener(self, listener):
        self.clickListeners.remove(listener)

    def removeKeyboardListener(self, listener):
        self.keyboardListeners.remove(listener)

    def selectAll(self):
        self.setSelectionRange(0, len(self.getText()))
        
    def setCursorPos(self, pos):
        self.setSelectionRange(pos, 0)
        
    def setKey(self, key):
        if currentEvent != None:
            DOM.eventSetKeyCode(self.currentEvent, key)

    def setSelectionRange(self, pos, length):
        element = self.getElement()
        element.setSelectionRange(pos, pos + length)
        
    def setText(self, text):
        DOM.setAttribute(self.getElement(), "value", text)

    def setTextAlignment(self, align):
        DOM.setStyleAttribute(self.getElement(), "textAlign", align)


class TextBox(TextBoxBase):
    def __init__(self):
        TextBoxBase.__init__(self, DOM.createInputText())
        self.setStyleName("gwt-TextBox")
        
    def getMaxLength(self):
        return DOM.getIntAttribute(self.getElement(), "maxLength")
    
    def getVisibleLength(self):
        return DOM.getIntAttribute(self.getElement(), "size")
    
    def setMaxLength(self, length):
        DOM.setIntAttribute(self.getElement(), "maxLength", length)
    
    def setVisibleLength(self, length):
        DOM.setIntAttribute(self.getElement(), "size", length)
        

class PasswordTextBox(TextBoxBase):
    def __init__(self):
        TextBoxBase.__init__(self, DOM.createInputPassword())
        self.setStyleName("gwt-PasswordTextBox")


class TextArea(TextBoxBase):
    def __init__(self):
        TextBoxBase.__init__(self, DOM.createTextArea())
        self.setStyleName("gwt-TextArea")
    
    def getCharacterWidth(self):
        return DOM.getIntAttribute(self.getElement(), "cols")
    
    def getCursorPos(self):
        return TextBoxBase.getCursorPos(self)
    
    def getVisibleLines(self):
        return DOM.getIntAttribute(self.getElement(), "rows")
    
    def setCharacterWidth(self, width):
        DOM.setIntAttribute(self.getElement(), "cols", width)
    
    def setVisibleLines(self, lines):
        DOM.setIntAttribute(self.getElement(), "rows", lines)


class TreeItem(UIObject):
    def __init__(self, html=None):
        self.children = []
        self.itemTable = None
        self.contentElem = None
        self.imgElem = None
        self.childSpanElem = None
        self.open = False
        self.parent = None
        self.selected = False
        self.tree = None
        self.userObject = None

        self.setElement(DOM.createDiv())
        
        self.itemTable = DOM.createTable()
        self.contentElem = DOM.createSpan()
        self.childSpanElem = DOM.createSpan()
        self.imgElem = DOM.createImg()

        tbody = DOM.createTBody()
        tr = DOM.createTR()
        tdImg = DOM.createTD()
        tdContent = DOM.createTD()
        DOM.appendChild(self.itemTable, tbody)
        DOM.appendChild(tbody, tr)
        DOM.appendChild(tr, tdImg)
        DOM.appendChild(tr, tdContent)
        DOM.setStyleAttribute(tdImg, "verticalAlign", "middle")
        DOM.setStyleAttribute(tdContent, "verticalAlign", "middle")
        
        DOM.setIntStyleAttribute(self.getElement(), "marginLeft", 16)
        DOM.appendChild(self.getElement(), self.itemTable)
        DOM.appendChild(self.getElement(), self.childSpanElem)
        DOM.appendChild(tdImg, self.imgElem)
        DOM.appendChild(tdContent, self.contentElem)
        
        DOM.setAttribute(self.getElement(), "position", "relative")
        DOM.setStyleAttribute(self.contentElem, "display", "inline")
        DOM.setStyleAttribute(self.getElement(), "whiteSpace", "nowrap")
        DOM.setAttribute(self.itemTable, "whiteSpace", "nowrap")
        DOM.setStyleAttribute(self.childSpanElem, "whiteSpace", "nowrap")
        
        DOM.setAttribute(self.imgElem, "src", self.imgSrc("tree_white.gif"))
        
        self.setStyleName(self.contentElem, "gwt-TreeItem", True)
        
        if html != None:
            self.setHTML(html)
    
    def addNewItem(self, itemText):
        ret = TreeItem(itemText)
        self.addItem(ret)

        return ret

    def addItem(self, item):
        item.setTree(self.tree)
        item.setParentItem(self)
        self.children.append(item)

        DOM.appendChild(self.childSpanElem, item.getElement())
        if len(self.children) == 1:
            self.updateState()

    def getChild(self, index):
        if (index < 0) or (index >= len(self.children)):
            return None
        
        return self.children[index]
    
    def getChildCount(self):
        return len(self.children)

    def getChildIndex(self, child):
        return self.children.index(child)

    def getHTML(self):
        return DOM.getInnerHTML(self.contentElem)

    def getText(self):
        return DOM.getInnerText(self.contentElem)
    
    def getParentItem(self):
        return self.parent

    def getState(self):
        return self.open

    def getTree(self):
        return self.tree

    def getUserObject(self):
        return self.userObject

    def isSelected(self):
        return self.selected
    
    def remove(self):
        if self.parent != None:
            self.parent.removeItem(self)
        elif self.tree != None:
            self.tree.removeItem(self)

    def removeItem(self, item):
        if item not in self.children:
            return

        item.setTree(None)
        item.setParentItem(None)
        self.children.remove(item)
        DOM.removeChild(self.childSpanElem, item.getElement())
        if len(self.children) == 0:
            self.updateState()
            
    def removeItems(self):
        while self.getChildCount() > 0:
            self.removeItem(self.getChild(0))

    def setHTML(self, html):
        DOM.setInnerHTML(self.contentElem, html)

    def setText(self, text):
        DOM.setInnerText(self.contentElem, text)

    def setSelected(self, selected):
        if self.selected == selected:
            return
        self.selected = selected
        self.setStyleName(self.contentElem, "gwt-TreeItem-selected", selected)

    def setState(self, open, fireEvents=True):
        if open and len(self.children) == 0:
            return

        self.open = open
        self.updateState()
        
        if fireEvents:
            self.tree.fireStateChanged(self)

    def setUserObject(self, userObj):
        self.userObject = userObj

    def getChildren(self):
        return self.children

    def getContentHeight(self):
        return DOM.getIntAttribute(self.itemTable, "offsetHeight")

    def getImageElement(self):
        return self.imgElem

    def getTreeTop(self):
        item = self
        ret = 0

        while item != None:
            ret += DOM.getIntAttribute(item.getElement(), "offsetTop")
            item = item.getParentItem()

        return ret

    def imgSrc(self, img):
        if self.tree == None:
            return img
        src = self.tree.getImageBase() + img
        return src

    def setParentItem(self, parent):
        self.parent = parent
        
    def setTree(self, tree):
        if self.tree == tree:
            return

        self.tree = tree
        for i in range(len(self.children)):
            child = self.children[i]
            child.setTree(tree)
            
        self.updateState()

    def updateState(self):
        if len(self.children) == 0:
            self.setVisible(self.childSpanElem, False)
            DOM.setAttribute(self.imgElem, "src", self.imgSrc("tree_white.gif"))
            return
            
        if self.open:
            self.setVisible(self.childSpanElem, True)
            DOM.setAttribute(self.imgElem, "src", self.imgSrc("tree_open.gif"))
        else:
            self.setVisible(self.childSpanElem, False)
            DOM.setAttribute(self.imgElem, "src", self.imgSrc("tree_closed.gif"))

    def updateStateRecursive(self):
        self.updateState()
        for i in range(len(self.children)):
            child = self.children[i]
            child.updateStateRecursive()


class RootTreeItem(TreeItem):
    def __init__(self):
        TreeItem.__init__(self)
    
    def addItem(self, item):
        item.setTree(self.getTree())
        item.setParentItem(None)
        self.getChildren().append(item)
    
    def removeItem(self, item):
        if item not in self.getChildren():
            return
    
        item.setTree(None)
        self.getChildren().remove(item)


class Tree(Widget):
    def __init__(self):
        Widget.__init__(self)
        self.root = None
        self.curSelection = None
        self.focusListeners = []
        self.mouseListeners = []
        self.imageBase = pygwt.getModuleBaseURL() + "/"
        self.keyboardListeners = []
        self.listeners = []
        
        self.setElement(Focus.createFocusable(self))
        self.sinkEvents(Event.ONMOUSEDOWN | Event.FOCUSEVENTS | Event.KEYEVENTS)

        self.root = RootTreeItem()
        self.root.setTree(self)

        DOM.setAttribute(self.getElement(), "overflow", "auto")
        self.sinkEvents(Event.ONMOUSEDOWN | Event.ONKEYDOWN)

        self.setStyleName("gwt-Tree")

    def addFocusListener(self, listener):
        self.focusListeners.append(listener)
        
    def addNewItem(self, itemText):
        ret = TreeItem(itemText)
        self.addItem(ret)

        return ret

    def addItem(self, item):
        self.root.addItem(item)
        DOM.appendChild(self.getElement(), item.getElement())

    def addKeyboardListener(self, listener):
        self.keyboardListeners.append(listener)
    
    def addTreeListener(self, listener):
        self.listeners.append(listener)
        
    def ensureSelectedItemVisible(self):
        if self.curSelection == None:
            return

        parent = self.curSelection.getParentItem()
        while parent != None:
            parent.setState(True)
            parent = parent.getParentItem()

    def getImageBase(self):
        return self.imageBase
    
    def getItem(self, index):
        return self.root.getChild(index)

    def getItemCount(self):
        return self.root.getChildCount()

    def getSelectedItem(self):
        return self.curSelection

    def getTabIndex(self):
        return Focus.getTabIndex(self, self.getElement())

    def moveSelectionDown(self, sel, dig):
        if sel == self.root:
            return

        parent = sel.getParentItem()
        if parent == None:
            parent = self.root
        idx = parent.getChildIndex(sel)

        if not dig or not sel.getState():
            if idx < parent.getChildCount() - 1:
                self.onSelection(parent.getChild(idx + 1), True)
            else:
                self.moveSelectionDown(parent, False)
        elif sel.getChildCount() > 0:
            self.onSelection(sel.getChild(0), True)

    def moveSelectionUp(self, sel, climb):
        parent = sel.getParentItem()
        if parent == None:
            parent = self.root
        idx = parent.getChildIndex(sel)

        if idx > 0:
            sibling = parent.getChild(idx - 1)
            self.onSelection(self.findDeepestOpenChild(sibling), True)
        else:
            self.onSelection(parent, True)
            
    def onBrowserEvent(self, event):
        type = DOM.eventGetType(event)
        
        if type == "mousedown":
            MouseListener.fireMouseEvent(self, self.mouseListeners, self, event)
            self.elementClicked(self.root, DOM.eventGetTarget(event))
            self.setFocus(True)
        elif type == "mouseup" or type == "mousemove" or type == "mouseover" or type == "mouseout":
            MouseListener.fireMouseEvent(self, self.mouseListeners, self, event)
        elif type == "blur" or type == "focus":
            FocusListener.fireFocusEvent(self, self.focusListeners, self, event)
        elif type == "keydown":
            if self.curSelection == None:
                if self.root.getChildCount() > 0:
                    self.onSelection(self.root.getChild(0), True)
                Widget.onBrowserEvent(self, event)
                return
            
            keycode = DOM.eventGetKeyCode(event)
            if keycode == KeyboardListener.KEY_UP:
                self.moveSelectionUp(self.curSelection, True)
                DOM.eventPreventDefault(event)
            elif keycode == KeyboardListener.KEY_DOWN:
                self.moveSelectionDown(self.curSelection, True)
                DOM.eventPreventDefault(event)
            elif keycode == KeyboardListener.KEY_LEFT:
                if self.curSelection.getState():
                    self.curSelection.setState(False)
                DOM.eventPreventDefault(event)
            elif keycode == KeyboardListener.KEY_RIGHT:
                if not self.curSelection.getState():
                    self.curSelection.setState(True)
                DOM.eventPreventDefault(event)
        elif type == "keypress" or type == "keyup":
            KeyboardListener.fireKeyboardEvent(self, self.keyboardListeners, self, event)
        
        Widget.onBrowserEvent(self, event)

    def removeFocusListener(self, listener):
        self.focusListeners.remove(listener)

    def removeItem(self, item):
        self.root.removeItem(item)
        DOM.removeChild(self.getElement(), item.getElement())

    def removeItems(self):
        while self.getItemCount() > 0:
            self.removeItem(self.getItem(0))

    def removeKeyboardListener(self, listener):
        self.keyboardListeners.remove(listener)

    def removeTreeListener(self, listener):
        self.listeners.remove(listener)

    def setAccessKey(self, key):
        Focus.setAccessKey(self, self.getElement(), key)

    def setFocus(self, focus):
        if focus:
            Focus.focus(self, self.getElement())
        else:
            Focus.blur(self, self.getElement())

    def setImageBase(self, baseUrl):
        self.imageBase = baseUrl
        self.root.updateStateRecursive()

    def setSelectedItem(self, item, fireEvents=True):
        if item == None:
            if self.curSelection == None:
                return
            self.curSelection.setSelected(False)
            self.curSelection = None
            return

        self.onSelection(item, fireEvents)
    
    def setTabIndex(self, index):
        Focus.setTabIndex(self, self.getElement(), index)

    def onLoad(self):
        self.root.updateStateRecursive()
    
    def fireStateChanged(self, item):
        for listener in self.listeners:
            listener.onTreeItemStateChanged(item)

    def collectElementChain(self, chain, hRoot, hElem):
        if (hElem == None) or DOM.compare(hElem, hRoot):
            return

        self.collectElementChain(chain, hRoot, DOM.getParent(hElem))
        chain.append(hElem)

    def elementClicked(self, root, hElem):
        chain = []
        self.collectElementChain(chain, self.getElement(), hElem)

        item = self.findItemByChain(chain, 0, root)
        if item != None:
            if DOM.compare(item.getImageElement(), hElem):
                self.onStateChanged(item)
                return True
            elif DOM.isOrHasChild(item.getElement(), hElem):
                self.onSelection(item, True)
                return True

        return False

    def findDeepestOpenChild(self, item):
        if not item.getState():
            return item
        return self.findDeepestOpenChild(item.getChild(item.getChildCount() - 1))
    
    def findItemByChain(self, chain, idx, root):
        if idx == len(chain):
            return root

        hCurElem = chain[idx]
        for i in range(root.getChildCount()):
            child = root.getChild(i)
            if DOM.compare(child.getElement(), hCurElem):
                retItem = self.findItemByChain(chain, idx + 1, root.getChild(i))
                if retItem == None:
                    return child
                return retItem
        
        return self.findItemByChain(chain, idx + 1, root)

    def onSelection(self, item, fireEvents):
        if item == self.root:
            return

        if self.curSelection != None:
            self.curSelection.setSelected(False)

        self.curSelection = item

        if self.curSelection != None:
            self.curSelection.setSelected(True)
            if fireEvents and len(self.listeners):
                for listener in self.listeners:
                    listener.onTreeItemSelected(item)

    def onStateChanged(self, item):
        item.setState(not item.getState())
        self.fireStateChanged(item)

    def addMouseListener(self, listener):
        self.mouseListeners.append(listener)


class FocusPanel(SimplePanel):
    def __init__(self, child=None):
        self.clickListeners = []
        self.focusListeners = []
        self.keyboardListeners = []
        self.mouseListeners = []

        SimplePanel.__init__(self, Focus.createFocusable(self))
        self.sinkEvents(Event.FOCUSEVENTS | Event.KEYEVENTS | Event.ONCLICK | Event.MOUSEEVENTS)

        if child:
            self.add(child)

    def addClickListener(self, listener):
        self.clickListeners.append(listener)
    
    def addFocusListener(self, listener):
        self.focusListeners.append(listener)

    def addKeyboardListener(self, listener):
        self.keyboardListeners.append(listener)

    def addMouseListener(self, listener):
        self.mouseListeners.append(listener)

    def getTabIndex(self):
        return Focus.getTabIndex(self, self.getElement())
        
    def onBrowserEvent(self, event):
        type = DOM.eventGetType(event)
        
        if type == "click":
            for listener in self.clickListeners:
                if listener.onClick: listener.onClick(self)
                else: listener(self)
        elif type == "mousedown" or type == "mouseup" or type == "mousemove" or type == "mouseover" or type == "mouseout":
            MouseListener.fireMouseEvent(self, self.mouseListeners, self, event)
        elif type == "blur" or type == "focus":
            FocusListener.fireFocusEvent(self, self.focusListeners, self, event)
        elif type == "keydown" or type == "keypress" or type == "keyup":
            KeyboardListener.fireKeyboardEvent(self, self.keyboardListeners, self, event)
        
    def removeClickListener(self, listener):
        self.clickListeners.remove(listener)

    def removeFocusListener(self, listener):
        self.focusListeners.remove(listener)

    def removeKeyboardListener(self, listener):
        self.keyboardListeners.remove(listener)

    def removeMouseListener(self, listener):
        self.mouseListeners.remove(listener)

    def setAccessKey(self, key):
        Focus.setAccessKey(self, self.getElement(), key)
    
    def setFocus(self, focused):
        if (focused):
            Focus.focus(self, self.getElement())
        else:
            Focus.blur(self, self.getElement())

    def setTabIndex(self, index):
        Focus.setTabIndex(self, self.getElement(), index)


# FocusImpl
class Focus:
    def blur(self, elem):
        """
        elem.blur();
        """
    
    def createFocusable(self):
        """
        var e = $doc.createElement("DIV");
        e.tabIndex = 0;
        return e;
        """

    def focus(self, elem):
        """
        elem.focus();
        """
    
    def getTabIndex(self, elem):
        """
        return elem.tabIndex;
        """
    
    def setAccessKey(self, elem, key):
        """
        elem.accessKey = key;
        """
    
    def setTabIndex(self, elem, index):
        """
        elem.tabIndex = index;
        """

