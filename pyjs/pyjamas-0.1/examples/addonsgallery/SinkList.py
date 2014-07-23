from ui import Composite, VerticalPanel, Hyperlink

class SinkList(Composite):
    def __init__(self):
        self.vp_list=VerticalPanel()
        self.sinks=[]
        self.selectedSink=-1
        
        self.setWidget(self.vp_list)
        self.setStyleName("ks-List")

    def addSink(self, info):
        name = info.getName()
        link = Hyperlink(name, False, name)
        link.setStyleName("ks-SinkItem")
        self.vp_list.add(link)
        self.sinks.append(info)

    def find(self, sinkName):
        for info in self.sinks:
            if info.getName()==sinkName:
                return info
        return None

    def setSinkSelection(self, name):
        if self.selectedSink <> -1:
            self.vp_list.getWidget(self.selectedSink).removeStyleName("ks-SinkItem-selected")

        for i in range(len(self.sinks)):
            info = self.sinks[i]
            if (info.getName()==name):
                self.selectedSink = i
                widget=self.vp_list.getWidget(self.selectedSink)
                widget.addStyleName("ks-SinkItem-selected")
                return


