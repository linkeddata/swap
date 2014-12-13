import DOM

class FocusWidget:

    def __init__(self, element):
        self.clickListeners = []

    def addClickListener(self, listener):
        self.clickListeners.append(listener)

    def onBrowserEvent(self, event):
        if DOM.eventGetType(event) == Event.ONCLICK:
            for listener in self.clickListeners:
                listener(self)
