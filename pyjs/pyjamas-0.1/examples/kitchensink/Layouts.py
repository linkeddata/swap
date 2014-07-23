from Sink import Sink, SinkInfo
from ui import Button, CheckBox, VerticalPanel, HorizontalPanel, HTML, DockPanel, HasAlignment, FlowPanel, HTMLPanel, MenuBar, MenuItem, ScrollPanel
from Logger import Logger
import DOM

class Layouts(Sink):
    def __init__(self):
        text="This is a <code>ScrollPanel</code> contained at "
        text+= "the center of a <code>DockPanel</code>.  "
        text+= "By putting some fairly large contents "
        text+= "in the middle and setting its size explicitly, it becomes a "
        text+= "scrollable area within the page, but without requiring the use of "
        text+= "an IFRAME."
        text+= "Here's quite a bit more meaningless text that will serve primarily "
        text+= "to make this thing scroll off the bottom of its visible area.  "
        text+= "Otherwise, you might have to make it really, really small in order "
        text+= "to see the nifty scroll bars!"
        
        contents = HTML(text)
        scroller = ScrollPanel(contents)
        scroller.setStyleName("ks-layouts-Scroller")
        
        dock = DockPanel()
        dock.setHorizontalAlignment(HasAlignment.ALIGN_CENTER)
        north0 = HTML("This is the <i>first</i> north component", True)
        east = HTML("<center>This<br>is<br>the<br>east<br>component</center>", True)
        south = HTML("This is the south component")
        west = HTML("<center>This<br>is<br>the<br>west<br>component</center>", True)
        north1 = HTML("This is the <b>second</b> north component", True)
        dock.add(north0, DockPanel.NORTH)
        dock.add(east, DockPanel.EAST)
        dock.add(south, DockPanel.SOUTH)
        dock.add(west, DockPanel.WEST)
        dock.add(north1, DockPanel.NORTH)
        dock.add(scroller, DockPanel.CENTER)
        
        Logger("Layouts", "TODO: flowpanel")
        flow = FlowPanel()
        for i in range(8):
            flow.add(CheckBox("Flow " + i))

        horz = HorizontalPanel()
        horz.setVerticalAlignment(HasAlignment.ALIGN_MIDDLE)
        horz.add(Button("Button"))
        horz.add(HTML("<center>This is a<br>very<br>tall thing</center>", True))
        horz.add(Button("Button"))

        vert = VerticalPanel()
        vert.setHorizontalAlignment(HasAlignment.ALIGN_CENTER)
        vert.add(Button("Small"))
        vert.add(Button("--- BigBigBigBig ---"))
        vert.add(Button("tiny"))

        menu = MenuBar()
        menu0 = MenuBar(True)
        menu1 = MenuBar(True)
        menu.addNewItem("menu0", False, None, menu0)
        menu.addNewItem("menu1", False, None, menu1)
        menu0.addNewItem("child00")
        menu0.addNewItem("child01")
        menu0.addNewItem("child02")
        menu1.addNewItem("child10")
        menu1.addNewItem("child11")
        menu1.addNewItem("child12")

        Logger("Layouts", "TODO: htmlpanel")
        id = HTMLPanel.createUniqueId()
        text="This is an <code>HTMLPanel</code>.  It allows you to add "
        text+="components inside existing HTML, like this:" + "<span id='" + id
        text+="'></span>" + "Notice how the menu just fits snugly in there?  Cute."
        html = HTMLPanel(text)
        
        DOM.setStyleAttribute(menu.getElement(), "display", "inline")
        html.add(menu, id)

        panel = VerticalPanel()
        panel.setSpacing(8)
        panel.setHorizontalAlignment(HasAlignment.ALIGN_CENTER)
        
        panel.add(self.makeLabel("Dock Panel"))
        panel.add(dock)
        panel.add(self.makeLabel("Flow Panel"))
        panel.add(flow)
        panel.add(self.makeLabel("Horizontal Panel"))
        panel.add(horz)
        panel.add(self.makeLabel("Vertical Panel"))
        panel.add(vert)
        panel.add(self.makeLabel("HTML Panel"))
        panel.add(html)
        
        self.setWidget(panel)
        self.setStyleName("ks-layouts")

    def onShow(self):
        pass

    def makeLabel(self, caption):
        html = HTML(caption)
        html.setStyleName("ks-layouts-Label")
        return html


def init():
    text="This page demonstrates some of the basic GWT panels, each of which"
    text+="arranges its contained widgets differently.  "
    text+="These panels are designed to take advantage of the browser's "
    text+="built-in layout mechanics, which keeps the user interface snappy "
    text+="and helps your AJAX code play nicely with existing HTML.  "
    text+="On the other hand, if you need pixel-perfect control, "
    text+="you can tweak things at a low level using the "
    text+="<code>DOM</code> class."
    return SinkInfo("Layouts", text, Layouts)
