import DOM

class UIObject:

    def getElement(self):
        return self.element

    def setElement(self, element):
        self.element = element

    def setStyleName(self, style):
        DOM.setAttribute(self.element, "className", style)
