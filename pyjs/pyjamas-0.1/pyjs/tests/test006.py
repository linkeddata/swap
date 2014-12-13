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


class FocusWidget(Widget):

    def __init__(self, element):
        self.setElement(element)


class ButtonBase(FocusWidget):

    def __init__(self, element):
        FocusWidget.__init__(self, element)

    def setHTML(self, html):
        DOM.setInnerHTML(self.getElement(), html)
    

class Button(ButtonBase):

    def __init__(self, html=None):
        ButtonBase.__init__(self, DOM.createButton())
        self.setStyleName("gwt-Button")
        if html:
            self.setHTML(html)
