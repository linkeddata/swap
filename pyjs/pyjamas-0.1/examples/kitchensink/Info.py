from Sink import Sink, SinkInfo
from ui import HTML

class Info(Sink):
    def __init__(self):
        text="<div class='infoProse'>This is the Kitchen Sink sample.  "
        text+="It demonstrates many of the widgets in the Google Web Toolkit."
        text+="<p>This sample also demonstrates something else really useful in GWT: "
        text+="history support.  "
        text+="When you click on a link at the left, the location bar will be "
        text+="updated with the current <i>history token</i>, which keeps the app "
        text+="in a bookmarkable state.  The back and forward buttons work properly "
        text+="as well.  Finally, notice that you can right-click a link and 'open "
        text+="in new window' (or middle-click for a new tab in Firefox).</p></div>"
        self.setWidget(HTML(text, True))

    def onShow(self):
        pass


def init():
    return SinkInfo("Info", "Introduction to the Kitchen Sink.", Info)