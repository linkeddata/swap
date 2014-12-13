import DOM

class UIObject:

    def getElement(self):
        return self.element

    def setElement(self, element):
        self.element = element

    def setStyleName(self, style):
        DOM.setAttribute(self.element, "className", style)


class Widget(UIObject):

    def setParent(self, parent):
        self.parent = parent


class Panel(Widget):
    pass


class ComplexPanel(Panel):

    def __init__(self):
        self.children = []
    
    def add(self, widget):
        self.children.append(widget)
        widget.setParent(self)
        return True


class AbsolutePanel(ComplexPanel):

    def __init__(self):
        ComplexPanel.__init__(self)
        self.setElement(DOM.createDiv())
        DOM.setStyleAttribute(self.getElement(), "overflow", "hidden")
    
    def add(self, widget):
        ComplexPanel.add(self, widget)
        DOM.appendChild(self.getElement(), widget.getElement())
        return True
