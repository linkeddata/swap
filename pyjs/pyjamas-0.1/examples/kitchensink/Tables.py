from Sink import Sink, SinkInfo
from ui import Grid, FlexTable, HasHorizontalAlignment, Image

class Tables(Sink):
    def __init__(self):
        inner = Grid(10, 5)
        outer = FlexTable()

        outer.setWidget(0, 0, Image(self.baseURL() + "rembrandt/LaMarcheNocturne.jpg"))
        outer.getFlexCellFormatter().setColSpan(0, 0, 2)
        outer.getFlexCellFormatter().setHorizontalAlignment(0, 0, HasHorizontalAlignment.ALIGN_CENTER)

        outer.setHTML(1, 0, "Look to the right...<br>That's a nested table component ->")
        outer.setWidget(1, 1, inner)
        outer.getCellFormatter().setColSpan(1, 1, 2)
        
        for i in range(10):
            for j in range(5):
                inner.setText(i, j, "" + i + "," + j)

        inner.setWidth("100%")
        outer.setWidth("100%")

        inner.setBorderWidth(1)
        outer.setBorderWidth(1)

        self.setWidget(outer)
        
    def onShow(self):
        pass

def init():
    text="The <code>FlexTable</code> widget doubles as a tabular data formatter and a panel.  In this example, you'll see that there is an outer table with four cells, two of which contain nested components."
    return SinkInfo("Tables", text, Tables)