from ui import Button, RootPanel
import Window

def greet(sender):
    Window.alert("Hello, AJAX!")

class Hello:
    def onModuleLoad(self):
        b = Button("Click me", greet)
        RootPanel().add(b)
