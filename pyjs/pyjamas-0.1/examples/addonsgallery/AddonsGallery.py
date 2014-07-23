from ui import Button, RootPanel, HTML, DockPanel, HasAlignment, Hyperlink, VerticalPanel
import Window
from SinkList import SinkList
from History import History
import IntroTab
import TooltipTab
import AutoCompleteTab
import CanvasTab

class AddonsGallery:

    def onHistoryChanged(self, token):
        info = self.sink_list.find(token)
        if info:
            self.show(info, False)
        else:
            self.showIntro()

    def onModuleLoad(self):
        self.curInfo=''
        self.curSink=None
        self.description=HTML()
        self.sink_list=SinkList()
        self.panel=DockPanel()
        
        self.loadSinks()
        self.sinkContainer = DockPanel()
        self.sinkContainer.setStyleName("ks-Sink")

        vp=VerticalPanel()
        vp.setWidth("100%")
        vp.add(self.description)
        vp.add(self.sinkContainer)

        self.description.setStyleName("ks-Info")

        self.panel.add(self.sink_list, DockPanel.WEST)
        self.panel.add(vp, DockPanel.CENTER)

        self.panel.setCellVerticalAlignment(self.sink_list, HasAlignment.ALIGN_TOP)
        self.panel.setCellWidth(vp, "100%")

        History().addHistoryListener(self)
        RootPanel().add(self.panel)

        initToken = History().getToken()
        if len(initToken):
            self.onHistoryChanged(initToken)
        else:
            self.showIntro()
    
    def show(self, info, affectHistory):
        if info == self.curInfo: return
        self.curInfo = info

        if self.curSink <> None:
            self.curSink.onHide()
            self.sinkContainer.remove(self.curSink)

        self.curSink = info.getInstance()
        self.sink_list.setSinkSelection(info.getName())
        self.description.setHTML(info.getDescription())

        if (affectHistory):
            History().newItem(info.getName())

        self.sinkContainer.add(self.curSink, DockPanel.CENTER)
        self.sinkContainer.setCellWidth(self.curSink, "100%")
        self.sinkContainer.setCellHeight(self.curSink, "100%")
        self.sinkContainer.setCellVerticalAlignment(self.curSink, DockPanel.ALIGN_TOP)
        self.curSink.onShow()
        
    def loadSinks(self):
        self.sink_list.addSink(IntroTab.init())
        self.sink_list.addSink(TooltipTab.init())
        self.sink_list.addSink(AutoCompleteTab.init())
        self.sink_list.addSink(CanvasTab.init())

    def showIntro(self):
        self.show(self.sink_list.find("Intro"))


