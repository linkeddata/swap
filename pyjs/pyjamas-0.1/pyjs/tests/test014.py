from ui import Button, RootPanel
import Windows

def greet(sender):
    Windows.alert("Hello AJAX!")

class Hello:
    def onModuleLoad(self):
        b = Button("Click me", greet)
        RootPanel().add(b)
