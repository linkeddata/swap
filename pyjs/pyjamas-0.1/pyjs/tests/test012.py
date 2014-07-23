import DOM

class Widget:

    def __init__(self):
        self.attached = False

    def setParent(self, parent):
        self.parent = parent
        if parent == None:
            self.onDetach()
        elif parent.attached:
            self.onAttach()

    def onAttach(self):
        if self.attached:
            return
        self.attached = True
        DOM.setEventListener(self.getElement(), self)
        
    def onDetach(self):
        if not self.attached:
            return
        self.attached = False
        DOM.setEventListener(self.getElement(), None)
