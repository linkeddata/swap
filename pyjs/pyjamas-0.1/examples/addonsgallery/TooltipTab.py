from Sink import Sink, SinkInfo
from ui import Image, HTML, VerticalPanel, HorizontalPanel
from Tooltip import TooltipListener

class TooltipTab(Sink):
    def __init__(self):
        img = Image("images/num1.png")
        img.addMouseListener(TooltipListener("An image: " + img.getUrl()))
        
        img2 = Image("images/num2.png")
        img2.addMouseListener(TooltipListener("An image: " + img2.getUrl()))

        html = HTML("Some <i>HTML</i> text.")
        html.addMouseListener(TooltipListener("An HTML component."))
        
        panel_h = HorizontalPanel()
        panel_h.add(img)
        panel_h.add(img2)       
        panel_h.setSpacing(8)
        
        panel = VerticalPanel()
        panel.add(panel_h)
        panel.add(html)
        
        panel.setSpacing(8)
        self.setWidget(panel)

    def onShow(self):
        pass


def init():
    text="<b>Tooltip popup component</b><p>Shows up after 1 second, hides after 5 seconds. Once activated, other tooltips show up immediately."
    text+=r"<br><br>Originally by Alexei Sokolov at <a href=\"http://gwt.components.googlepages.com\">gwt.components.googlepages.com</a>"
    return SinkInfo("Tooltip", text, TooltipTab)
