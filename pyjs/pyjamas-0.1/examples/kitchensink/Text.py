from Sink import Sink, SinkInfo
from ui import Button, HorizontalPanel, HTML, PasswordTextBox, TextArea, TextBox, TextBoxBase, VerticalPanel, Widget

class Text(Sink):
    def __init__(self):
        self.fPasswordText = PasswordTextBox()
        self.fTextArea = TextArea()
        self.fTextBox = TextBox()

        panel = VerticalPanel()
        panel.setSpacing(8)
        panel.add(HTML("Normal text box:"))
        panel.add(self.createTextThing(self.fTextBox))
        panel.add(HTML("Password text box:"))
        panel.add(self.createTextThing(self.fPasswordText))
        panel.add(HTML("Text area:"))
        panel.add(self.createTextThing(self.fTextArea))
        self.setWidget(panel)

    def onShow(self):
        pass

    def createTextThing(self, textBox):
        p = HorizontalPanel()
        p.setSpacing(4)

        p.add(textBox)

        echo = HTML()
        select_all = Button("select all")
        p.add(select_all)
        p.add(echo)
        
        listener=TextBoxListener(self, textBox, echo, select_all)
        select_all.addClickListener(listener)
        textBox.addKeyboardListener(listener)
        textBox.addClickListener(listener)

        return p

    def updateText(self, text, echo):
        echo.setHTML("Text: " + text.getText() + "<br>" + "Selection: " + text.getCursorPos() + ", " + text.getSelectionLength())


class TextBoxListener:
    def __init__(self, parent, textBox, echo, select_all):
        self.textBox=textBox
        self.echo=echo
        self.parent=parent
        self.select_all=select_all
        
    def onClick(self, sender):
        if sender == self.select_all:
            self.textBox.selectAll()
            self.textBox.setFocus(True)

        self.parent.updateText(self.textBox, self.echo)

    def onKeyUp(self, sender, keyCode, modifiers):
        self.parent.updateText(self.textBox, self.echo)

    def onKeyDown(self, sender, keyCode, modifiers):
        pass
    
    def onKeyPress(self, sender, keyCode, modifiers):
        pass

    
def init():
    text="GWT includes the standard complement of text-entry widgets, each of which "
    text+="supports keyboard and selection events you can use to control text entry.  "
    text+="In particular, notice that the selection range for each widget is "
    text+="updated whenever you press a key.  "
    text+="This can be a bit tricky on some browsers, but the GWT class library "
    text+="takes care of the plumbing for you automatically."
    return SinkInfo("Text", text, Text)
