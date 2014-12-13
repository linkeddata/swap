from Sink import Sink, SinkInfo
from ui import ListBox, HorizontalPanel, VerticalPanel, HasAlignment, Label, Widget

class Lists(Sink):
    def __init__(self):
        self.sStrings=[["foo0", "bar0", "baz0", "toto0", "tintin0"],
            ["foo1", "bar1", "baz1", "toto1", "tintin1"],
            ["foo2", "bar2", "baz2", "toto2", "tintin2"],
            ["foo3", "bar3", "baz3", "toto3", "tintin3"],
            ["foo4", "bar4", "baz4", "toto4", "tintin4"]]

        self.combo=ListBox()
        self.list=ListBox()
        self.echo=Label()

        self.combo.setVisibleItemCount(1)
        self.combo.addChangeListener(self)
        self.list.setVisibleItemCount(10)
        self.list.setMultipleSelect(True)
        
        for i in range(len(self.sStrings)):
            self.combo.addItem("List " + i)
        self.combo.setSelectedIndex(0)
        self.fillList(0)
        
        self.list.addChangeListener(self)
        
        horz = HorizontalPanel()
        horz.setVerticalAlignment(HasAlignment.ALIGN_TOP)
        horz.setSpacing(8)
        horz.add(self.combo)
        horz.add(self.list)
        
        panel = VerticalPanel()
        panel.setHorizontalAlignment(HasAlignment.ALIGN_LEFT)
        panel.add(horz)
        panel.add(self.echo)
        self.setWidget(panel)
        
        self.echoSelection()

    def onChange(self, sender):
        if sender == self.combo:
            self.fillList(self.combo.getSelectedIndex())
        elif sender == self.list:
            self.echoSelection()

    def onShow(self):
        pass
    
    def fillList(self, idx):
        self.list.clear()
        strings = self.sStrings[idx]
        for i in range(len(strings)):
            self.list.addItem(strings[i])

        self.echoSelection()

    def echoSelection(self):
        msg = "Selected items: "
        for i in range(self.list.getItemCount()):
            if self.list.isItemSelected(i):
                msg += self.list.getItemText(i) + " "
        self.echo.setText(msg)


def init():
    text="Here is the ListBox widget in its two major forms."
    return SinkInfo("Lists", text, Lists)

