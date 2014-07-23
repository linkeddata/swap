from Sink import Sink, SinkInfo
from ui import HTML

class IntroTab(Sink):
    def __init__(self):
        text="<div class='infoProse'>Welcome to the Addons Gallery.  "
        text+="This app shows off the addon components for Pyjamas.</div>"
        self.setWidget(HTML(text, True))

    def onShow(self):
        pass


def init():
    return SinkInfo("Intro", "<b>Introduction to the Addons Gallery</b>", IntroTab)