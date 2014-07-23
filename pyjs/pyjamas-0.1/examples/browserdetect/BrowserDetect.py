from ui import Label, RootPanel

class BrowserDetect:
    def onModuleLoad(self):
        self.l = Label()
        RootPanel().add(self.l)
        self.display()

    def display(self):
        self.l.setText("Browser not detected/supported")

