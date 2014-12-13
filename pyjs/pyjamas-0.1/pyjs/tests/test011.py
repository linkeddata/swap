from ui import Button, RootPanel

class Hello:
    def onModuleLoad(self):
        b = Button("Click me")
        RootPanel().add(b)