from Sink import Sink, SinkInfo
from ui import DockPanel, Image, VerticalPanel, HasAlignment, HTML

class Images(Sink):
    def __init__(self):
        self.curImage=0
        self.image=Image()
        self.loadingImage = Image(self.baseURL() + "images/blanksearching.gif")
        self.nextButton = Image(self.baseURL() + "rembrandt/forward.gif")
        self.prevButton = Image(self.baseURL() + "rembrandt/back.gif")
        self.sImages=["rembrandt/JohannesElison.jpg", "rembrandt/LaMarcheNocturne.jpg", "rembrandt/SelfPortrait1628.jpg", "rembrandt/SelfPortrait1640.jpg", "rembrandt/TheArtistInHisStudio.jpg", "rembrandt/TheReturnOfTheProdigalSon.jpg"]

        for i in range(len(self.sImages)):
            self.sImages[i]=self.baseURL() + self.sImages[i]
        
        self.image.addLoadListener(self)
        self.prevButton.addClickListener(self)
        self.nextButton.addClickListener(self)
        
        topPanel = DockPanel()
        topPanel.setVerticalAlignment(HasAlignment.ALIGN_MIDDLE)
        topPanel.add(self.prevButton, DockPanel.WEST)
        topPanel.add(self.nextButton, DockPanel.EAST)
        topPanel.add(self.loadingImage, DockPanel.CENTER)
        
        panel = VerticalPanel()
        panel.setHorizontalAlignment(HasAlignment.ALIGN_CENTER)
        panel.add(HTML("<h2>A Bit of Rembrandt</h2>", True))
        panel.add(topPanel)
        panel.add(self.image)
        
        panel.setWidth("100%")
        self.setWidget(panel)
        self.image.setStyleName("ks-images-Image")
        self.nextButton.setStyleName("ks-images-Button")
        self.prevButton.setStyleName("ks-images-Button")
        
        self.loadImage(0)           

    def onClick(self, sender):
        if sender==self.prevButton:
            self.loadImage(self.curImage - 1)
        elif sender == self.nextButton:
            self.loadImage(self.curImage + 1)

    def onError(self, sender):
        pass

    def onLoad(self, sender):
        self.loadingImage.setUrl(self.baseURL() + "images/blanksearching.gif")

    def loadImage(self, index):
        if index < 0:
            index = len(self.sImages) - 1
        elif index > len(self.sImages) - 1:
            index = 0

        self.curImage = index
        self.loadingImage.setUrl(self.baseURL() + "images/searching.gif")
        self.image.setUrl(self.sImages[self.curImage])

def init():
    text="This page demonstrates GWT's support for images.  Notice in particular how it uses the image's onLoad event to display a 'wait spinner' between the back and forward buttons."
    return SinkInfo("Images", text, Images)
