import ui

class Hello:
    def onModuleLoad(self):
        b = ui.Button("Click me")
        ui.RootPanel().add(b)