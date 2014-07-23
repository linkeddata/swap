from Sink import Sink, SinkInfo
from ui import Button, VerticalPanel, PopupPanel, ListBox, HTML, DockPanel, DialogBox, Frame, HasAlignment
import DOM

class Popups(Sink):
    def __init__(self):
        self.fDialogButton = Button("Show Dialog", self)
        self.fPopupButton = Button("Show Popup", self)
        
        panel = VerticalPanel()
        panel.add(self.fPopupButton)
        panel.add(self.fDialogButton)
        
        list = ListBox()
        list.setVisibleItemCount(5)
        for i in range(10):
            list.addItem("list item " + i)
        panel.add(list)
        
        panel.setSpacing(8)
        self.setWidget(panel)

    def onShow(self):
        pass

    def onClick(self, sender):
        if sender == self.fPopupButton:
            p = MyPopup()
            left = sender.getAbsoluteLeft() + 10
            top = sender.getAbsoluteTop() + 10
            p.setPopupPosition(left, top)
            p.show()
        elif sender == self.fDialogButton:
            dlg = MyDialog()
            left = self.fDialogButton.getAbsoluteLeft() + 10
            top = self.fDialogButton.getAbsoluteTop() + 10
            dlg.setPopupPosition(left, top)
            dlg.show()


def init():
    text="This page demonstrates GWT's built-in support for in-page "
    text+="popups.  The first is a very simple informational popup that closes "
    text+="itself automatically when you click off of it.  The second is a more "
    text+="complex draggable dialog box. If you're wondering why there's "
    text+="a list box at the bottom, it's to demonstrate that you can drag the "
    text+="dialog box over it.  "
    text+="This is noteworthy because some browsers render lists and combos in "
    text+="a funky way that, if GWT didn't do some magic for you, would "
    text+="normally cause the dialog box to appear to hover <i>underneath</i> "
    text+="the list box.  Fortunately, you don't have to worry about it -- "
    text+="just use the GWT <code>DialogBox</code> class."
    return SinkInfo("Popups", text, Popups)


class MyDialog(DialogBox):
    def __init__(self):
        DialogBox.__init__(self)
        self.setText("Sample DialogBox with embedded Frame")
        
        iframe = Frame(Popups.baseURL() + "rembrandt/LaMarcheNocturne.html")
        closeButton = Button("Close", self)
        msg = HTML("<center>This is an example of a standard dialog box component.<br>  You can put pretty much anything you like into it,<br>such as the following IFRAME:</center>", True)
        
        dock = DockPanel()
        dock.setSpacing(4)
        
        dock.add(closeButton, DockPanel.SOUTH)
        dock.add(msg, DockPanel.NORTH)
        dock.add(iframe, DockPanel.CENTER)
        
        dock.setCellHorizontalAlignment(closeButton, HasAlignment.ALIGN_RIGHT)
        dock.setCellWidth(iframe, "100%")
        dock.setWidth("100%")
        iframe.setWidth("36em")
        iframe.setHeight("20em")
        self.add(dock)

    def onClick(self, sender):
        self.hide()


class MyPopup(PopupPanel):
    def __init__(self):
        PopupPanel.__init__(self, True)
        
        contents = HTML("Click anywhere outside this popup to make it disappear.")
        contents.setWidth("128px")
        self.add(contents)
        
        self.setStyleName("ks-popups-Popup")
