from ui import Button, RootPanel, HTML, DockPanel, HasAlignment, Hyperlink, VerticalPanel
import Window
from SinkList import SinkList
from History import History
import Info
import Buttons
import Layouts
import Images
import Menus
import Lists
import Popups
import Tables
import Text
import Trees
import Frames
import Tabs
from Logger import Logger

class KitchenSink:

    def onHistoryChanged(self, token):
        info = self.sink_list.find(token)
        if info:
            self.show(info, False)
        else:
            self.showInfo()

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
        RootPanel().add(Logger())

        #Show the initial screen.
        initToken = History().getToken()
        if len(initToken):
            self.onHistoryChanged(initToken)
        else:
            self.showInfo()

    def show(self, info, affectHistory):
        if info == self.curInfo: return
        self.curInfo = info

        Logger("", "showing " + info.getName())
        if self.curSink <> None:
            self.curSink.onHide()
            Logger("", "removing " + self.curSink)
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
        self.sink_list.addSink(Info.init())
        self.sink_list.addSink(Buttons.init())
        self.sink_list.addSink(Menus.init())
        self.sink_list.addSink(Images.init())
        self.sink_list.addSink(Layouts.init())
        self.sink_list.addSink(Lists.init())
        self.sink_list.addSink(Popups.init())
        self.sink_list.addSink(Tables.init())
        self.sink_list.addSink(Text.init())
        self.sink_list.addSink(Trees.init())
        self.sink_list.addSink(Frames.init())
        self.sink_list.addSink(Tabs.init())

    def showInfo(self):
        self.show(self.sink_list.find("Info"), False)


