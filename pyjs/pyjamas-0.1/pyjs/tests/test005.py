import DOM

class UIObject:

    def getElement(self):
        return self.element

    def setElement(self, element):
        self.element = element


class Widget(UIObject):
    pass

class FocusWidget(Widget):

    def __init__(self, element):
        self.setElement(element)


class ButtonBase(FocusWidget):

    def __init__(self, element):
        FocusWidget.__init__(self, element)

    def setHTML(self, html):
        DOM.setInnerHTML(self.getElement(), html)
