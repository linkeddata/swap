from Sink import Sink, SinkInfo
from ui import TabPanel, HasAlignment, Image, VerticalPanel

class Tabs(Sink):
    def __init__(self):
        self.fTabs = TabPanel()
        self.fTabs.add(self.createImage(self.baseURL() + "rembrandt/JohannesElison.jpg"), "1634")
        self.fTabs.add(self.createImage(self.baseURL() + "rembrandt/SelfPortrait1640.jpg"), "1640")
        self.fTabs.add(self.createImage(self.baseURL() + "rembrandt/LaMarcheNocturne.jpg"), "1642")
        self.fTabs.add(self.createImage(self.baseURL() + "rembrandt/TheReturnOfTheProdigalSon.jpg"), "1662")
        self.fTabs.selectTab(0)

        self.fTabs.setWidth("100%")
        self.fTabs.setHeight("100%")
        self.setWidget(self.fTabs)

    def onShow(self):
        pass

    def createImage(self, imageUrl):
        image = Image(imageUrl)
        image.setStyleName("ks-images-Image")
        
        p = VerticalPanel()
        p.setHorizontalAlignment(HasAlignment.ALIGN_CENTER)
        p.setVerticalAlignment(HasAlignment.ALIGN_MIDDLE)
        p.add(image)
        return p

def init():
    text="This page demonstrates GWT's support for images.  Notice in particular how it uses the image's onLoad event to display a 'wait spinner' between the back and forward buttons."
    text="GWT's built-in <code>TabPanel</code> class makes it easy to build tabbed dialogs "
    text+="and the like.  Notice that no page load occurs when you select the "
    text+="different tabs in this page.  That's the magic of dynamic HTML."
    return SinkInfo("Tabs", text, Tabs)
