class UIObject:

    def setElement(self, element):
        self.element = element


class Widget(UIObject):
    pass


class FocusWidget(Widget):

    def __init__(self, element):
        self.setElement(element)
