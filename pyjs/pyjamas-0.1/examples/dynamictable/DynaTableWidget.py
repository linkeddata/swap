from ui import Composite, DockPanel, HTML, HorizontalPanel, DockPanel, HasAlignment, Button, Grid

class NavBar(Composite):

    def __init__(self, owner):
        self.owner = owner
        self.bar = DockPanel()
        self.gotoFirst = Button("&lt;&lt;", self)
        self.gotoNext = Button("&gt;", self)
        self.gotoPrev = Button("&lt;", self)
        self.status = HTML()
        
        self.setWidget(self.bar)
        self.bar.setStyleName("navbar")
        self.status.setStyleName("status")
        
        buttons = HorizontalPanel()
        buttons.add(self.gotoFirst)
        buttons.add(self.gotoPrev)
        buttons.add(self.gotoNext)
        self.bar.add(buttons, DockPanel.EAST)
        self.bar.setCellHorizontalAlignment(buttons, HasAlignment.ALIGN_RIGHT)
        self.bar.add(self.status, DockPanel.CENTER)
        self.bar.setVerticalAlignment(HasAlignment.ALIGN_MIDDLE)
        self.bar.setCellHorizontalAlignment(self.status, HasAlignment.ALIGN_RIGHT)
        self.bar.setCellVerticalAlignment(self.status, HasAlignment.ALIGN_MIDDLE)
        self.bar.setCellWidth(self.status, "100%")
        
        self.gotoPrev.setEnabled(False)
        self.gotoFirst.setEnabled(False)
        
    def onClick(self, sender):
        if sender == self.gotoNext:
            self.owner.startRow += self.owner.getDataRowCount()
            self.owner.refresh()
        elif sender == self.gotoPrev:
            self.owner.startRow -= self.owner.getDataRowCount()
            if self.owner.startRow < 0:
                self.owner.startRow = 0
            self.owner.refresh()
        elif sender == self.gotoFirst:
            self.owner.startRow = 0
            self.owner.refresh()


class RowDataAcceptorImpl:

    def __init__(self, owner):
        self.owner = owner

    def accept(self, startRow, data):
        destRowCount = self.owner.getDataRowCount()
        destColCount = self.owner.grid.getCellCount(0)
        
        srcRowIndex = 0
        srcRowCount = len(data)
        destRowIndex = 1
        
        while srcRowIndex < srcRowCount:
            
            srcRowData = data[srcRowIndex]
            
            for srcColIndex in range(destColCount):
                cellHTML = srcRowData[srcColIndex]
                self.owner.grid.setText(destRowIndex, srcColIndex, cellHTML)
            
            srcRowIndex += 1
            destRowIndex += 1
        
        isLastPage = False
        
        while destRowIndex < destRowCount + 1:
        
            isLastPage = True
            
            for destColIndex in range(destColCount):
                self.owner.grid.clearCell(destRowIndex, destColIndex)
        
            destRowIndex += 1
            
        self.owner.navbar.gotoNext.setEnabled(not isLastPage)
        self.owner.navbar.gotoFirst.setEnabled(startRow > 0)
        self.owner.navbar.gotoPrev.setEnabled(startRow > 0)
        
        self.owner.setStatusText(str(startRow + 1) + " - " + str(startRow + srcRowCount))
    
    def failed(self, message): 
        msg = "Failed to access data"
        if message:
            msg += ": " + message
        self.owner.setStatusText(msg)



class DynaTableWidget(Composite):

    def __init__(self, provider, columns, columnStyles, rowCount):
        Composite.__init__(self)
    
        self.acceptor = RowDataAcceptorImpl(self)
        self.outer = DockPanel()
        self.startRow = 0
        self.grid = Grid()
        self.navbar = NavBar(self)
        
        self.provider = provider
        self.setWidget(self.outer)
        self.grid.setStyleName("table")
        self.outer.add(self.navbar, DockPanel.NORTH)
        self.outer.add(self.grid, DockPanel.CENTER)
        self.initTable(columns, columnStyles, rowCount)
        self.setStyleName("DynaTable-DynaTableWidget")
        
    def initTable(self, columns, columnStyles, rowCount):
        self.grid.resize(rowCount + 1, len(columns))
        for i in range(len(columns)):
            caption = columns[i]
            self.grid.setText(0, i, columns[i])
            if columnStyles:
                self.grid.cellFormatter.setStyleName(0, i, columnStyles[i] + "header")

    def setStatusText(self, text):
        self.navbar.status.setText(text)
        
    def clearStatusText(self, text):
        self.navbar.status.setHTML("&nbsp;")
        
    def refresh(self):
        self.navbar.gotoFirst.setEnabled(False)
        self.navbar.gotoPrev.setEnabled(False)
        self.navbar.gotoNext.setEnabled(False)
        
        self.setStatusText("Please wait...")
        self.provider.updateRowData(self.startRow, self.grid.getRowCount() - 1, self.acceptor)
        
    def setRowCount(self, rows):
        self.grid.resizeRows(rows)
        
    def getDataRowCount(self):
        return self.grid.getRowCount() - 1
